// 认证检查脚本，页面加载时执行
(function() {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    console.log('检查认证状态: ', Boolean(token && tokenType));
    
    if (!token || !tokenType) {
        console.log('未找到有效令牌，重定向到登录页面');
        window.location.href = '/login';
    }
})();

// 在页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 初始化模型下拉列表
    initModelSelect();
    
    // 绑定上传表单提交事件
    initUploadForm();
    
    // 绑定图像保存按钮事件
    initSaveButton();
    
    // 绑定帮助和对比按钮事件
    initButtons();
    
    // 处理退出按钮
    document.getElementById('logoutBtn').addEventListener('click', (e) => {
        e.preventDefault();
        // 尝试调用authManager如果存在
        if (typeof authManager !== 'undefined') {
            authManager.logout();
        } else {
            // 备用登出方法
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('username');
            window.location.href = '/login';
        }
    });
});

// 初始化保存图像按钮
function initSaveButton() {
    const saveReconstructedBtn = document.getElementById('saveReconstructedBtn');
    if (saveReconstructedBtn) {
        console.log('初始化保存图像按钮');
        
        saveReconstructedBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const reconstructedImg = document.querySelector('#reconstructedImagePreview img');
            if (!reconstructedImg) {
                console.error('未找到重建图像元素');
                showNotification('没有可保存的重建图像', 'warning');
                return;
            }
            
            console.log('正在保存图像...');
            
            try {
                // 创建一个临时链接
                const link = document.createElement('a');
                link.href = reconstructedImg.src;
                link.download = 'reconstructed_image_' + new Date().getTime() + '.png';
                
                // 添加到文档并触发点击
                document.body.appendChild(link);
                link.click();
                
                // 清理
                document.body.removeChild(link);
                
                console.log('图像保存成功');
                showNotification('图像已保存', 'success');
            } catch (error) {
                console.error('保存图像失败:', error);
                showNotification('保存图像失败: ' + error.message, 'error');
            }
        });
    }
}

// 影像对比按钮事件处理
document.getElementById('compareBtn').addEventListener('click', () => {
    // 创建模态框
    const compareModal = document.createElement('div');
    compareModal.className = 'modal fade';
    compareModal.id = 'compareModal';
    compareModal.setAttribute('aria-labelledby', 'compareModalLabel');
    compareModal.setAttribute('aria-hidden', 'true');
    compareModal.style.backgroundColor = 'rgba(0, 0, 0, 0.75)'; // 设置初始背景颜色为深色半透明
    
    // 使用内联样式直接设置颜色
    compareModal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered" style="display: flex; align-items: center; min-height: calc(100% - 1rem); max-width: 500px; margin: 1.75rem auto;">
            <div class="modal-content" style="background-color: #00607A; color: white; border: none; box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);">
                <div class="modal-header" style="background: linear-gradient(135deg, #00607A, #004a60); border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding: 1rem 1.5rem;">
                    <h5 class="modal-title" id="compareModalLabel" style="color: white; font-weight: 600;">
                        <i class="bi bi-grid-3x3-gap me-2"></i>影像对比
                    </h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body" style="background-color: #005066; padding: 1.5rem;">
                    <div class="text-center">
                        <i class="bi bi-clock-history display-4 mb-3" style="color: #40c4ff;"></i>
                        <h4 style="color: white;">功能即将上线</h4>
                        <p style="color: rgba(255, 255, 255, 0.8);">我们正在努力开发影像对比功能，敬请期待！</p>
                    </div>
                </div>
                <div class="modal-footer" style="background-color: #004a60; border-top: 1px solid rgba(255, 255, 255, 0.1); padding: 1rem 1.5rem;">
                    <button type="button" class="btn btn-outline-light" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(compareModal);
    
    // 显示模态框
    const modal = new bootstrap.Modal(compareModal, {
        backdrop: 'static' // 防止点击背景关闭模态框
    });
    modal.show();
    
    // 添加事件监听器以确保模态框显示时背景就是深色的
    compareModal.addEventListener('shown.bs.modal', function() {
        // 确保模态框背景是深色的
        document.querySelector('.modal-backdrop').style.opacity = '0.85';
        document.querySelector('.modal-backdrop').style.backgroundColor = 'rgba(0, 0, 0, 0.85)';
        
        // 确保模态框在页面中居中
        const modalDialog = document.querySelector('#compareModal .modal-dialog');
        if (modalDialog) {
            modalDialog.style.display = 'flex';
            modalDialog.style.alignItems = 'center';
            modalDialog.style.justifyContent = 'center';
            modalDialog.style.margin = '0 auto';
            modalDialog.style.height = '100%';
            modalDialog.style.maxWidth = '500px';
        }
    });
    
    // 模态框关闭后从DOM中移除
    compareModal.addEventListener('hidden.bs.modal', function () {
        compareModal.remove();
    });
});

