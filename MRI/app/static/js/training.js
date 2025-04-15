// 全局变量
let lossChart = null;
let metricsChart = null;
let currentTaskId = null;
let progressInterval = null;
let trainingChart = null;

// DOM元素
const trainingForm = document.getElementById('training-form');
const trainingProgressContainer = document.getElementById('training-progress-container');
const trainingProgress = document.getElementById('training-progress');
const trainingStatus = document.getElementById('training-status');
const trainingLoss = document.getElementById('training-loss');
const trainingLog = document.getElementById('training-log');
const loadingOverlay = document.getElementById('loadingOverlay');

// UI状态管理
let isTraining = false;

// 显示加载状态
function showLoading() {
    isTraining = true;
    if (trainingForm) {
        const submitButton = trainingForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 训练中...';
        }
    }
    if (trainingProgressContainer) {
        trainingProgressContainer.style.display = 'block';
    }
}

// 隐藏加载状态
function hideLoading() {
    isTraining = false;
    if (trainingForm) {
        const submitButton = trainingForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = '开始训练';
        }
    }
}

// 重置UI状态
function resetUI() {
    hideLoading();
    if (trainingProgress) {
        trainingProgress.style.width = '0%';
        trainingProgress.textContent = '0%';
    }
    if (trainingStatus) {
        trainingStatus.textContent = '';
    }
    if (trainingLoss) {
        trainingLoss.textContent = '-';
    }
    if (trainingForm) {
        trainingForm.reset();
    }
}

