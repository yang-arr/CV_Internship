// 全局变量
let lossChart = null;
let metricsChart = null;
let currentTaskId = null;
let progressInterval = null;

// DOM元素
const trainingForm = document.getElementById('training-form');
const trainingProgressContainer = document.getElementById('training-progress-container');
const trainingProgress = document.getElementById('training-progress');
const trainingStatus = document.getElementById('training-status');
const trainingLoss = document.getElementById('training-loss');
const trainingLog = document.getElementById('training-log');
const loadingOverlay = document.getElementById('loadingOverlay');

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
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('p');
    logEntry.className = 'mb-1';
    logEntry.innerHTML = `<small class="text-muted">[${timestamp}]</small> ${message}`;
    trainingLog.appendChild(logEntry);
    trainingLog.scrollTop = trainingLog.scrollHeight;
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
        
        // 更新进度
        updateProgress(data.progress, data.status, data.loss);
        
        // 添加日志
        if (data.log_message) {
            addLog(data.log_message);
        }
        
        // 更新图表
        if (data.current_epoch > 0) {
            updateCharts(data.current_epoch, data.current_loss, data.metrics);
        }
        
        // 如果训练未完成，继续轮询
        if (data.status !== 'completed' && data.status !== 'failed') {
            setTimeout(() => pollTrainingProgress(taskId), 1000);
        } else {
            if (data.status === 'completed') {
                addLog('训练完成！');
            } else {
                addLog(`训练失败: ${data.error || '未知错误'}`);
            }
        }
    } catch (error) {
        console.error('轮询训练进度时出错:', error);
        addLog(`轮询出错: ${error.message}`);
    }
}

// 提交训练表单
trainingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // 显示加载遮罩
    loadingOverlay.classList.remove('d-none');
    
    try {
        const formData = new FormData(trainingForm);
        
        // 发送训练请求
        const response = await fetch('/api/training/start', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        currentTaskId = data.task_id;
        
        // 显示进度容器
        trainingProgressContainer.style.display = 'block';
        
        // 清空日志
        trainingLog.innerHTML = '';
        addLog('训练任务已启动');
        
        // 重置图表
        initCharts();
        
        // 开始轮询进度
        pollTrainingProgress(currentTaskId);
        
    } catch (error) {
        console.error('提交训练请求时出错:', error);
        addLog(`提交失败: ${error.message}`);
    } finally {
        // 隐藏加载遮罩
        loadingOverlay.classList.add('d-none');
    }
});

// 页面加载完成后初始化图表
document.addEventListener('DOMContentLoaded', initCharts);

// 更新训练状态的函数
function updateTrainingProgress() {
    if (!currentTaskId) return;
    
    fetch(`/api/training/progress/${currentTaskId}`)
        .then(response => response.json())
        .then(data => {
            // 更新进度条
            const progress = data.progress || 0;
            $('.progress-bar').css('width', `${progress}%`);
            $('.progress-bar').attr('aria-valuenow', progress);
            
            // 更新状态文本
            let statusText = `状态: ${data.status}<br>`;
            if (data.current_epoch) {
                statusText += `当前轮次: ${data.current_epoch}<br>`;
            }
            if (data.loss) {
                statusText += `损失值: ${data.loss}<br>`;
            }
            $('#statusText').html(statusText);
            
            // 添加日志
            if (data.logs && data.logs.length > 0) {
                const logArea = $('#logArea');
                data.logs.forEach(log => {
                    logArea.append(`<div>${log}</div>`);
                });
                // 滚动到底部
                logArea.scrollTop(logArea[0].scrollHeight);
            }
            
            // 如果训练完成或失败，停止轮询
            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(progressInterval);
                progressInterval = null;
                currentTaskId = null;
                
                if (data.status === 'completed') {
                    alert('训练完成！');
                } else {
                    alert('训练失败：' + (data.error || '未知错误'));
                }
                
                // 重置表单
                $('#trainingForm button').prop('disabled', false);
            }
        })
        .catch(error => {
            console.error('获取训练进度时出错:', error);
            clearInterval(progressInterval);
            progressInterval = null;
            currentTaskId = null;
            alert('获取训练进度时出错');
            $('#trainingForm button').prop('disabled', false);
        });
}

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