// 使用帮助按钮事件处理
document.getElementById('helpBtn').addEventListener('click', () => {
    // 创建模态框
    const helpModal = document.createElement('div');
    helpModal.className = 'modal fade';
    helpModal.id = 'helpModal';
    helpModal.tabIndex = '-1';
    helpModal.setAttribute('aria-labelledby', 'helpModalLabel');
    helpModal.setAttribute('aria-hidden', 'true');
    
    helpModal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="helpModalLabel">MRI重建系统使用帮助</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <h5><i class="bi bi-1-circle-fill me-2"></i>选择图像文件</h5>
                    <p>点击<strong>选择图像文件</strong>按钮，上传需要重建的MRI图像。支持常见图像格式如PNG、JPG等。</p>
                    
                    <h5><i class="bi bi-2-circle-fill me-2"></i>选择重建模型</h5>
                    <p>从下拉菜单中选择适合的重建模型，系统将显示所选模型的详细信息。</p>
                    
                    <h5><i class="bi bi-3-circle-fill me-2"></i>开始重建</h5>
                    <p>点击<strong>开始重建</strong>按钮，系统将开始处理您的图像。重建过程中，您可以通过进度条查看当前进度。</p>
                    
                    <h5><i class="bi bi-4-circle-fill me-2"></i>查看结果</h5>
                    <p>重建完成后，系统会在右侧显示原始图像和重建结果的对比，并提供PSNR、SSIM、NSE等性能指标。</p>
                    
                    <h5><i class="bi bi-5-circle-fill me-2"></i>历史记录</h5>
                    <p>点击顶部导航栏的<strong>历史记录</strong>按钮，可以查看您之前的重建历史。</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(helpModal);
    
    // 显示模态框
    const modal = new bootstrap.Modal(helpModal);
    modal.show();
    
    // 模态框关闭后从DOM中移除
    helpModal.addEventListener('hidden.bs.modal', function () {
        helpModal.remove();
    });
});

