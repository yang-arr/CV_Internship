/**
 * MRI重建系统前端主逻辑
 * 
 * 包含功能：
 * - WebSocket连接管理
 * - 图像上传和预览
 * - 模型选择和信息展示
 * - 重建请求提交
 * - 结果显示
 */

// 全局变量
const API_URL = window.location.origin;
const WS_URL = window.location.protocol === 'https:' ? 
    `wss://${window.location.host}` : 
    `ws://${window.location.host}`;
let ws = null;
let clientId = null;
let selectedModel = null;
let currentTask = null;
let isAuthenticated = false;  // 添加认证状态变量

// DOM元素
const uploadForm = document.getElementById('uploadForm');
const modelSelect = document.getElementById('modelSelect');
const reconstructBtn = document.getElementById('reconstructBtn');
const originalImagePreview = document.getElementById('originalImagePreview');
const reconstructedImagePreview = document.getElementById('reconstructedImagePreview');
const connectionStatus = document.getElementById('connectionStatus');
const taskStatus = document.getElementById('taskStatus');
const progressBar = document.getElementById('progressBar');
const modelInfo = document.getElementById('modelInfo');
const psnrValue = document.getElementById('psnrValue');
const ssimValue = document.getElementById('ssimValue');
const nseValue = document.getElementById('nseValue');
const executionTimeValue = document.getElementById('executionTimeValue');
const loadingOverlay = document.getElementById('loadingOverlay');

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();  // 检查认证状态
    initWebSocket();
    loadModels();
    setupEventListeners();
});

/**
 * 检查用户认证状态
 */
function checkAuthStatus() {
    const token = localStorage.getItem('token');
    isAuthenticated = !!token;
    
    // 更新UI
    updateAuthUI();
    
    // 如果已认证，获取用户信息
    if (isAuthenticated) {
        fetchUserInfo();
    }
}

/**
 * 更新认证UI
 */
function updateAuthUI() {
    const loginItem = document.getElementById('loginItem');
    const registerItem = document.getElementById('registerItem');
    const userDropdown = document.getElementById('userDropdown');
    
    if (isAuthenticated) {
        loginItem.style.display = 'none';
        registerItem.style.display = 'none';
        userDropdown.style.display = 'block';
    } else {
        loginItem.style.display = 'block';
        registerItem.style.display = 'block';
        userDropdown.style.display = 'none';
    }
}

/**
 * 获取用户信息
 */
