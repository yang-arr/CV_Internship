// data_dashboard.js - 数据看板交互脚本

// 全局变量
let reconstructionTrendChart = null;
let qaTrendChart = null;
let isDarkMode = localStorage.getItem('theme') === 'dark';

// DOM 加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 应用主题设置
    applyThemeSettings();
    
    // 加载数据
    loadDashboardData();
    
    // 绑定事件
    document.getElementById('refreshBtn').addEventListener('click', loadDashboardData);
    document.getElementById('exportBtn').addEventListener('click', exportDashboardReport);
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);
});

// 应用主题设置
function applyThemeSettings() {
    // 检查本地存储中的主题偏好
    isDarkMode = localStorage.getItem('theme') === 'dark';
    if (isDarkMode) {
        document.body.classList.add('night-mode');
    }
    
    // 应用高对比度设置
    if (localStorage.getItem('highContrast') === 'true') {
        document.body.classList.add('high-contrast');
    }
    
    // 应用字体大小设置
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        const baseFontSize = parseInt(savedFontSize);
        document.documentElement.style.setProperty('--font-size-base', `${baseFontSize}px`);
        document.body.style.fontSize = `${baseFontSize}px`;
    }
}

// 处理登出
function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    window.location.href = '/login';
}

// 加载仪表盘数据
async function loadDashboardData() {
    showLoading(true);
    
    try {
        // 获取统计数据
        const statsResponse = await fetch('/api/dashboard/stats', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!statsResponse.ok) {
            throw new Error('获取统计数据失败');
        }
        
        const statsData = await statsResponse.json();
        
        // 更新统计卡片
        updateStatCards(statsData);
        
        // 更新系统性能指标
        updatePerformanceIndicators(statsData.system_performance);
        
        // 更新趋势图表
        updateTrendCharts(statsData.reconstruction_trend, statsData.qa_trend);
        
        // 获取最近的重建记录
        const recResponse = await fetch('/api/dashboard/recent-reconstructions', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!recResponse.ok) {
            throw new Error('获取最近重建记录失败');
        }
        
        const recData = await recResponse.json();
        
        // 获取最近的问答记录
        const qaResponse = await fetch('/api/dashboard/recent-qa', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!qaResponse.ok) {
            throw new Error('获取最近问答记录失败');
        }
        
        const qaData = await qaResponse.json();
        
        // 更新最近记录
        updateRecentReconstructions(recData.reconstructions);
        updateRecentQA(qaData.qa_records);
        
        // 更新数据更新时间
        document.getElementById('last-update-time').textContent = 
            new Date().toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        
        showLoading(false);
        
    } catch (error) {
        console.error('加载数据失败:', error);
        showLoading(false);
        showError('加载数据失败，请重试');
    }
}

// 显示/隐藏加载动画
function showLoading(show) {
    const loadingElement = document.getElementById('loading');
    const contentSections = document.querySelectorAll('#stats-section, #charts-section, #records-section');
    
    if (show) {
        loadingElement.style.display = 'block';
        contentSections.forEach(section => {
            if (section) section.style.opacity = '0.5';
        });
    } else {
        loadingElement.style.display = 'none';
        contentSections.forEach(section => {
            if (section) section.style.opacity = '1';
        });
    }
}

// 显示错误消息
function showError(message) {
    // 简单的错误提示，实际应用中可以使用模态框或toast
    alert(message);
}

// 更新统计卡片
function updateStatCards(data) {
    document.getElementById('models-count').textContent = data.models_count;
    document.getElementById('reconstructions-count').textContent = data.reconstructions.total;
    document.getElementById('qa-count').textContent = data.qa_sessions.total;
    document.getElementById('users-count').textContent = data.active_users.total;
}

// 更新系统性能指标
function updatePerformanceIndicators(performance) {
    // CPU使用率
    updateProgressBar('cpu-usage', performance.cpu_usage);
    
    // 内存使用率
    updateProgressBar('memory-usage', performance.memory_usage);
    
    // 磁盘使用率
    updateProgressBar('disk-usage', performance.disk_usage);
    
    // 响应时间 (假设范围是0-2秒，超过1秒显示为警告)
    const responseTimePercent = Math.min(performance.avg_response_time / 2 * 100, 100);
    const responseTimeBar = document.getElementById('response-time-bar');
    if (responseTimeBar) {
        responseTimeBar.style.width = `${responseTimePercent}%`;
        
        if (performance.avg_response_time > 1) {
            responseTimeBar.className = 'progress-bar bg-warning';
        } else {
            responseTimeBar.className = 'progress-bar';
        }
    }
    
    const responseTimeValue = document.getElementById('response-time-value');
    if (responseTimeValue) {
        responseTimeValue.textContent = `${performance.avg_response_time.toFixed(2)}s`;
    }
}