// 显示通知消息
function showNotification(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type} border-0 position-fixed top-0 start-50 translate-middle-x mt-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="bi bi-${type === 'info' ? 'info-circle' : type === 'warning' ? 'exclamation-triangle' : type === 'error' ? 'exclamation-circle' : 'check-circle'} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: 3000
    });
    
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// 初始化模型下拉列表
function initModelSelect() {
    const modelSelect = document.getElementById('modelSelect');
    if (!modelSelect) return;
    
    // 添加change事件监听器
    modelSelect.addEventListener('change', async function() {
        const selectedModelId = this.value;
        if (selectedModelId) {
            try {
                // 获取模型详情
                const token = localStorage.getItem('access_token');
                const tokenType = localStorage.getItem('token_type');
                
                if (!token || !tokenType) {
                    console.error('未找到有效令牌');
                    return;
                }
                
                const response = await fetch(`/api/models/${selectedModelId}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `${tokenType} ${token}`
                    }
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const modelData = await response.json();
                
                // 显示模型信息
                const modelInfo = document.getElementById('modelInfo');
                if (modelInfo) {
                    modelInfo.innerHTML = `
                        <table class="table table-sm">
                            <tr>
                                <th>名称:</th>
                                <td>${modelData.name || modelData.id}</td>
                            </tr>
                            <tr>
                                <th>描述:</th>
                                <td>${modelData.description || '无描述'}</td>
                            </tr>
                            <tr>
                                <th>创建日期:</th>
                                <td>${new Date(modelData.created_at).toLocaleString()}</td>
                            </tr>
                        </table>
                    `;
                }
            } catch (error) {
                console.error('获取模型详情失败:', error);
                showNotification('获取模型详情失败: ' + error.message, 'error');
            }
        }
    });
    
    // 尝试加载模型列表
    loadModels();
}

// 加载模型列表
async function loadModels() {
    try {
        const modelSelect = document.getElementById('modelSelect');
        if (!modelSelect) return;
        
        // 获取认证令牌
        const token = localStorage.getItem('access_token');
        const tokenType = localStorage.getItem('token_type');
        
        if (!token || !tokenType) {
            console.error('未找到有效令牌');
            return;
        }
        
        // 显示加载状态
        modelSelect.innerHTML = '<option>加载中...</option>';
        
        // 获取模型列表
        const response = await fetch('/api/reconstruction/models', {
            method: 'GET',
            headers: {
                'Authorization': `${tokenType} ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const models = data.models || [];
        
        // 更新下拉列表
        modelSelect.innerHTML = '<option value="" selected disabled>-- 请选择模型 --</option>';
        
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.id;
            option.textContent = model.name || model.id;
            modelSelect.appendChild(option);
        });
        
        if (models.length === 0) {
            const option = document.createElement('option');
            option.disabled = true;
            option.textContent = '没有可用的模型';
            modelSelect.appendChild(option);
        }
    } catch (error) {
        console.error('加载模型列表失败:', error);
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            modelSelect.innerHTML = '<option value="" selected disabled>加载失败，请刷新页面重试</option>';
        }
    }
}

// 初始化上传表单
function initUploadForm() {
    const uploadForm = document.getElementById('uploadForm');
    if (!uploadForm) return;
    
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const imageFile = document.getElementById('imageFile');
        const modelSelect = document.getElementById('modelSelect');
        
        // 检查是否选择了文件和模型
        if (!imageFile.files.length) {
            showNotification('请选择图像文件', 'warning');
            return;
        }
        
        if (!modelSelect.value) {
            showNotification('请选择重建模型', 'warning');
            return;
        }
        
        try {
            // 创建FormData对象
            const formData = new FormData();
            formData.append('file', imageFile.files[0]);
            formData.append('model_id', modelSelect.value);
            
            // 获取认证令牌
            const token = localStorage.getItem('access_token');
            const tokenType = localStorage.getItem('token_type');
            
            if (!token || !tokenType) {
                console.error('未找到有效令牌');
                return;
            }
            
            // 显示加载状态
            showLoading();
            
            // 预览上传的图像
            previewImage(imageFile.files[0]);
            
            // 发送请求
            const response = await fetch('/api/reconstruction/start', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `${tokenType} ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // 更新任务状态
            document.getElementById('taskStatus').textContent = '处理中';
            document.getElementById('taskStatus').className = 'badge bg-warning';
            
            // 显示通知
            showNotification('重建任务已开始，请稍候...', 'info');
            
        } catch (error) {
            console.error('提交重建任务失败:', error);
            showNotification('提交重建任务失败: ' + error.message, 'error');
            hideLoading();
        }
    });
}

// 加载中状态控制
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
    }
}

function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('d-none');
    }
}

// 预览图像
function previewImage(file) {
    if (!file) return;
    
    const reader = new FileReader();
    const originalImagePreview = document.getElementById('originalImagePreview');
    
    reader.onload = function(e) {
        originalImagePreview.innerHTML = `<img src="${e.target.result}" alt="原始图像" class="preview-img">`;
    };
    
    reader.readAsDataURL(file);
}

// 初始化按钮
function initButtons() {
    // 帮助按钮已经在全局作用域进行绑定
    // 影像对比按钮已经在全局作用域进行绑定
    
    // 导出报告按钮
    const exportReportBtn = document.getElementById('exportReportBtn');
    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', function() {
            const exportReportModal = new bootstrap.Modal(document.getElementById('exportReportModal'));
            exportReportModal.show();
        });
    }
    
    // 确认导出按钮
    const confirmExportBtn = document.getElementById('confirmExportBtn');
    if (confirmExportBtn) {
        confirmExportBtn.addEventListener('click', function() {
            const format = document.querySelector('input[name="reportFormat"]:checked').value;
            const exportStatus = document.getElementById('exportStatus');
            
            if (format === 'pdf') {
                exportStatus.innerHTML = '<div class="alert alert-warning">PDF导出功能即将推出，敬请期待！</div>';
                return;
            }
            
            exportStatus.innerHTML = '<div class="alert alert-info">正在导出报告，请稍候...</div>';
            
            // 模拟导出过程
            setTimeout(function() {
                exportStatus.innerHTML = '<div class="alert alert-success">报告导出成功！</div>';
                
                // 创建模拟JSON数据
                const reportData = {
                    report_id: 'REP' + Date.now(),
                    generated_at: new Date().toISOString(),
                    analysis_type: 'full',
                    results: {
                        brain_volume: {
                            total: 1250,
                            gray_matter: 650,
                            white_matter: 450,
                            csf: 150
                        },
                        lesions: {
                            count: 0,
                            volume: 0,
                            confidence: 0.95
                        },
                        motion_artifacts: {
                            detected: false,
                            severity: 0,
                            confidence: 0.98
                        }
                    }
                };
                
                // 创建并下载JSON文件
                const dataStr = JSON.stringify(reportData, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                
                const link = document.createElement('a');
                link.setAttribute('href', dataUri);
                link.setAttribute('download', 'medical_analysis_report_' + Date.now() + '.json');
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
            }, 1500);
        });
    }
    
    // 开始分析按钮
    const startAnalysisBtn = document.getElementById('startAnalysisBtn');
    if (startAnalysisBtn) {
        startAnalysisBtn.addEventListener('click', function() {
            const taskIdInput = document.getElementById('taskIdInput');
            
            if (!taskIdInput.value.trim()) {
                showNotification('请输入重建任务ID', 'warning');
                return;
            }
            
            const analysisTaskId = document.getElementById('analysisTaskId');
            analysisTaskId.textContent = taskIdInput.value.trim();
            
            // 模拟分析过程
            showNotification('正在分析图像，请稍候...', 'info');
            simulateAnalysis();
        });
    }
}

// 模拟分析过程
function simulateAnalysis() {
    // 更新分析状态
    const diagnosisAlert = document.getElementById('diagnosisAlert');
    diagnosisAlert.innerHTML = '<i class="bi bi-clipboard2-pulse me-2"></i>正在进行图像分析，请稍候...';
    
    // 禁用分析按钮
    const startAnalysisBtn = document.getElementById('startAnalysisBtn');
    if (startAnalysisBtn) {
        startAnalysisBtn.disabled = true;
    }
    
    // 模拟分析延迟
    setTimeout(function() {
        // 更新分析面板数据
        updateAnalysisResults();
        
        // 恢复按钮状态
        if (startAnalysisBtn) {
            startAnalysisBtn.disabled = false;
        }
        
        // 更新分析状态
        diagnosisAlert.innerHTML = '<i class="bi bi-clipboard2-check me-2"></i>分析完成！系统未检测到明显异常。';
        
        showNotification('图像分析完成', 'success');
    }, 2000);
}

// 更新分析结果
function updateAnalysisResults() {
    // 更新体积分析数据
    document.getElementById('totalBrainVolume').textContent = '1235';
    document.getElementById('grayMatterVolume').textContent = '642';
    document.getElementById('whiteMatterVolume').textContent = '458';
    document.getElementById('csfVolume').textContent = '135';
    
    // 更新病灶检测数据
    document.getElementById('lesionsCount').textContent = '0';
    document.getElementById('lesionsTotalVolume').textContent = '0';
    document.getElementById('lesionsConfidence').textContent = '95%';
    
    // 更新运动伪影检测数据
    document.getElementById('motionArtifactValue').textContent = '未检测到';
    document.getElementById('motionSeverity').textContent = '0';
    document.getElementById('motionConfidence').textContent = '98%';
    
    // 更新异常列表
    document.getElementById('abnormalitiesList').innerHTML = `
        <li class="list-group-item text-success">
            <i class="bi bi-check-circle-fill me-2"></i>未检测到明显的运动伪影
        </li>
        <li class="list-group-item text-success">
            <i class="bi bi-check-circle-fill me-2"></i>未检测到病灶
        </li>
        <li class="list-group-item text-success">
            <i class="bi bi-check-circle-fill me-2"></i>脑体积指标在正常范围内
        </li>
    `;
} 