async function fetchUserInfo() {
    try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await fetch(`${API_URL}/users/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('username').textContent = user.username;
        } else if (response.status === 401) {
            // Token无效或过期
            localStorage.removeItem('token');
            isAuthenticated = false;
            updateAuthUI();
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
    }
}

/**
 * 初始化WebSocket连接
 */
function initWebSocket() {
    if (ws) {
        ws.close();
    }

    // 生成客户端ID
    clientId = uuid.v4();
    
    // 创建WebSocket连接
    ws = new WebSocket(`${WS_URL}/api/ws/${clientId}`);
    
    // 设置事件处理器
    ws.onopen = () => {
        console.log('WebSocket连接已建立');
        connectionStatus.textContent = '已连接';
        connectionStatus.classList.remove('bg-secondary', 'bg-danger');
        connectionStatus.classList.add('bg-success');
    };
    
    ws.onmessage = (event) => {
        handleWebSocketMessage(event);
    };
    
    ws.onclose = () => {
        console.log('WebSocket连接已关闭');
        connectionStatus.textContent = '已断开';
        connectionStatus.classList.remove('bg-success', 'bg-secondary');
        connectionStatus.classList.add('bg-danger');
        
        // 尝试重新连接
        setTimeout(initWebSocket, 3000);
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        connectionStatus.textContent = '连接错误';
        connectionStatus.classList.remove('bg-success', 'bg-secondary');
        connectionStatus.classList.add('bg-danger');
    };
}

/**
 * 处理WebSocket消息
 * @param {MessageEvent} event - WebSocket消息事件
 */
function handleWebSocketMessage(event) {
    try {
        const message = JSON.parse(event.data);
        console.log('收到消息:', message);
        
        switch (message.type) {
            case 'connection_established':
                // 连接成功消息
                break;
                
            case 'progress_update':
                // 更新进度条
                updateProgress(message.progress, message.status, message.message);
                break;
                
            case 'model_loaded':
                // 模型加载状态
                if (message.success) {
                    showMessage('模型加载成功', 'success');
                } else {
                    showMessage(`模型加载失败: ${message.message}`, 'danger');
                }
                break;
                
            case 'reconstruction_complete':
                // 重建完成
                hideLoading();
                showMessage('重建完成!', 'success');
                fetchReconstructionResult(message.result_id);
                break;
                
            case 'pong':
                // 心跳响应
                break;
                
            default:
                console.log('未知消息类型:', message.type);
        }
    } catch (error) {
        console.error('解析消息时出错:', error);
    }
}

/**
 * 发送心跳消息
 */
function sendPing() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'ping',
            timestamp: new Date().toISOString()
        }));
    }
}

/**
 * 加载可用的模型列表
 */
async function loadModels() {
    try {
        const response = await fetch(`${API_URL}/api/reconstruction/models`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const models = data.models || [];
        
        // 清空现有选项
        modelSelect.innerHTML = '<option value="" selected disabled>-- 请选择模型 --</option>';
        
        // 添加模型选项
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name || model.id;
            modelSelect.appendChild(option);
        });
        
        if (models.length === 0) {
            showMessage('没有可用的模型', 'warning');
        }
    } catch (error) {
        console.error('加载模型时出错:', error);
        showMessage('加载模型失败: ' + error.message, 'danger');
    }
}

/**
 * 加载模型详细信息
 * @param {string} modelId - 模型ID
 */
async function loadModelDetails(modelId) {
    try {
        const response = await fetch(`${API_URL}/api/models/${modelId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const model = await response.json();
        selectedModel = model;
        
        // 显示模型信息 - 仅显示名称、描述和创建时间
        let html = '<table class="table table-sm model-info-table">';
        html += '<tr><th>名称</th><td>' + (model.name || model.id) + '</td></tr>';
        html += '<tr><th>描述</th><td>' + (model.description || '无描述') + '</td></tr>';
        html += '<tr><th>创建时间</th><td>' + (formatDate(model.created_at) || 'N/A') + '</td></tr>';
        html += '</table>';
        
        modelInfo.innerHTML = html;
    } catch (error) {
        console.error('加载模型详情时出错:', error);
        modelInfo.innerHTML = '<p class="text-danger">加载模型信息失败</p>';
    }
}

/**
 * 设置事件监听器
 */
function setupEventListeners() {
    // 模型选择变更事件
    modelSelect.addEventListener('change', () => {
        const modelId = modelSelect.value;
        if (modelId) {
            loadModelDetails(modelId);
        } else {
            modelInfo.innerHTML = '<p class="text-muted text-center">请先选择模型</p>';
        }
    });
    
    // 图像文件选择事件
    document.getElementById('imageFile').addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            previewImage(file, originalImagePreview);
        }
    });
    
    // 表单提交事件
    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        
        // 检查是否选择了文件和模型
        const fileInput = document.getElementById('imageFile');
        const modelId = modelSelect.value;
        
        if (!fileInput.files.length) {
            showMessage('请选择图像文件', 'warning');
            return;
        }
        
        if (!modelId) {
            showMessage('请选择模型', 'warning');
            return;
        }
        
        // 提交重建请求
        await submitReconstruction(fileInput.files[0], modelId);
    });
    
    // 设置定时心跳
    setInterval(sendPing, 30000);
    
    // 退出登录按钮点击事件
    document.getElementById('logoutBtn').addEventListener('click', (event) => {
        event.preventDefault();
        logout();
    });
}

/**
 * 预览图像
 * @param {File} file - 图像文件
 * @param {Element} previewElement - 预览容器元素
 */
function previewImage(file, previewElement) {
    if (!file || !previewElement) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        previewElement.innerHTML = '';
        const img = document.createElement('img');
        img.src = e.target.result;
        img.alt = file.name;
        img.classList.add('preview-img');
        previewElement.appendChild(img);
    };
    reader.readAsDataURL(file);
}

/**
 * 提交重建请求
 * @param {File} file - 图像文件
 * @param {string} modelId - 模型ID
 */