// 更新进度条
function updateProgressBar(id, value) {
    const bar = document.getElementById(`${id}-bar`);
    const valueElement = document.getElementById(`${id}-value`);
    
    if (!bar || !valueElement) return;
    
    bar.style.width = `${value}%`;
    valueElement.textContent = `${value}%`;
    
    // 根据使用率级别设置颜色
    if (value > 90) {
        bar.className = 'progress-bar bg-danger';
    } else if (value > 70) {
        bar.className = 'progress-bar bg-warning';
    } else {
        bar.className = 'progress-bar';
    }
}

// 更新趋势图表
function updateTrendCharts(reconstructionData, qaData) {
    const dates = reconstructionData.map(item => item.date);
    const recCounts = reconstructionData.map(item => item.count);
    const qaCounts = qaData.map(item => item.count);
    
    // 图表颜色设置
    const chartColors = {
        reconstruction: {
            line: isDarkMode ? 'rgba(0, 176, 255, 0.7)' : 'rgba(0, 96, 122, 0.7)',
            fill: isDarkMode ? 'rgba(0, 176, 255, 0.1)' : 'rgba(0, 96, 122, 0.1)'
        },
        qa: {
            line: isDarkMode ? 'rgba(255, 193, 7, 0.7)' : 'rgba(251, 140, 0, 0.7)',
            fill: isDarkMode ? 'rgba(255, 193, 7, 0.1)' : 'rgba(251, 140, 0, 0.1)'
        },
        text: isDarkMode ? '#E0E0E0' : '#666666',
        grid: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)'
    };
    
    // 重建趋势图
    if (reconstructionTrendChart) {
        reconstructionTrendChart.destroy();
    }
    
    const recCtx = document.getElementById('reconstruction-trend-chart').getContext('2d');
    reconstructionTrendChart = new Chart(recCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '重建数量',
                data: recCounts,
                borderColor: chartColors.reconstruction.line,
                backgroundColor: chartColors.reconstruction.fill,
                tension: 0.4,
                fill: true
            }]
        },
        options: getChartOptions('重建数量', chartColors)
    });
    
    // 问答趋势图
    if (qaTrendChart) {
        qaTrendChart.destroy();
    }
    
    const qaCtx = document.getElementById('qa-trend-chart').getContext('2d');
    qaTrendChart = new Chart(qaCtx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [{
                label: '问答数量',
                data: qaCounts,
                borderColor: chartColors.qa.line,
                backgroundColor: chartColors.qa.fill,
                tension: 0.4,
                fill: true
            }]
        },
        options: getChartOptions('问答数量', chartColors)
    });
}

// 获取图表配置
function getChartOptions(yAxisTitle, colors) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 2,
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: isDarkMode ? '#333' : 'white',
                titleColor: colors.text,
                bodyColor: colors.text,
                borderColor: colors.grid,
                borderWidth: 1
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                },
                ticks: {
                    color: colors.text
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: colors.grid
                },
                ticks: {
                    color: colors.text
                },
                title: {
                    display: true,
                    text: yAxisTitle,
                    color: colors.text
                }
            }
        }
    };
}

// 更新图表主题
function updateChartsTheme() {
    if (reconstructionTrendChart && qaTrendChart) {
        // 获取最新数据
        const recData = reconstructionTrendChart.data.datasets[0].data;
        const recLabels = reconstructionTrendChart.data.labels;
        const qaData = qaTrendChart.data.datasets[0].data;
        
        // 重新渲染图表
        updateTrendCharts(
            recLabels.map((date, i) => ({ date, count: recData[i] })),
            recLabels.map((date, i) => ({ date, count: qaData[i] }))
        );
    }
}

// 更新最近重建记录
function updateRecentReconstructions(reconstructions) {
    const container = document.getElementById('recent-reconstructions');
    container.innerHTML = '';
    
    if (reconstructions.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">暂无重建记录</p>';
        return;
    }
    
    reconstructions.forEach(rec => {
        const date = new Date(rec.timestamp);
        const formattedDate = date.toLocaleString('zh-CN');
        
        // 格式化指标数据
        let metricsHtml = '';
        if (rec.metrics) {
            const metrics = [];
            if (rec.metrics.psnr !== null) metrics.push(`PSNR: ${rec.metrics.psnr.toFixed(2)}`);
            if (rec.metrics.ssim !== null) metrics.push(`SSIM: ${rec.metrics.ssim.toFixed(4)}`);
            if (rec.metrics.nse !== null) metrics.push(`NSE: ${rec.metrics.nse.toFixed(4)}`);
            
            if (metrics.length > 0) {
                metricsHtml = `<div class="metrics-info mt-1"><small class="text-muted">${metrics.join(' | ')}</small></div>`;
            }
        }
        
        const recItem = document.createElement('div');
        recItem.className = 'record-item';
        recItem.innerHTML = `
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <strong>${rec.user}</strong> 使用 <span class="text-primary">${rec.model}</span> 完成重建
                    <div class="record-time">${formattedDate}</div>
                    ${metricsHtml}
                </div>
                <div>
                    <span class="badge ${rec.execution_time > 2 ? 'bg-warning' : 'bg-info'}">${rec.execution_time.toFixed(2)}s</span>
                    <button class="btn btn-sm btn-outline-primary mt-2 view-detail-btn" data-id="${rec.id}">
                        <i class="bi bi-eye-fill"></i> 查看
                    </button>
                </div>
            </div>
        `;
        
        container.appendChild(recItem);
        
        // 添加查看详情事件
        const viewBtn = recItem.querySelector('.view-detail-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', () => {
                viewReconstructionDetail(rec.id);
            });
        }
    });
}

