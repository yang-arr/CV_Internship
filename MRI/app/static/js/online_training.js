// 全局变量
let trainingChart = null;
let isTraining = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    initializeChart();
    setupEventListeners();
});

// 初始化训练曲线图表
function initializeChart() {
    const ctx = document.getElementById('trainingChart').getContext('2d');
    trainingChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '训练损失',
                data: [],
                borderColor: '#00607A',
                tension: 0.1,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
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
                    position: 'top',
                },
                title: {
                    display: true,
                    text: '训练损失曲线'
                }
            }
        }
    });
}

// 设置事件监听器
function setupEventListeners() {
    const trainingForm = document.getElementById('trainingForm');
    trainingForm.addEventListener('submit', handleTrainingSubmit);

    // 监听夜间模式切换
    document.addEventListener('themeChange', (e) => {
        const isDarkMode = e.detail.isDarkMode;
        updateChartTheme(isDarkMode);
    });
}

// 处理训练表单提交
async function handleTrainingSubmit(e) {
    e.preventDefault();
    if (isTraining) {
        alert('已有训练任务正在进行中');
        return;
    }

    const formData = new FormData();
    const trainingData = document.getElementById('trainingData').files;
    const modelArchitecture = document.getElementById('modelArchitecture').value;
    const learningRate = document.getElementById('learningRate').value;
    const batchSize = document.getElementById('batchSize').value;
    const epochs = document.getElementById('epochs').value;
    const modelName = document.getElementById('modelName').value;

    // 验证表单
    if (trainingData.length === 0) {
        alert('请选择训练数据');
        return;
    }
    if (!modelName) {
        alert('请输入模型保存名称');
        return;
    }

    // 添加表单数据
    for (let i = 0; i < trainingData.length; i++) {
        formData.append('training_data', trainingData[i]);
    }
    formData.append('model_architecture', modelArchitecture);
    formData.append('learning_rate', learningRate);
    formData.append('batch_size', batchSize);
    formData.append('epochs', epochs);
    formData.append('model_name', modelName);

    try {
        // 开始训练
        isTraining = true;
        showLoadingOverlay();
        updateUIForTrainingStart();

        // 发送训练请求
        const response = await fetch('/api/training/start', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('训练启动失败');
        }

        const { task_id } = await response.json();
        
        // 开始监控训练进度
        monitorTrainingProgress(task_id);
    } catch (error) {
        console.error('训练错误:', error);
        alert('训练启动失败: ' + error.message);
        resetUI();
    }
}

// 监控训练进度
async function monitorTrainingProgress(taskId) {
    const progressInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/training/progress/${taskId}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error('获取进度失败');
            }

            updateTrainingProgress(data);

            if (data.status === 'completed' || data.status === 'failed') {
                clearInterval(progressInterval);
                handleTrainingCompletion(data);
            }
        } catch (error) {
            console.error('进度监控错误:', error);
            clearInterval(progressInterval);
            alert('训练进度监控失败');
            resetUI();
        }
    }, 1000);
}

// 更新训练进度UI
function updateTrainingProgress(data) {
    // 更新进度条
    const progress = document.getElementById('trainingProgress');
    progress.style.width = `${data.progress}%`;
    progress.textContent = `${data.progress}%`;

    // 更新指标
    document.getElementById('currentEpoch').textContent = data.current_epoch;
    document.getElementById('currentLoss').textContent = data.current_loss.toFixed(4);

    // 更新图表
    updateChart(data);

    // 更新日志
    appendLog(data.log_message);
}

// 更新训练曲线图表
function updateChart(data) {
    if (!trainingChart) return;

    const dataset = trainingChart.data.datasets[0];
    dataset.data.push(data.current_loss);
    trainingChart.data.labels.push(data.current_epoch);
    trainingChart.update();
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

// 处理训练完成
function handleTrainingCompletion(data) {
    isTraining = false;
    hideLoadingOverlay();

    if (data.status === 'completed') {
        alert('训练完成！模型已保存。');
    } else {
        alert('训练失败: ' + data.error);
    }

    resetUI();
}

// 重置UI状态
function resetUI() {
    isTraining = false;
    hideLoadingOverlay();
    document.getElementById('trainingProgress').style.width = '0%';
    document.getElementById('trainingProgress').textContent = '0%';
    document.getElementById('currentEpoch').textContent = '0';
    document.getElementById('currentLoss').textContent = '-';
    document.getElementById('trainingForm').reset();
}

// 显示加载遮罩
function showLoadingOverlay() {
    document.getElementById('loadingOverlay').classList.remove('d-none');
}

// 隐藏加载遮罩
function hideLoadingOverlay() {
    document.getElementById('loadingOverlay').classList.add('d-none');
}

// 更新UI以开始训练
function updateUIForTrainingStart() {
    document.getElementById('startTrainingBtn').disabled = true;
    document.getElementById('trainingData').disabled = true;
    document.getElementById('modelArchitecture').disabled = true;
    document.getElementById('learningRate').disabled = true;
    document.getElementById('batchSize').disabled = true;
    document.getElementById('epochs').disabled = true;
    document.getElementById('modelName').disabled = true;
} 