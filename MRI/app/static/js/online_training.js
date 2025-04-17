// 全局变量
let trainingChart = null;
let currentTaskId = null;
let pollingInterval = null;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeUI();
    initializeChart();
    setupEventListeners();
});

// 初始化UI
function initializeUI() {
    // 显示空状态提示
    document.getElementById('training-empty-state').style.display = 'block';
    
    // 隐藏进度容器
    document.getElementById('training-progress-container').style.display = 'none';
    
    // 检查暗黑模式
    const isDarkMode = document.body.classList.contains('night-mode');
    if (isDarkMode) {
        updateChartTheme(true);
    }
}

// 初始化训练曲线图表
function initializeChart() {
    console.log("初始化训练损失图表");
    const ctx = document.getElementById('training-chart').getContext('2d');
    
    // 检查是否已经存在图表实例
    if (trainingChart) {
        console.log("图表已存在，重置数据");
        trainingChart.data.labels = [];
        trainingChart.data.datasets[0].data = [];
        trainingChart.update();
        return;
    }
    
    // 创建新的图表实例
    trainingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '训练损失',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.2,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 150 // 减少动画时长以提高性能
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value.toExponential(2);
                        }
                    },
                    title: {
                        display: true,
                        text: '损失值'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: '训练轮次'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toExponential(4);
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
    
    console.log("图表初始化完成");
    
    // 检查暗黑模式并更新图表
    const isDarkMode = document.body.classList.contains('night-mode');
    if (isDarkMode) {
        updateChartTheme(true);
    }
}

// 设置事件监听器
function setupEventListeners() {
    const trainingForm = document.getElementById('training-form');
    trainingForm.addEventListener('submit', handleTrainingSubmit);

    // 监听夜间模式切换
    document.addEventListener('themeChange', (e) => {
        const isDarkMode = e.detail.isDarkMode;
        updateChartTheme(isDarkMode);
    });
    
    // 添加中断训练按钮事件
    document.getElementById('stop-training-btn').addEventListener('click', handleStopTraining);
    
    // 添加下载模型按钮事件
    document.getElementById('download-model-btn').addEventListener('click', handleDownloadModel);
}

// 处理训练表单提交
async function handleTrainingSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    try {
        // 显示加载中遮罩
        document.getElementById('loadingOverlay').classList.remove('d-none');
        
        // 隐藏空状态提示
        document.getElementById('training-empty-state').style.display = 'none';
        
        // 显示进度容器
        document.getElementById('training-progress-container').style.display = 'block';
        
        // 初始化图表
        if (!trainingChart) {
            initializeChart();
        }
        
        // 创建auth实例
        const auth = new AuthManager();
        
        // 发送训练请求
        const response = await auth.fetch('/api/online-training/', {
            method: 'POST',
            body: formData
        });
        
        // 隐藏加载中遮罩
        document.getElementById('loadingOverlay').classList.add('d-none');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        if (data.task_id) {
            // 开始轮询训练状态
            startPolling(data.task_id);
        } else {
            throw new Error('未收到任务ID');
        }
    } catch (error) {
        console.error('提交训练请求时出错:', error);
        const logElement = document.getElementById('training-log');
        const errorEntry = document.createElement('div');
        errorEntry.className = 'alert alert-danger';
        errorEntry.textContent = `错误: ${error.message}`;
        logElement.appendChild(errorEntry);
        
        // 隐藏加载中遮罩
        document.getElementById('loadingOverlay').classList.add('d-none');
    }
}