// 查看重建记录详情
async function viewReconstructionDetail(id) {
    try {
        showLoading(true);
        
        // 获取重建记录详情
        const response = await fetch(`/api/dashboard/reconstruction/${id}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`获取详情失败: ${response.status}`);
        }
        
        const detail = await response.json();
        
        // 创建模态框
        const modalId = 'reconstructionDetailModal';
        let modal = document.getElementById(modalId);
        
        // 如果模态框不存在，创建一个新的
        if (!modal) {
            modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = modalId;
            modal.tabIndex = -1;
            modal.setAttribute('aria-labelledby', `${modalId}Label`);
            modal.setAttribute('aria-hidden', 'true');
            
            document.body.appendChild(modal);
        }
        
        // 创建模态框内容
        const createdAt = new Date(detail.created_at);
        const formattedDate = createdAt.toLocaleString('zh-CN');
        
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="${modalId}Label">重建记录详情 #${detail.id}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-4">
                            <div class="col-md-6">
                                <h6>基本信息</h6>
                                <table class="table table-bordered">
                                    <tr>
                                        <th>用户</th>
                                        <td>${detail.user}</td>
                                    </tr>
                                    <tr>
                                        <th>模型</th>
                                        <td>${detail.model_name || detail.model_id}</td>
                                    </tr>
                                    <tr>
                                        <th>状态</th>
                                        <td>
                                            <span class="badge ${detail.status === 'completed' ? 'bg-success' : 'bg-warning'}">
                                                ${detail.status === 'completed' ? '完成' : '处理中'}
                                            </span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <th>重建时间</th>
                                        <td>${formattedDate}</td>
                                    </tr>
                                    <tr>
                                        <th>执行耗时</th>
                                        <td>${detail.execution_time ? detail.execution_time.toFixed(2) + ' 秒' : '未记录'}</td>
                                    </tr>
                                </table>
                            </div>
                            <div class="col-md-6">
                                <h6>评估指标</h6>
                                <table class="table table-bordered">
                                    <tr>
                                        <th>PSNR</th>
                                        <td>${detail.psnr ? detail.psnr.toFixed(4) : '未记录'}</td>
                                    </tr>
                                    <tr>
                                        <th>SSIM</th>
                                        <td>${detail.ssim ? detail.ssim.toFixed(4) : '未记录'}</td>
                                    </tr>
                                    <tr>
                                        <th>NSE</th>
                                        <td>${detail.nse ? detail.nse.toFixed(4) : '未记录'}</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <h6>原始图像</h6>
                                    <div class="image-container text-center">
                                        <img src="/api/upload/view?path=${encodeURIComponent(detail.original_image_path)}" 
                                             class="img-fluid" style="max-height: 250px;" alt="原始图像">
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <h6>重建结果</h6>
                                    <div class="image-container text-center">
                                        <img src="/api/upload/view?path=${encodeURIComponent(detail.reconstructed_image_path)}" 
                                             class="img-fluid" style="max-height: 250px;" alt="重建结果">
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        ${detail.notes ? `
                        <div class="row mt-3">
                            <div class="col-12">
                                <h6>笔记</h6>
                                <div class="card">
                                    <div class="card-body">
                                        ${detail.notes}
                                    </div>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">关闭</button>
                    </div>
                </div>
            </div>
        `;
        
        // 显示模态框
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        showLoading(false);
    } catch (error) {
        console.error('获取重建记录详情失败:', error);
        showError('获取重建记录详情失败: ' + error.message);
        showLoading(false);
    }
}

// 更新最近问答记录
function updateRecentQA(qaRecords) {
    const container = document.getElementById('recent-qa');
    container.innerHTML = '';
    
    if (qaRecords.length === 0) {
        container.innerHTML = '<p class="text-center text-muted">暂无问答记录</p>';
        return;
    }
    
    qaRecords.forEach(qa => {
        const date = new Date(qa.timestamp);
        const formattedDate = date.toLocaleString('zh-CN');
        
        const qaItem = document.createElement('div');
        qaItem.className = 'record-item';
        qaItem.innerHTML = `
            <div>
                <strong>${qa.user}</strong> 提问：<span class="text-primary">${qa.question}</span>
                <div class="record-time">${formattedDate}</div>
            </div>
        `;
        
        container.appendChild(qaItem);
    });
}

// 导出看板报告
function exportDashboardReport() {
    alert('将生成数据看板报告PDF并下载');
    // 实际实现可以使用html2canvas + jsPDF等库生成PDF报告
} 