// 初始化图表
function initCharts() {
    // 销毁已存在的图表实例
    if (lossChart) {
        lossChart.destroy();
    }
    if (metricsChart) {
        metricsChart.destroy();
    }
    
    // 损失值图表
    const lossCtx = document.getElementById('loss-chart').getContext('2d');
    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '训练损失',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // 验证指标图表
    const metricsCtx = document.getElementById('metrics-chart').getContext('2d');
    metricsChart = new Chart(metricsCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'PSNR',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1
            }, {
                label: 'SSIM',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    const ctx = document.getElementById('trainingChart').getContext('2d');
    trainingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '训练损失',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 更新训练进度
function updateProgress(progress, status, loss) {
    trainingProgress.style.width = `${progress}%`;
    trainingProgress.setAttribute('aria-valuenow', progress);
    trainingStatus.textContent = `状态: ${status}`;
    trainingLoss.textContent = `损失值: ${loss !== null ? loss.toFixed(4) : '-'}`;
}

// 添加日志
function addLog(message) {
    if (!message) return;
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `<small class="text-muted">[${timestamp}]</small> ${message}`;
    if (trainingLog) {
        trainingLog.appendChild(logEntry);
        trainingLog.scrollTop = trainingLog.scrollHeight;
    }
    console.log(`[${timestamp}] ${message}`); // 同时在控制台显示日志
}

// 更新图表
function updateCharts(epoch, loss, metrics) {
    // 更新损失图表
    lossChart.data.labels.push(epoch);
    lossChart.data.datasets[0].data.push(loss);
    lossChart.update();

    // 更新指标图表
    if (metrics) {
        metricsChart.data.labels.push(epoch);
        metricsChart.data.datasets[0].data.push(metrics.psnr);
        metricsChart.data.datasets[1].data.push(metrics.ssim);
        metricsChart.update();
    }
}

// 轮询训练进度
async function pollTrainingProgress(taskId) {
    try {
        const response = await fetch(`/api/training/progress/${taskId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Training progress data:', data); // 添加调试日志
        
        // 更新进度
        updateTrainingProgress(data);
        
        // 如果训练未完成，继续轮询
        if (data.status !== 'completed' && data.status !== 'failed') {
            setTimeout(() => pollTrainingProgress(taskId), 1000);
        } else {
            handleTrainingCompletion(data);
        }
    } catch (error) {
        console.error('轮询训练进度时出错:', error);
        addLog(`轮询出错: ${error.message}`);
    }
}

// 更新训练进度UI
function updateTrainingProgress(data) {
    console.log('Updating training progress:', data); // 添加调试日志
    
    // 更新进度条
    const progressBar = document.getElementById('trainingProgress');
    if (progressBar) {
        const progress = data.progress || 0;
        progressBar.style.width = `${progress}%`;
        progressBar.textContent = `${Math.round(progress)}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }

    // 更新状态和损失值
    const statusElement = document.getElementById('trainingStatus');
    if (statusElement) {
        statusElement.textContent = `状态: ${data.status || '未知'}`;
    }

    const lossElement = document.getElementById('trainingLoss');
    if (lossElement && data.current_loss !== undefined) {
        lossElement.textContent = `损失值: ${Number(data.current_loss).toFixed(4)}`;
    }

    // 更新图表
    if (trainingChart && data.current_epoch && data.current_loss !== undefined) {
        const dataset = trainingChart.data.datasets[0];
        dataset.data.push(data.current_loss);
        trainingChart.data.labels.push(data.current_epoch);
        trainingChart.update();
    }

    // 添加日志
    if (data.log_message) {
        addLog(data.log_message);
    }
}

// 处理训练完成
function handleTrainingCompletion(data) {
    hideLoading();
    
    if (data.status === 'completed') {
        addLog('训练完成！');
        if (data.model_path) {
            addLog(`模型已保存至: ${data.model_path}`);
        }
        alert('训练完成！模型已保存。');
    } else {
        addLog(`训练失败: ${data.error || '未知错误'}`);
        alert('训练失败: ' + (data.error || '未知错误'));
    }

    resetUI();
}

// 提交训练表单
trainingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    showLoading();
    
    try {
        const formData = new FormData(trainingForm);
        
        // 添加默认的训练配置
        if (!formData.has('encoder_mode')) {
            formData.append('encoder_mode', 'fourier');
        }
        if (!formData.has('in_features')) {
            formData.append('in_features', '2');
        }
        if (!formData.has('out_features')) {
            formData.append('out_features', '20');
        }
        if (!formData.has('coordinate_scales')) {
            formData.append('coordinate_scales', '[1.0, 1.0]');
        }
        if (!formData.has('mlp_hidden_features')) {
            formData.append('mlp_hidden_features', '256');
        }
        if (!formData.has('mlp_hidden_layers')) {
            formData.append('mlp_hidden_layers', '4');
        }
        if (!formData.has('omega_0')) {
            formData.append('omega_0', '30.0');
        }
        if (!formData.has('activation')) {
            formData.append('activation', 'sine');
        }
        if (!formData.has('supervision_mode')) {
            formData.append('supervision_mode', 'image');
        }
        if (!formData.has('lambda_tv')) {
            formData.append('lambda_tv', '1e-5');
        }
        if (!formData.has('use_gpu')) {
            formData.append('use_gpu', 'true');
        }
        if (!formData.has('save_interval')) {
            formData.append('save_interval', '500');
        }
        
        // 发送训练请求到训练API
        const response = await fetch('/api/training/start', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Training started:', data); // 调试日志
        
        if (!data.task_id) {
            throw new Error('服务器未返回任务ID');
        }
        
        // 显示进度容器
        if (trainingProgressContainer) {
            trainingProgressContainer.style.display = 'block';
        }
        
        // 清空日志
        if (trainingLog) {
            trainingLog.innerHTML = '';
        }
        addLog('训练任务已启动');
        
        // 开始轮询进度
        pollTrainingProgress(data.task_id);
        
    } catch (error) {
        console.error('提交训练请求时出错:', error);
        addLog(`提交失败: ${error.message}`);
        hideLoading();
    }
});

// 页面加载完成后初始化图表
document.addEventListener('DOMContentLoaded', initCharts);

// 处理表单提交
$('#trainingForm').on('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const files = $('#trainingData')[0].files;
    
    // 添加所有选择的文件
    for (let i = 0; i < files.length; i++) {
        formData.append('training_data', files[i]);
    }
    
    // 添加训练参数
    formData.append('epochs', $('#epochs').val());
    formData.append('batch_size', $('#batchSize').val());
    
    // 禁用提交按钮
    $('#trainingForm button').prop('disabled', true);
    
    // 显示训练状态区域
    $('#trainingStatus').show();
    $('#logArea').empty();
    $('.progress-bar').css('width', '0%');
    $('#statusText').html('正在开始训练...');
    
    // 发送训练请求
    fetch('/api/training/start', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.task_id) {
            currentTaskId = data.task_id;
            // 开始轮询进度
            progressInterval = setInterval(updateTrainingProgress, 1000);
        } else {
            throw new Error('未收到任务ID');
        }
    })
    .catch(error => {
        console.error('启动训练时出错:', error);
        alert('启动训练时出错');
        $('#trainingForm button').prop('disabled', false);
        $('#trainingStatus').hide();
    });
}); 