// 处理中断训练请求
async function handleStopTraining() {
    if (!currentTaskId) return;
    
    try {
        document.getElementById('stop-training-btn').disabled = true;
        
        // 显示加载中提示
        const logElement = document.getElementById('training-log');
        const logEntry = document.createElement('div');
        logEntry.textContent = '正在发送中断训练请求...';
        logElement.appendChild(logEntry);
        
        // 创建auth实例
        const auth = new AuthManager();
        
        // 发送中断训练请求
        const response = await auth.fetch(`/api/online-training/stop/${currentTaskId}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // 添加日志
        const statusLogEntry = document.createElement('div');
        statusLogEntry.className = 'alert alert-info';
        statusLogEntry.textContent = data.message || '训练已中断';
        logElement.appendChild(statusLogEntry);
        
        // 停止轮询
        stopPolling();
        
    } catch (error) {
        console.error('中断训练时出错:', error);
        const logElement = document.getElementById('training-log');
        const errorEntry = document.createElement('div');
        errorEntry.className = 'alert alert-danger';
        errorEntry.textContent = `错误: ${error.message}`;
        logElement.appendChild(errorEntry);
        
        // 如果出错，重新启用按钮
        document.getElementById('stop-training-btn').disabled = false;
    }
}

// 处理下载模型请求
async function handleDownloadModel() {
    if (!currentTaskId) return;
    
    try {
        // 添加日志
        const logElement = document.getElementById('training-log');
        const logEntry = document.createElement('div');
        logEntry.textContent = '正在准备下载模型...';
        logElement.appendChild(logEntry);
        
        // 显示加载中遮罩
        document.getElementById('loadingOverlay').classList.remove('d-none');
        
        // 创建auth实例
        const auth = new AuthManager();
        
        // 先检查模型权限
        try {
            const checkResponse = await auth.fetch(`/api/online-training/check-model/${currentTaskId}`);
            if (!checkResponse.ok) {
                // 如果检查失败，显示错误信息
                const errorData = await checkResponse.json();
                throw new Error(errorData.detail || '无权限下载此模型');
            }
        } catch (error) {
            throw new Error(`权限检查失败: ${error.message}`);
        }
        
        // 如果权限检查通过，继续下载
        const downloadLogEntry = document.createElement('div');
        downloadLogEntry.className = 'alert alert-success';
        downloadLogEntry.textContent = '模型下载已开始，请稍候...';
        logElement.appendChild(downloadLogEntry);
        
        // 构建下载链接
        const downloadURL = `/api/online-training/download/${currentTaskId}`;
        
        // 创建一个临时链接并模拟点击
        const link = document.createElement('a');
        link.href = downloadURL;
        link.setAttribute('download', `model_${currentTaskId}.pt`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 隐藏加载中遮罩
        setTimeout(() => {
            document.getElementById('loadingOverlay').classList.add('d-none');
        }, 1000);
        
    } catch (error) {
        console.error('下载模型时出错:', error);
        const logElement = document.getElementById('training-log');
        const errorEntry = document.createElement('div');
        errorEntry.className = 'alert alert-danger';
        errorEntry.textContent = `错误: ${error.message}`;
        logElement.appendChild(errorEntry);
        
        // 隐藏加载中遮罩
        document.getElementById('loadingOverlay').classList.add('d-none');
    }
}

// 更新训练进度UI
function updateTrainingProgress(data) {
    console.log("收到训练状态数据:", JSON.stringify(data)); // 添加日志，便于调试
    
    const progressBar = document.getElementById('training-progress-bar');
    const statusElement = document.getElementById('training-status');
    const lossElement = document.getElementById('training-loss');
    const logElement = document.getElementById('training-log');
    const stopTrainingBtn = document.getElementById('stop-training-btn');
    const downloadModelBtn = document.getElementById('download-model-btn');
    
    // 确保空状态提示被隐藏
    document.getElementById('training-empty-state').style.display = 'none';
    
    // 确保进度容器显示
    document.getElementById('training-progress-container').style.display = 'block';

    // 更新进度条
    if (data.progress !== undefined) {
        const progress = Math.round(data.progress);
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
        progressBar.textContent = `${progress}%`;
    }

    // 更新状态
    if (data.status) {
        // 状态显示文本转换
        let statusText = data.status;
        if (data.status === 'running') {
            statusText = '训练中';
        } else if (data.status === 'completed') {
            statusText = '已完成';
        } else if (data.status === 'failed') {
            statusText = '失败';
        } else if (data.status === 'stopping') {
            statusText = '正在停止...';
        } else if (data.status === 'stopped') {
            statusText = '已停止';
        }
        
        statusElement.textContent = statusText;
        
        // 根据状态启用或禁用按钮
        if (data.status === 'running') {
            stopTrainingBtn.disabled = false;
            downloadModelBtn.disabled = true;
        } else if (data.status === 'completed') {
            stopTrainingBtn.disabled = true;
            downloadModelBtn.disabled = false;
        } else if (data.status === 'failed' || data.status === 'stopped') {
            stopTrainingBtn.disabled = true;
            downloadModelBtn.disabled = true;
        } else if (data.status === 'stopping') {
            stopTrainingBtn.disabled = true; // 禁用停止按钮，防止重复点击
            downloadModelBtn.disabled = true;
        }
    }

    // 更新损失值（支持多种字段名称格式）
    if (data.current_loss !== undefined) {
        lossElement.textContent = data.current_loss.toExponential(4);
    } else if (data.loss !== undefined) {
        lossElement.textContent = data.loss.toExponential(4);
    } else if (data.current_loss_value !== undefined) {
        lossElement.textContent = data.current_loss_value.toExponential(4);
    }

    // 更新图表 - 支持多种历史记录字段名称
    const lossHistory = data.loss_history || data.losses || data.loss_values || [];
    
    // 检查是否有损失历史记录
    if (lossHistory && lossHistory.length > 0) {
        console.log(`更新图表，有${lossHistory.length}条历史记录`);
        
        // 创建标签
        const labels = Array.from({ length: lossHistory.length }, (_, i) => i + 1);
        
        // 确保图表已初始化
        if (!trainingChart) {
            console.log("图表未初始化，正在初始化...");
            initializeChart();
        }
        
        // 更新图表数据
        trainingChart.data.labels = labels;
        trainingChart.data.datasets[0].data = lossHistory;
        trainingChart.update();
    } else {
        // 如果没有历史记录但有当前损失值，也更新图表
        if (data.current_loss !== undefined || data.loss !== undefined) {
            const currentLoss = data.current_loss !== undefined ? data.current_loss : data.loss;
            console.log(`添加当前损失值到图表: ${currentLoss}`);
            
            // 确保图表已初始化
            if (!trainingChart) {
                initializeChart();
            }
            
            // 添加新的数据点
            if (trainingChart.data.labels.length === 0) {
                trainingChart.data.labels.push(1);
                trainingChart.data.datasets[0].data.push(currentLoss);
            } else {
                const nextEpoch = trainingChart.data.labels.length + 1;
                trainingChart.data.labels.push(nextEpoch);
                trainingChart.data.datasets[0].data.push(currentLoss);
            }
            
            // 限制显示的数据点数量，避免图表过于拥挤
            if (trainingChart.data.labels.length > 100) {
                trainingChart.data.labels.shift();
                trainingChart.data.datasets[0].data.shift();
            }
            
            trainingChart.update();
        }
    }

    // 添加日志 - 支持多种日志字段名称
    const logMessages = data.log_messages || data.logs || data.messages || [];
    if (logMessages && logMessages.length > 0) {
        for (const logMessage of logMessages) {
            // 创建新的日志条目
            const logEntry = document.createElement('div');
            logEntry.textContent = logMessage;
            logElement.appendChild(logEntry);
        }
        
        // 自动滚动到底部
        logElement.scrollTop = logElement.scrollHeight;
    } else if (data.log_message) {
        // 兼容单条日志消息
        const logEntry = document.createElement('div');
        logEntry.textContent = data.log_message;
        logElement.appendChild(logEntry);
        logElement.scrollTop = logElement.scrollHeight;
    }

    // 如果训练完成，停止轮询
    if (data.status === 'completed' || data.status === 'failed' || data.status === 'stopped') {
        stopPolling();
        
        // 根据状态添加特定日志
        const statusLogEntry = document.createElement('div');
        
        if (data.status === 'completed') {
            statusLogEntry.className = 'alert alert-success';
            statusLogEntry.textContent = '训练已完成！您现在可以下载模型或前往MRI重建页面使用它。';
        } else if (data.status === 'failed') {
            statusLogEntry.className = 'alert alert-danger';
            statusLogEntry.textContent = data.error || '训练失败，请检查日志了解详情。';
        } else if (data.status === 'stopped') {
            statusLogEntry.className = 'alert alert-warning';
            statusLogEntry.textContent = '训练已手动停止。';
        }
        
        logElement.appendChild(statusLogEntry);
        logElement.scrollTop = logElement.scrollHeight;
    }
}

// 开始轮询训练状态
function startPolling(taskId) {
    currentTaskId = taskId;
    
    // 确保之前的轮询已停止
    stopPolling();
    
    // 创建auth实例
    const auth = new AuthManager();
    
    // 清空图表数据
    if (trainingChart) {
        trainingChart.data.labels = [];
        trainingChart.data.datasets[0].data = [];
        trainingChart.update();
    } else {
        initializeChart();
    }
    
    // 启用停止训练按钮，禁用下载模型按钮
    document.getElementById('stop-training-btn').disabled = false;
    document.getElementById('download-model-btn').disabled = true;
    
    // 添加开始训练的日志
    const logElement = document.getElementById('training-log');
    const startLogEntry = document.createElement('div');
    startLogEntry.className = 'alert alert-info';
    startLogEntry.textContent = `开始训练任务 (ID: ${taskId})`;
    logElement.appendChild(startLogEntry);
    
    // 开始新的轮询
    pollingInterval = setInterval(async () => {
        try {
            const response = await auth.fetch(`/api/online-training/status/${taskId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            updateTrainingProgress(data);
        } catch (error) {
            console.error('轮询训练状态时出错:', error);
            
            // 添加错误日志
            const errorEntry = document.createElement('div');
            errorEntry.className = 'alert alert-danger';
            errorEntry.textContent = `轮询出错: ${error.message}`;
            logElement.appendChild(errorEntry);
            
            stopPolling();
        }
    }, 1000); // 每秒轮询一次
}

