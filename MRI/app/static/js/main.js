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
let lastHistoryId = null;

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
    if (!checkAuth()) {
        return;
    }
    initWebSocket();
    loadModels();
    setupEventListeners();
});

/**
 * 初始化WebSocket连接
 */
function initWebSocket() {
    if (ws) {
        ws.close();
    }

    // 生成客户端ID
    clientId = uuid.v4();
    
    // 获取认证令牌
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error('未找到认证令牌，WebSocket连接失败');
        connectionStatus.textContent = '未认证';
        connectionStatus.classList.remove('bg-success', 'bg-secondary');
        connectionStatus.classList.add('bg-danger');
        window.location.href = '/login';
        return;
    }
    
    console.log(`WebSocket: 正在尝试连接 ${WS_URL}/api/ws/${clientId} 并附带令牌`);
    
    // 创建WebSocket连接，附带认证令牌
    const wsUrl = `${WS_URL}/api/ws/${clientId}?token=${encodeURIComponent(token)}`;
    console.log('WebSocket URL:', wsUrl);
    ws = new WebSocket(wsUrl);
    
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
    
    ws.onclose = (event) => {
        console.log('WebSocket连接已关闭', event.code, event.reason);
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
        console.log('开始加载模型列表...');
        
        const response = await fetch(`${API_URL}/api/reconstruction/models`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('获取到的模型数据:', data);
        
        const models = data.models || [];
        
        // 清空现有选项
        modelSelect.innerHTML = '<option value="" selected disabled>-- 请选择模型 --</option>';
        
        // 添加模型选项
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name || model.id;
            modelSelect.appendChild(option);
            console.log(`添加模型选项: ${model.id} - ${model.name}`);
        });
        
        if (models.length === 0) {
            showMessage('没有可用的模型', 'warning');
            console.log('未找到任何模型');
        } else {
            console.log(`成功加载了 ${models.length} 个模型`);
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
        // 添加认证头
        const headers = {
            'Authorization': getAuthHeader()
        };
        
        const response = await fetch(`${API_URL}/api/models/${modelId}`, { headers });
        if (!response.ok) {
            if (response.status === 401) {
                // 认证失败，重定向到登录页面
                window.location.href = '/login';
                return;
            }
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
        
        // 如果是认证错误，重定向到登录页面
        if (error.message.includes('401')) {
            window.location.href = '/login';
        }
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
    
    // 确保保存图像按钮事件正确绑定
    const saveReconstructedBtn = document.getElementById('saveReconstructedBtn');
    if (saveReconstructedBtn) {
        console.log('main.js: 找到保存图像按钮，确保事件监听正确绑定');
        
        // 移除任何可能的旧监听器
        const newButton = saveReconstructedBtn.cloneNode(true);
        saveReconstructedBtn.parentNode.replaceChild(newButton, saveReconstructedBtn);
        
        // 添加新的事件监听器
        newButton.addEventListener('click', function(e) {
            console.log('main.js: 保存图像按钮被点击');
            
            e.preventDefault();
            const reconstructedImg = document.querySelector('#reconstructedImagePreview img');
            if (!reconstructedImg) {
                console.error('main.js: 未找到重建图像元素');
                alert('没有可保存的重建图像');
                return;
            }
            
            try {
                console.log('main.js: 找到图像，准备下载', reconstructedImg.src.substring(0, 30) + '...');
                
                // 创建一个临时链接
                const link = document.createElement('a');
                link.href = reconstructedImg.src;
                link.download = 'reconstructed_image_' + new Date().getTime() + '.png';
                
                // 添加到文档并触发点击
                document.body.appendChild(link);
                link.click();
                
                // 清理
                document.body.removeChild(link);
                
                console.log('main.js: 图像下载操作完成');
                showToast('图像已保存', '文件已下载到您的设备');
            } catch (error) {
                console.error('main.js: 下载图像时出错:', error);
                showToast('保存失败', '无法保存图像: ' + error.message, 'danger');
            }
        });
        
        console.log('main.js: 保存图像按钮事件监听器已重新绑定');
    } else {
        console.warn('main.js: 未找到保存图像按钮元素');
    }
    
    // 设置定时心跳
    setInterval(sendPing, 30000);
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
        // 先清空预览容器
        previewElement.innerHTML = '';
        
        // 创建统一的容器样式
        const imgContainer = document.createElement('div');
        imgContainer.style.width = '100%';
        imgContainer.style.height = '100%';
        imgContainer.style.display = 'flex';
        imgContainer.style.alignItems = 'center';
        imgContainer.style.justifyContent = 'center';
        imgContainer.style.background = '#000';
        
        // 创建图像元素
        const img = document.createElement('img');
        img.src = e.target.result;
        img.alt = file.name;
        img.classList.add('preview-img');
        // 统一图像样式
        img.style.maxWidth = '100%';
        img.style.maxHeight = '100%';
        img.style.width = 'auto';
        img.style.height = 'auto';
        img.style.objectFit = 'contain';
        
        // 监听图像加载事件，确保图像显示正确
        img.onload = function() {
            // 清空重建结果区域，因为上传了新图像
            if (previewElement === originalImagePreview) {
                reconstructedImagePreview.innerHTML = '<p class="text-muted text-center">尚未执行重建</p>';
                resetResults();
            }
        };
        
        // 添加图像到容器
        imgContainer.appendChild(img);
        previewElement.appendChild(imgContainer);
    };
    reader.readAsDataURL(file);
}

