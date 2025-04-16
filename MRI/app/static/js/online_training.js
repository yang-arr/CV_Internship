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
    const ctx = document.getElementById('training-chart').getContext('2d');
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
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
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
        // 创建auth实例
        const auth = new AuthManager();
        
        // 添加日志
        const logElement = document.getElementById('training-log');
        const logEntry = document.createElement('div');
        logEntry.textContent = '正在准备下载模型...';
        logElement.appendChild(logEntry);
        
        // 直接导航到下载URL
        // 这将触发浏览器的下载行为
        window.location.href = `/api/online-training/download/${currentTaskId}`;
        
        // 添加下载开始日志
        setTimeout(() => {
            const downloadLogEntry = document.createElement('div');
            downloadLogEntry.className = 'alert alert-success';
            downloadLogEntry.textContent = '模型下载已开始';
            logElement.appendChild(downloadLogEntry);
            logElement.scrollTop = logElement.scrollHeight;
        }, 1000);
        
    } catch (error) {
        console.error('下载模型时出错:', error);
        const logElement = document.getElementById('training-log');
        const errorEntry = document.createElement('div');
        errorEntry.className = 'alert alert-danger';
        errorEntry.textContent = `错误: ${error.message}`;
        logElement.appendChild(errorEntry);
    }
}

// 更新训练进度UI
function updateTrainingProgress(data) {
    const progressBar = document.getElementById('training-progress-bar');
    const statusElement = document.getElementById('training-status');
    const lossElement = document.getElementById('training-loss');
    const logElement = document.getElementById('training-log');
    const stopTrainingBtn = document.getElementById('stop-training-btn');
    const downloadModelBtn = document.getElementById('download-model-btn');

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

    // 更新损失值
    if (data.current_loss !== undefined) {
        lossElement.textContent = data.current_loss.toFixed(6);
        
        // 更新图表
        if (trainingChart) {
            const epoch = data.current_epoch || trainingChart.data.labels.length + 1;
            trainingChart.data.labels.push(epoch);
            trainingChart.data.datasets[0].data.push(data.current_loss);
            trainingChart.update();
        }
    }

    // 添加日志
    if (data.log_message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = data.log_message;
        logElement.appendChild(logEntry);
        logElement.scrollTop = logElement.scrollHeight;
    }

    // 如果训练完成或失败，停止轮询
    if (data.status === 'completed' || data.status === 'failed' || data.status === 'stopped') {
        stopPolling();
        
        if (data.status === 'completed' && data.model_path) {
            const logEntry = document.createElement('div');
            logEntry.className = 'alert alert-success';
            logEntry.textContent = `训练完成！模型已保存至: ${data.model_path}`;
            logElement.appendChild(logEntry);
        } else if (data.status === 'failed') {
            const logEntry = document.createElement('div');
            logEntry.className = 'alert alert-danger';
            logEntry.textContent = `训练失败: ${data.error || '未知错误'}`;
            logElement.appendChild(logEntry);
        } else if (data.status === 'stopped') {
            const logEntry = document.createElement('div');
            logEntry.className = 'alert alert-warning';
            logEntry.textContent = `训练已中断`;
            logElement.appendChild(logEntry);
        }
    }
}

// 开始轮询训练状态
function startPolling(taskId) {
    currentTaskId = taskId;
    
    // 确保之前的轮询已停止
    stopPolling();
    
    // 创建auth实例
    const auth = new AuthManager();
    
    // 启用停止训练按钮，禁用下载模型按钮
    document.getElementById('stop-training-btn').disabled = false;
    document.getElementById('download-model-btn').disabled = true;
    
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
    if (!trainingChart) return;

    const textColor = isDarkMode ? '#E0E0E0' : '#666666';
    const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

    trainingChart.options.scales.x.grid.color = gridColor;
    trainingChart.options.scales.y.grid.color = gridColor;
    trainingChart.options.scales.x.ticks.color = textColor;
    trainingChart.options.scales.y.ticks.color = textColor;
    trainingChart.options.plugins.title.color = textColor;
    trainingChart.options.plugins.legend.labels.color = textColor;

    trainingChart.update();
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

// 重置UI状态
function resetUI() {
    currentTaskId = null;
    pollingInterval = null;
    document.getElementById('training-progress-bar').style.width = '0%';
    document.getElementById('training-progress-bar').setAttribute('aria-valuenow', 0);
    document.getElementById('training-progress-bar').textContent = '0%';
    document.getElementById('training-status').textContent = '';
    document.getElementById('training-loss').textContent = '-';
    document.getElementById('stop-training-btn').disabled = true;
    document.getElementById('download-model-btn').disabled = true;
    document.getElementById('training-form').reset();
} 