// 停止轮询
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// 更新图表主题
function updateChartTheme(isDarkMode) {
    console.log(`更新图表主题，夜间模式：${isDarkMode}`);
    if (!trainingChart) {
        console.log("图表未初始化，无需更新主题");
        return;
    }

    const textColor = isDarkMode ? '#E0E0E0' : '#666666';
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';
    const backgroundColor = isDarkMode ? 'rgba(0, 176, 255, 0.1)' : 'rgba(75, 192, 192, 0.1)';
    const borderColor = isDarkMode ? 'rgb(0, 176, 255)' : 'rgb(75, 192, 192)';

    // 检查并设置网格颜色
    if (trainingChart.options.scales && trainingChart.options.scales.x) {
        if (trainingChart.options.scales.x.grid) {
    trainingChart.options.scales.x.grid.color = gridColor;
        } else {
            trainingChart.options.scales.x.grid = { color: gridColor };
        }
        
        if (trainingChart.options.scales.x.ticks) {
            trainingChart.options.scales.x.ticks.color = textColor;
        } else {
            trainingChart.options.scales.x.ticks = { color: textColor };
        }
        
        if (trainingChart.options.scales.x.title) {
            trainingChart.options.scales.x.title.color = textColor;
        }
    }
    
    if (trainingChart.options.scales && trainingChart.options.scales.y) {
        if (trainingChart.options.scales.y.grid) {
    trainingChart.options.scales.y.grid.color = gridColor;
        } else {
            trainingChart.options.scales.y.grid = { color: gridColor };
        }
        
        if (trainingChart.options.scales.y.ticks) {
    trainingChart.options.scales.y.ticks.color = textColor;
        } else {
            trainingChart.options.scales.y.ticks = { color: textColor };
        }
        
        if (trainingChart.options.scales.y.title) {
            trainingChart.options.scales.y.title.color = textColor;
        }
    }
    
    // 设置图例颜色
    if (trainingChart.options.plugins && trainingChart.options.plugins.legend) {
        if (!trainingChart.options.plugins.legend.labels) {
            trainingChart.options.plugins.legend.labels = {};
        }
        trainingChart.options.plugins.legend.labels.color = textColor;
    }
    
    // 设置标题颜色
    if (trainingChart.options.plugins && trainingChart.options.plugins.title) {
    trainingChart.options.plugins.title.color = textColor;
    }
    
    // 更新数据集颜色
    if (trainingChart.data.datasets && trainingChart.data.datasets.length > 0) {
        trainingChart.data.datasets[0].borderColor = borderColor;
        trainingChart.data.datasets[0].backgroundColor = backgroundColor;
    }

    trainingChart.update();
    console.log("图表主题更新完成");
}