/**
 * 提交重建请求
 * @param {File} file - 图像文件
 * @param {string} modelId - 模型ID
 */
async function submitReconstruction(file, modelId) {
    // 检查认证
    if (!checkAuth()) {
        return;
    }
    
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
        
        // 添加认证头
        const headers = {
            'Authorization': getAuthHeader()
        };
        
        // 发送请求
        const response = await fetch(`${API_URL}/api/reconstruction/`, {
            method: 'POST',
            headers,
            body: formData
        });
        
        if (!response.ok) {
            if (response.status === 401) {
                // 认证失败，重定向到登录页面
                window.location.href = '/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        // 显示结果
        displayReconstructionResult(result);
        
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
        
        // 如果是认证错误，重定向到登录页面
        if (error.message.includes('401')) {
            window.location.href = '/login';
        }
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
function displayReconstructionResult(result) {
    console.log('重建结果:', result);
    
    // 隐藏加载中遮罩
    document.getElementById('loadingOverlay').classList.add('d-none');
    
    // 设置任务状态为完成
    document.getElementById('taskStatus').textContent = '已完成';
    document.getElementById('taskStatus').className = 'badge bg-success';
    
    // 显示重建后的图像
    const reconstructedPreview = document.getElementById('reconstructedImagePreview');
    reconstructedPreview.innerHTML = '';
    
    const img = document.createElement('img');
    img.src = `data:image/png;base64,${result.reconstructed_image}`;
    img.alt = '重建结果';
    img.className = 'preview-img';
    reconstructedPreview.appendChild(img);
    
    // 启用图像保存按钮
    const saveBtn = document.getElementById('saveReconstructedBtn');
    if (saveBtn) {
        saveBtn.disabled = false;
        console.log('保存图像按钮已启用');
    } else {
        console.warn('未找到保存图像按钮元素');
    }
    
    // 更新性能指标
    document.getElementById('psnrValue').textContent = result.metrics.psnr.toFixed(2) + ' dB';
    document.getElementById('ssimValue').textContent = result.metrics.ssim.toFixed(4);
    document.getElementById('nseValue').textContent = result.metrics.nse.toFixed(4);
    
    // 更新执行时间
    document.getElementById('executionTimeValue').textContent = result.execution_time.toFixed(2) + ' 秒';
    
    // 显示通知
    showToast('重建完成', '图像重建已成功完成');
    
    // 当前任务ID (用于历史记录查询)
    currentTaskId = result.result_id;
}

/**
 * 获取重建结果
 * @param {string} resultId - 结果ID
 */
async function fetchReconstructionResult(resultId) {
    try {
        // 添加认证头
        const headers = {
            'Authorization': getAuthHeader()
        };
        
        const response = await fetch(`${API_URL}/api/reconstruction/results/${resultId}`, { headers });
        if (!response.ok) {
            if (response.status === 401) {
                // 认证失败，重定向到登录页面
                window.location.href = '/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayReconstructionResult(result);
        
    } catch (error) {
        console.error('获取重建结果时出错:', error);
        showMessage('获取结果失败: ' + error.message, 'danger');
        
        // 如果是认证错误，重定向到登录页面
        if (error.message.includes('401')) {
            window.location.href = '/login';
        }
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
 * 获取认证请求头
 */
function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    if (!token) {
        console.error('未找到认证令牌');
        return '';
    }
    return `${tokenType} ${token}`;
}

/**
 * 检查认证状态
 */
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        window.location.href = '/login';
        return false;
    }
    return true;
}

// 显示通知消息
function showToast(title, message, type = 'success') {
    // 创建toast元素
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0 position-fixed top-0 start-50 translate-middle-x mt-3`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // 设置toast内容
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong> ${message ? ' - ' + message : ''}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // 添加到文档
    document.body.appendChild(toastEl);
    
    // 创建Bootstrap Toast实例并显示
    const toast = new bootstrap.Toast(toastEl, {
        delay: 3000,
        animation: true
    });
    toast.show();
    
    // 监听关闭事件，移除元素
    toastEl.addEventListener('hidden.bs.toast', function() {
        document.body.removeChild(toastEl);
    });
} 