async function submitReconstruction(file, modelId) {
    showLoading();
    resetResults();
    
    // 生成任务ID
    currentTask = uuid.v4();
    
    // 更新状态
    taskStatus.textContent = '处理中';
    taskStatus.classList.remove('bg-secondary', 'bg-danger');
    taskStatus.classList.add('bg-warning');
    
    // 清空重建结果
    reconstructedImagePreview.innerHTML = '<p class="text-muted text-center">重建中...</p>';
    
    try {
        // 创建表单数据
        const formData = new FormData();
        formData.append('file', file);
        formData.append('model_id', modelId);
        
        // 发送请求
        const response = await fetch(`${API_URL}/api/reconstruction/`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 显示结果
        displayResults(result);
        
        // 更新状态
        taskStatus.textContent = '已完成';
        taskStatus.classList.remove('bg-warning');
        taskStatus.classList.add('bg-success');
        
        // 更新进度条
        updateProgress(100, 'completed', '重建完成');
        
    } catch (error) {
        console.error('重建过程中出错:', error);
        showMessage('重建失败: ' + error.message, 'danger');
        
        // 更新状态
        taskStatus.textContent = '失败';
        taskStatus.classList.remove('bg-warning');
        taskStatus.classList.add('bg-danger');
        
        reconstructedImagePreview.innerHTML = '<p class="text-danger text-center">重建失败</p>';
    } finally {
        hideLoading();
    }
}

/**
 * 重置结果显示
 */
function resetResults() {
    reconstructedImagePreview.innerHTML = '<p class="text-muted text-center">尚未执行重建</p>';
    psnrValue.textContent = '-';
    ssimValue.textContent = '-';
    nseValue.textContent = '-';
    executionTimeValue.textContent = '-';
    progressBar.style.width = '0%';
    progressBar.setAttribute('aria-valuenow', 0);
}

/**
 * 显示重建结果
 * @param {Object} result - 重建结果对象
 */
function displayResults(result) {
    if (!result) return;
    
    console.log("收到重建结果:", result);
    
    // 显示重建图像
    if (result.reconstructed_image) {
        reconstructedImagePreview.innerHTML = '';
        const img = document.createElement('img');
        img.src = 'data:image/png;base64,' + result.reconstructed_image;
        img.alt = '重建结果';
        img.classList.add('preview-img');
        img.style.width = '100%';  // 确保图像大小适合容器
        reconstructedImagePreview.appendChild(img);
        
        console.log("已显示重建图像");
    } else {
        console.error("重建结果中没有图像数据");
        reconstructedImagePreview.innerHTML = '<p class="text-danger text-center">重建结果中没有图像数据</p>';
    }
    
    // 显示评估指标
    if (result.metrics) {
        psnrValue.textContent = result.metrics.psnr ? result.metrics.psnr.toFixed(2) : '-';
        ssimValue.textContent = result.metrics.ssim ? result.metrics.ssim.toFixed(4) : '-';
        nseValue.textContent = result.metrics.nse ? result.metrics.nse.toFixed(4) : '-';
    } else {
        console.warn("重建结果中没有评估指标");
    }
    
    // 显示执行时间
    if (result.execution_time) {
        executionTimeValue.textContent = result.execution_time.toFixed(2) + ' 秒';
    } else {
        console.warn("重建结果中没有执行时间");
    }
}

/**
 * 获取重建结果
 * @param {string} resultId - 结果ID
 */
async function fetchReconstructionResult(resultId) {
    try {
        const response = await fetch(`${API_URL}/api/reconstruction/results/${resultId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayResults(result);
        
    } catch (error) {
        console.error('获取重建结果时出错:', error);
        showMessage('获取结果失败: ' + error.message, 'danger');
    }
}

/**
 * 更新进度条
 * @param {number} progress - 进度值(0-100)
 * @param {string} status - 状态
 * @param {string} message - 状态消息
 */
function updateProgress(progress, status, message) {
    progressBar.style.width = `${progress}%`;
    progressBar.setAttribute('aria-valuenow', progress);
    
    // 更新进度条颜色
    progressBar.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    
    switch (status) {
        case 'completed':
            progressBar.classList.add('bg-success');
            break;
        case 'failed':
            progressBar.classList.add('bg-danger');
            break;
        case 'processing':
            progressBar.classList.add('bg-info');
            break;
        default:
            progressBar.classList.add('bg-secondary');
    }
    
    // 设置提示信息
    if (message) {
        progressBar.setAttribute('title', message);
    }
}

/**
 * 显示消息提示
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型 (success, danger, warning, info)
 */
function showMessage(message, type = 'info') {
    // 创建消息元素
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.role = 'alert';
    
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 添加到页面
    const container = document.querySelector('.container');
    container.insertBefore(alertElement, container.firstChild);
    
    // 自动消失
    setTimeout(() => {
        alertElement.classList.remove('show');
        setTimeout(() => alertElement.remove(), 500);
    }, 5000);
}

/**
 * 显示加载中遮罩
 */
function showLoading() {
    loadingOverlay.classList.remove('d-none');
}

/**
 * 隐藏加载中遮罩
 */
function hideLoading() {
    loadingOverlay.classList.add('d-none');
}

/**
 * 格式化日期
 * @param {string} dateString - ISO日期字符串
 * @returns {string} 格式化的日期字符串
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (error) {
        return dateString;
    }
}

/**
 * 退出登录
 */
function logout() {
    localStorage.removeItem('token');
    isAuthenticated = false;
    updateAuthUI();
    showMessage('已成功退出登录', 'success');
} 