// 添加训练日志
function appendLog(message) {
    if (!message) return;

    const logContainer = document.getElementById('trainingLog');
    const logEntry = document.createElement('div');
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// 重置UI
function resetUI() {
    // 隐藏进度容器
    document.getElementById('training-progress-container').style.display = 'none';
    
    // 显示空状态提示
    document.getElementById('training-empty-state').style.display = 'block';
    
    // 重置进度条
    const progressBar = document.getElementById('training-progress-bar');
    progressBar.style.width = '0%';
    progressBar.setAttribute('aria-valuenow', 0);
    progressBar.textContent = '0%';
    
    // 重置状态和损失
    document.getElementById('training-status').textContent = '等待开始';
    document.getElementById('training-loss').textContent = '-';
    
    // 清空日志
    document.getElementById('training-log').innerHTML = '';
    
    // 禁用按钮
    document.getElementById('stop-training-btn').disabled = true;
    document.getElementById('download-model-btn').disabled = true;
    
    // 重置表单
    document.getElementById('training-form').reset();
    
    // 重置图表
    if (trainingChart) {
        trainingChart.data.labels = [];
        trainingChart.data.datasets[0].data = [];
        trainingChart.update();
    }
    
    // 重置全局变量
    currentTaskId = null;
    pollingInterval = null;
} 