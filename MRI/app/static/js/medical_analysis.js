/**
 * 医学图像分析模块
 * 用于对重建后的MRI图像进行医学分析
 * 包含脑体积分析、病灶检测和运动伪影检测等功能
 */

// 全局变量
let currentTaskId = null;
let currentAnalysisResults = null;
let brainRenderer = null;
let analysisMode = 'volume'; // 默认分析模式：volume, lesion, motion, full

// AMI.js和Three.js相关变量
let container = null;
let renderer = null;
let scene = null;
let camera = null;
let controls = null;
let brainMesh = null;
let lesionMeshes = [];
let isMeshLoaded = false;

// 初始化函数
document.addEventListener('DOMContentLoaded', function() {
    // 检查Medical Analysis面板是否存在
    if (!document.getElementById('medicalAnalysisPanel')) {
        console.log('Medical Analysis面板不存在，跳过初始化');
        return;
    }
    
    console.log('初始化医学分析模块');
    
    // 绑定按钮事件
    document.getElementById('startAnalysisBtn').addEventListener('click', startAnalysis);
    document.getElementById('volumeAnalysisBtn').addEventListener('click', () => switchAnalysisMode('volume'));
    document.getElementById('lesionAnalysisBtn').addEventListener('click', () => switchAnalysisMode('lesion'));
    document.getElementById('motionAnalysisBtn').addEventListener('click', () => switchAnalysisMode('motion'));
    document.getElementById('fullAnalysisBtn').addEventListener('click', () => switchAnalysisMode('full'));
    document.getElementById('exportReportBtn').addEventListener('click', exportReport);
    
    // 检查URL参数中是否有任务ID，如果有则自动启动分析
    const urlParams = new URLSearchParams(window.location.search);
    const taskId = urlParams.get('task_id');
    if (taskId) {
        currentTaskId = taskId;
        document.getElementById('analysisTaskId').textContent = taskId;
        loadAnalysisResults(taskId);
    }
    
    // 初始化3D渲染容器
    initRenderer();
});

// 初始化3D渲染器
function initRenderer() {
    try {
        // 获取容器元素
        container = document.getElementById('brain3DView');
        if (!container) {
            console.error('未找到3D渲染容器');
            return;
        }
        
        console.log('初始化3D渲染器');
        
        // 创建Three.js场景
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x2a2a2a);
        
        // 创建相机
        const width = container.clientWidth;
        const height = container.clientHeight;
        if (width === 0 || height === 0) {
            console.error('容器尺寸无效:', width, height);
            return;
        }
        
        camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
        camera.position.set(0, 0, 150);
        
        // 创建渲染器
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(width, height);
        container.appendChild(renderer.domElement);
        
        // 创建相机控制器
        controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.minDistance = 50;
        controls.maxDistance = 200;
        controls.enablePan = true;
        controls.update();
        
        // 添加光源
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(0, 200, 100);
        scene.add(directionalLight);
        
        // 添加坐标轴辅助工具
        const axesHelper = new THREE.AxesHelper(50);
        scene.add(axesHelper);
        
        // 渲染循环
        function animate() {
            if (!renderer || !scene || !camera) {
                console.warn('渲染循环中断: 缺少渲染器、场景或相机');
                return;
            }
            
            requestAnimationFrame(animate);
            if (controls) controls.update();
            renderer.render(scene, camera);
        }
        
        // 启动渲染循环
        animate();
        
        // 添加窗口大小调整事件
        window.addEventListener('resize', function() {
            if (!container || !camera || !renderer) return;
            
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            if (width > 0 && height > 0) {
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            }
        });
        
        console.log('3D渲染器初始化完成');
    } catch (error) {
        console.error('初始化3D渲染器时出错:', error);
    }
}

// 开始分析
function startAnalysis() {
    const taskIdInput = document.getElementById('taskIdInput');
    const taskId = taskIdInput.value.trim();
    
    if (!taskId) {
        showNotification('请输入重建任务ID', 'warning');
        return;
    }
    
    currentTaskId = taskId;
    document.getElementById('analysisTaskId').textContent = taskId;
    document.getElementById('medicalAnalysisPanel').classList.add('loading');
    document.getElementById('analysisPanelContent').innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div><p class="mt-3">正在分析MRI图像，请稍候...</p></div>';
    
    // 发送API请求启动分析
    const formData = new FormData();
    formData.append('analysis_type', analysisMode);
    
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    if (!token || !tokenType) {
        console.error('未找到认证令牌');
        showNotification('请先登录', 'error');
        window.location.href = '/login';
        return;
    }
    
    console.log(`开始分析任务ID: ${taskId}, 分析类型: ${analysisMode}`);
    
    fetch(`/api/medical-analysis/analyze/${taskId}`, {
        method: 'POST',
        headers: {
            'Authorization': `${tokenType} ${token}`
        },
        body: formData
    })
    .then(response => {
        console.log('收到响应:', response.status, response.statusText);
        // 检查内容类型
        const contentType = response.headers.get('content-type');
        console.log('响应内容类型:', contentType);
        
        if (!response.ok) {
            throw new Error('分析请求失败：' + response.status);
        }
        
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                console.error('响应不是JSON格式:', text.substring(0, 300) + '...');
                throw new Error('服务器返回了非JSON格式的数据');
            });
        }
    })
    .then(data => {
        console.log('分析结果返回：', data);
        if (data.success) {
            loadAnalysisResults(taskId);
        } else {
            throw new Error(data.message || '分析请求失败');
        }
    })
    .catch(error => {
        console.error('分析请求错误：', error);
        document.getElementById('medicalAnalysisPanel').classList.remove('loading');
        showNotification('分析请求失败：' + error.message, 'error');
        
        // 恢复原始界面状态，但不刷新页面
        document.getElementById('analysisPanelContent').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                分析过程中出现错误：${error.message}
            </div>
            <div class="mt-3">
                <button class="btn btn-outline-primary" onclick="window.location.reload()">
                    <i class="bi bi-arrow-clockwise me-1"></i>刷新页面
                </button>
            </div>
        `;
    });
}

// 加载分析结果
function loadAnalysisResults(taskId) {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    console.log(`正在加载分析结果，任务ID: ${taskId}`);
    
    fetch(`/api/medical-analysis/analysis/${taskId}`, {
        method: 'GET',
        headers: {
            'Authorization': `${tokenType} ${token}`
        }
    })
    .then(response => {
        console.log('加载结果响应:', response.status, response.statusText);
        // 检查内容类型
        const contentType = response.headers.get('content-type');
        console.log('响应内容类型:', contentType);
        
        if (!response.ok) {
            throw new Error('获取分析结果失败：' + response.status);
        }
        
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                console.error('响应不是JSON格式:', text.substring(0, 300) + '...');
                throw new Error('服务器返回了非JSON格式的数据');
            });
        }
    })
    .then(data => {
        console.log('获取结果成功:', data);
        document.getElementById('medicalAnalysisPanel').classList.remove('loading');
        
        if (data.success) {
            currentAnalysisResults = data.results;
            displayAnalysisResults(data.results);
            
            try {
                if (data.results.visualization_data && data.results.visualization_data.brain_mesh) {
                    loadBrainMesh(data.results.visualization_data.brain_mesh);
                    
                    if (data.results.lesion_detection && 
                        data.results.lesion_detection.lesions_count > 0 && 
                        data.results.visualization_data.lesion_mesh) {
                        loadLesionMesh(data.results.visualization_data.lesion_mesh);
                    }
                } else {
                    console.warn('缺少可视化数据或脑部网格数据');
                }
            } catch (vizError) {
                console.error('加载3D可视化数据失败:', vizError);
                showNotification('3D可视化加载失败，但分析结果已显示', 'warning');
            }
        } else {
            throw new Error(data.message || '获取分析结果失败');
        }
    })
    .catch(error => {
        console.error('获取分析结果错误：', error);
        document.getElementById('medicalAnalysisPanel').classList.remove('loading');
        showNotification('获取分析结果失败：' + error.message, 'error');
        
        // 恢复原始界面状态，但不刷新页面
        document.getElementById('analysisPanelContent').innerHTML = `
            <div class="alert alert-danger">
                <i class="bi bi-exclamation-triangle-fill me-2"></i>
                获取分析结果时出错：${error.message}
            </div>
            <div class="mt-3">
                <button class="btn btn-outline-primary" onclick="window.location.reload()">
                    <i class="bi bi-arrow-clockwise me-1"></i>刷新页面
                </button>
            </div>
        `;
    });
}

// 显示分析结果
function displayAnalysisResults(results) {
    console.log('开始显示分析结果:', results);
    
    // 安全地设置元素属性的辅助函数
    function safeSetElement(id, propertyName, value) {
        const element = document.getElementById(id);
        if (element) {
            if (propertyName === 'className') {
                element.className = value;
            } else if (propertyName === 'innerHTML') {
                element.innerHTML = value;
            } else if (propertyName === 'textContent') {
                element.textContent = value;
            }
        } else {
            console.warn(`元素 ${id} 不存在，无法设置 ${propertyName}`);
        }
    }
    
    const medicalAnalysisPanel = document.getElementById('medicalAnalysisPanel');
    if (medicalAnalysisPanel) {
        medicalAnalysisPanel.classList.remove('loading');
    }
    
    let alertClass = 'alert-success';
    if (results.alert_level === 'warning') {
        alertClass = 'alert-warning';
    } else if (results.alert_level === 'alert') {
        alertClass = 'alert-danger';
    }
    
    // 更新诊断信息
    safeSetElement('diagnosisAlert', 'className', `alert ${alertClass}`);
    safeSetElement('diagnosisAlert', 'innerHTML', `<i class="bi bi-clipboard2-pulse me-2"></i>${results.diagnosis}`);
    
    // 更新体积分析结果
    const volumeAnalysis = results.volume_analysis;
    safeSetElement('totalBrainVolume', 'textContent', volumeAnalysis.total_volume);
    safeSetElement('grayMatterVolume', 'textContent', volumeAnalysis.gray_matter);
    safeSetElement('whiteMatterVolume', 'textContent', volumeAnalysis.white_matter);
    safeSetElement('csfVolume', 'textContent', volumeAnalysis.csf);
    
    // 更新体积异常指示
    if (volumeAnalysis.abnormal) {
        safeSetElement('volumeAbnormalIndicator', 'className', 'badge bg-warning text-dark');
        safeSetElement('volumeAbnormalIndicator', 'textContent', '异常');
    } else {
        safeSetElement('volumeAbnormalIndicator', 'className', 'badge bg-success');
        safeSetElement('volumeAbnormalIndicator', 'textContent', '正常');
    }
    
    // 更新病灶检测结果
    const lesionDetection = results.lesion_detection;
    safeSetElement('lesionsCount', 'textContent', lesionDetection.lesions_count);
    safeSetElement('lesionsTotalVolume', 'textContent', lesionDetection.total_volume);
    safeSetElement('lesionsConfidence', 'textContent', lesionDetection.confidence + '%');
    
    // 更新病灶异常指示
    if (lesionDetection.abnormal) {
        safeSetElement('lesionAbnormalIndicator', 'className', 'badge bg-danger');
        safeSetElement('lesionAbnormalIndicator', 'textContent', '异常');
    } else {
        safeSetElement('lesionAbnormalIndicator', 'className', 'badge bg-success');
        safeSetElement('lesionAbnormalIndicator', 'textContent', '正常');
    }
    
    // 更新运动伪影检测结果
    const motionDetection = results.motion_detection;
    safeSetElement('motionArtifactValue', 'textContent', motionDetection.has_artifact ? '存在' : '无');
    safeSetElement('motionSeverity', 'textContent', motionDetection.severity);
    safeSetElement('motionConfidence', 'textContent', motionDetection.confidence + '%');
    
    // 更新运动伪影异常指示
    if (motionDetection.abnormal) {
        safeSetElement('motionAbnormalIndicator', 'className', 'badge bg-warning text-dark');
        safeSetElement('motionAbnormalIndicator', 'textContent', '异常');
    } else {
        safeSetElement('motionAbnormalIndicator', 'className', 'badge bg-success');
        safeSetElement('motionAbnormalIndicator', 'textContent', '正常');
    }
    
    // 更新综合异常信息
    const abnormalitiesList = document.getElementById('abnormalitiesList');
    if (abnormalitiesList) {
        abnormalitiesList.innerHTML = '';
        
        if (results.abnormalities.length === 0) {
            abnormalitiesList.innerHTML = '<li class="list-group-item text-success"><i class="bi bi-check-circle me-2"></i>未发现异常</li>';
        } else {
            results.abnormalities.forEach(abnormality => {
                let icon = 'bi-exclamation-triangle';
                let textClass = 'text-warning';
                
                if (abnormality.type.includes('病灶')) {
                    icon = 'bi-exclamation-octagon';
                    textClass = 'text-danger';
                }
                
                const abnormalityItem = document.createElement('li');
                abnormalityItem.className = `list-group-item ${textClass}`;
                abnormalityItem.innerHTML = `
                    <i class="bi ${icon} me-2"></i>
                    <strong>${abnormality.type}:</strong> 
                    ${abnormality.value} ${abnormality.type.includes('体积') ? 'cm³' : ''}
                    ${abnormality.count ? `(${abnormality.count}个)` : ''}
                    <span class="float-end">可信度: ${abnormality.confidence}%</span>
                `;
                abnormalitiesList.appendChild(abnormalityItem);
            });
        }
    } else {
        console.warn('元素 abnormalitiesList 不存在');
    }
    
    // 更新雷达图
    try {
        updateRadarChart(results);
    } catch (error) {
        console.error('更新雷达图时出错:', error);
    }
    
    console.log('分析结果显示完成');
}

// 加载脑部3D网格
function loadBrainMesh(brainMeshData) {
    try {
        if (!scene) {
            console.error('3D场景未初始化');
            return;
        }
        
        if (!brainMeshData || !brainMeshData.vertices || !brainMeshData.faces) {
            console.error('脑部网格数据无效');
            return;
        }
        
        console.log('开始加载脑部3D网格, 顶点数量:', brainMeshData.vertices.length);
        
        // 清除旧的脑部网格
        if (brainMesh) {
            scene.remove(brainMesh);
            brainMesh = null;
        }
        
        // 创建顶点几何体
        const geometry = new THREE.BufferGeometry();
        
        // 设置顶点
        const vertices = new Float32Array(brainMeshData.vertices.flat());
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        
        // 设置面
        const indices = new Uint32Array(brainMeshData.faces.flat());
        geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        
        // 计算顶点法线
        geometry.computeVertexNormals();
        
        // 创建材质
        const material = new THREE.MeshPhongMaterial({
            color: 0x80b3ff,
            transparent: true,
            opacity: 0.9,
            side: THREE.DoubleSide,
            flatShading: false
        });
        
        // 创建网格
        brainMesh = new THREE.Mesh(geometry, material);
        scene.add(brainMesh);
        
        // 重置相机位置
        if (camera && controls) {
            camera.position.set(0, 0, 150);
            controls.update();
        }
        
        isMeshLoaded = true;
        console.log('脑部3D网格加载完成');
    } catch (error) {
        console.error('加载脑部3D网格时出错:', error);
    }
}

// 加载病灶3D网格
function loadLesionMesh(lesionMeshData) {
    try {
        if (!scene) {
            console.error('3D场景未初始化');
            return;
        }
        
        if (!lesionMeshData || !lesionMeshData.vertices || !lesionMeshData.faces) {
            console.error('病灶网格数据无效');
            return;
        }
        
        console.log('开始加载病灶3D网格, 顶点数量:', lesionMeshData.vertices.length);
        
        // 清除旧的病灶网格
        lesionMeshes.forEach(mesh => {
            if (mesh && scene.children.includes(mesh)) {
                scene.remove(mesh);
            }
        });
        lesionMeshes = [];
        
        // 创建顶点几何体
        const geometry = new THREE.BufferGeometry();
        
        // 设置顶点
        const vertices = new Float32Array(lesionMeshData.vertices.flat());
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        
        // 设置面
        const indices = new Uint32Array(lesionMeshData.faces.flat());
        geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        
        // 计算顶点法线
        geometry.computeVertexNormals();
        
        // 创建材质
        const material = new THREE.MeshPhongMaterial({
            color: 0xff5555,
            transparent: true,
            opacity: 0.8,
            side: THREE.DoubleSide,
            flatShading: false
        });
        
        // 创建网格
        const lesionMesh = new THREE.Mesh(geometry, material);
        scene.add(lesionMesh);
        lesionMeshes.push(lesionMesh);
        
        console.log('病灶3D网格加载完成');
    } catch (error) {
        console.error('加载病灶3D网格时出错:', error);
    }
}

// 切换分析模式
function switchAnalysisMode(mode) {
    analysisMode = mode;
    
    // 更新UI
    document.querySelectorAll('.analysis-mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    document.getElementById(`${mode}AnalysisBtn`).classList.add('active');
    
    // 如果已有分析结果，则切换显示内容
    if (currentAnalysisResults) {
        // 更新可视化部分
        switch (mode) {
            case 'volume':
                document.getElementById('volumeAnalysisTab').classList.add('show', 'active');
                document.getElementById('lesionAnalysisTab').classList.remove('show', 'active');
                document.getElementById('motionAnalysisTab').classList.remove('show', 'active');
                
                // 更新3D视图 - 只显示脑部，隐藏病灶
                if (brainMesh) {
                    brainMesh.visible = true;
                }
                lesionMeshes.forEach(mesh => {
                    mesh.visible = false;
                });
                break;
                
            case 'lesion':
                document.getElementById('volumeAnalysisTab').classList.remove('show', 'active');
                document.getElementById('lesionAnalysisTab').classList.add('show', 'active');
                document.getElementById('motionAnalysisTab').classList.remove('show', 'active');
                
                // 更新3D视图 - 显示脑部和病灶
                if (brainMesh) {
                    brainMesh.visible = true;
                    brainMesh.material.opacity = 0.4; // 降低脑部透明度以便查看病灶
                }
                lesionMeshes.forEach(mesh => {
                    mesh.visible = true;
                });
                break;
                
            case 'motion':
                document.getElementById('volumeAnalysisTab').classList.remove('show', 'active');
                document.getElementById('lesionAnalysisTab').classList.remove('show', 'active');
                document.getElementById('motionAnalysisTab').classList.add('show', 'active');
                
                // 更新3D视图 - 只显示脑部，隐藏病灶
                if (brainMesh) {
                    brainMesh.visible = true;
                    brainMesh.material.opacity = 0.9;
                }
                lesionMeshes.forEach(mesh => {
                    mesh.visible = false;
                });
                break;
                
            case 'full':
                // 在综合分析模式下，显示所有项，默认显示体积分析标签页
                document.getElementById('volumeAnalysisTab').classList.add('show', 'active');
                document.getElementById('lesionAnalysisTab').classList.remove('show', 'active');
                document.getElementById('motionAnalysisTab').classList.remove('show', 'active');
                
                // 更新3D视图 - 显示脑部和病灶
                if (brainMesh) {
                    brainMesh.visible = true;
                    brainMesh.material.opacity = 0.7;
                }
                lesionMeshes.forEach(mesh => {
                    mesh.visible = true;
                });
                break;
        }
    }
}

// 导出分析报告
function exportReport() {
    if (!currentTaskId) {
        showNotification('没有可导出的分析结果', 'warning');
        return;
    }
    
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    // 显示导出选项模态框
    const exportModal = new bootstrap.Modal(document.getElementById('exportReportModal'));
    exportModal.show();
    
    // 绑定导出按钮事件
    document.getElementById('confirmExportBtn').addEventListener('click', function() {
        const reportFormat = document.querySelector('input[name="reportFormat"]:checked').value;
        
        // 显示加载指示器
        document.getElementById('exportStatus').innerHTML = '<div class="spinner-border spinner-border-sm text-primary me-2" role="status"><span class="visually-hidden">加载中...</span></div> 正在生成报告...';
        
        fetch(`/api/medical-analysis/report/${currentTaskId}?report_format=${reportFormat}`, {
            method: 'GET',
            headers: {
                'Authorization': `${tokenType} ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('导出报告失败：' + response.status);
            }
            return response.json();
        })
        .then(data => {
            if (reportFormat === 'json') {
                // 创建一个Blob对象
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                // 创建下载链接
                const a = document.createElement('a');
                a.href = url;
                a.download = `medical_analysis_${currentTaskId}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                document.getElementById('exportStatus').innerHTML = '<i class="bi bi-check-circle text-success me-2"></i> 报告已导出';
                setTimeout(() => {
                    exportModal.hide();
                }, 1500);
            } else if (reportFormat === 'pdf') {
                if (data.success === false) {
                    document.getElementById('exportStatus').innerHTML = '<i class="bi bi-exclamation-circle text-warning me-2"></i> ' + data.message;
                } else {
                    document.getElementById('exportStatus').innerHTML = '<i class="bi bi-check-circle text-success me-2"></i> 报告已导出';
                    setTimeout(() => {
                        exportModal.hide();
                    }, 1500);
                }
            }
        })
        .catch(error => {
            console.error('导出报告错误：', error);
            document.getElementById('exportStatus').innerHTML = '<i class="bi bi-exclamation-circle text-danger me-2"></i> 导出失败: ' + error.message;
        });
    });
}

// 更新雷达图
function updateRadarChart(results) {
    const chartElement = document.getElementById('radarChart');
    if (!chartElement) {
        console.warn('雷达图元素不存在，无法更新雷达图');
        return;
    }
    
    try {
        const ctx = chartElement.getContext('2d');
        
        // 已有的Chart实例则销毁
        if (window.radarChart) {
            window.radarChart.destroy();
        }
        
        // 准备数据
        const data = {
            labels: ['灰质体积', '白质完整性', '脑脊液体积', '病灶数量', '对称性'],
            datasets: [{
                label: '当前患者',
                data: [
                    normalizeValue(results.volume_analysis.gray_matter, 600, 700),
                    normalizeValue(results.volume_analysis.white_matter, 400, 500),
                    normalizeValue(results.volume_analysis.csf, 100, 200),
                    normalizeValue(5 - results.lesion_detection.lesions_count, 0, 5),
                    normalizeValue(100 - results.motion_detection.severity * 10, 0, 100)
                ],
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgb(255, 99, 132)',
                pointBackgroundColor: 'rgb(255, 99, 132)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(255, 99, 132)'
            }, {
                label: '正常参考值',
                data: [80, 80, 80, 80, 80],
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                pointBackgroundColor: 'rgb(54, 162, 235)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(54, 162, 235)'
            }]
        };
        
        // 创建雷达图
        window.radarChart = new Chart(ctx, {
            type: 'radar',
            data: data,
            options: {
                elements: {
                    line: {
                        borderWidth: 3
                    }
                },
                scales: {
                    r: {
                        angleLines: {
                            display: true
                        },
                        suggestedMin: 0,
                        suggestedMax: 100
                    }
                }
            }
        });
        
        console.log('雷达图更新完成');
    } catch (error) {
        console.error('创建雷达图时出错:', error);
    }
}

// 归一化值到0-100范围
function normalizeValue(value, min, max) {
    if (value < min) return 0;
    if (value > max) return 100;
    return Math.round((value - min) / (max - min) * 100);
}

// 显示通知
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
        delay: 5000
    });
    
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

// 分析自定义上传图像
function analyzeCustomImage() {
    const fileInput = document.getElementById('customImageInput');
    const analysisType = document.getElementById('customAnalysisType').value;
    
    if (!fileInput.files || fileInput.files.length === 0) {
        showNotification('请选择一个图像文件', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    
    // 显示加载状态
    const medicalAnalysisPanel = document.getElementById('medicalAnalysisPanel');
    const analysisPanelContent = document.getElementById('analysisPanelContent');
    
    if (!medicalAnalysisPanel || !analysisPanelContent) {
        console.error('找不到必要的UI元素');
        showNotification('UI元素不存在，无法显示分析结果', 'error');
        return;
    }
    
    // 给加载界面一个唯一ID，以便后面识别
    const loadingId = 'loading-' + Date.now();
    
    medicalAnalysisPanel.classList.add('loading');
    analysisPanelContent.innerHTML = `<div id="${loadingId}" class="text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div><p class="mt-3">正在分析上传的图像，请稍候...</p></div>`;
    
    // 创建FormData对象
    const formData = new FormData();
    formData.append('file', file);
    formData.append('analysis_type', analysisType);
    
    // 获取认证令牌
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    if (!token || !tokenType) {
        console.error('未找到认证令牌');
        showNotification('请先登录', 'error');
        window.location.href = '/login';
        return;
    }
    
    console.log('开始上传和分析图像...', file.name, '分析类型:', analysisType);
    
    // 发送API请求
    fetch('/api/medical-analysis/analyze-upload', {
        method: 'POST',
        headers: {
            'Authorization': `${tokenType} ${token}`
        },
        body: formData
    })
    .then(response => {
        console.log('收到响应:', response.status, response.statusText);
        // 检查内容类型
        const contentType = response.headers.get('content-type');
        console.log('响应内容类型:', contentType);
        
        if (!response.ok) {
            throw new Error('分析请求失败：' + response.status);
        }
        
        if (contentType && contentType.includes('application/json')) {
            return response.json();
        } else {
            return response.text().then(text => {
                console.error('响应不是JSON格式:', text.substring(0, 300) + '...');
                throw new Error('服务器返回了非JSON格式的数据');
            });
        }
    })
    .then(data => {
        console.log('分析结果返回：', data);
        if (data.success) {
            currentTaskId = data.task_id;
            
            // 检查当前面板是否仍然是加载界面
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) {
                console.log('找到加载界面，重建分析面板内容');
                // 重建分析面板内容
                rebuildAnalysisPanelContent(analysisPanelContent);
            }
            
            const taskIdElement = document.getElementById('analysisTaskId');
            if (taskIdElement) {
                taskIdElement.textContent = data.task_id;
            } else {
                console.warn('analysisTaskId元素不存在');
            }
            
            // 显示分析结果
            currentAnalysisResults = data.results;
            try {
                displayAnalysisResults(data.results);
            } catch (displayError) {
                console.error('显示分析结果时出错:', displayError);
                showNotification('显示分析结果时出错', 'error');
            }
            
            // 加载3D模型
            try {
                if (data.results && data.results.visualization_data && data.results.visualization_data.brain_mesh) {
                    loadBrainMesh(data.results.visualization_data.brain_mesh);
                    
                    if (data.results.lesion_detection && 
                        data.results.lesion_detection.lesions_count > 0 && 
                        data.results.visualization_data.lesion_mesh) {
                        loadLesionMesh(data.results.visualization_data.lesion_mesh);
                    }
                } else {
                    console.warn('缺少可视化数据或脑部网格数据');
                }
            } catch (vizError) {
                console.error('加载3D可视化数据失败:', vizError);
            }
            
            showNotification('图像分析完成', 'success');
        } else {
            throw new Error(data.message || '分析请求失败');
        }
    })
    .catch(error => {
        console.error('分析请求错误：', error);
        
        if (medicalAnalysisPanel) {
            medicalAnalysisPanel.classList.remove('loading');
        }
        
        showNotification('分析请求失败：' + error.message, 'error');
        
        // 恢复原始界面状态，但不刷新页面
        if (analysisPanelContent) {
            analysisPanelContent.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    分析过程中出现错误：${error.message}
                </div>
                <div class="mt-3">
                    <button class="btn btn-outline-primary me-2" onclick="window.location.reload()">
                        <i class="bi bi-arrow-clockwise me-1"></i>刷新页面
                    </button>
                    <button class="btn btn-outline-secondary" onclick="document.getElementById('customImageAnalysisForm').reset();">
                        <i class="bi bi-x-circle me-1"></i>清除表单
                    </button>
                </div>
            `;
        }
    });
}

// 重建分析面板内容
function rebuildAnalysisPanelContent(container) {
    if (!container) return;
    
    // 构建面板的基本HTML结构
    container.innerHTML = `
        <div class="row mb-3">
            <div class="col-md-8">
                <div class="input-group">
                    <span class="input-group-text">重建任务ID</span>
                    <input type="text" class="form-control" id="taskIdInput" placeholder="输入任务ID">
                    <button class="btn btn-primary" id="startAnalysisBtn">
                        <i class="bi bi-play-fill me-1"></i>开始分析
                    </button>
                </div>
                <div class="form-text">当前分析任务ID: <span id="analysisTaskId">-</span></div>
            </div>
            <div class="col-md-4 text-end">
                <button class="btn btn-outline-secondary" id="exportReportBtn">
                    <i class="bi bi-file-earmark-text me-1"></i>导出报告
                </button>
            </div>
        </div>
        
        <!-- 添加自定义图像上传选项 -->
        <div class="row mb-3">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-light">
                        <i class="bi bi-upload me-1"></i>自定义图像分析
                    </div>
                    <div class="card-body">
                        <form id="customImageAnalysisForm" enctype="multipart/form-data" onsubmit="event.preventDefault(); analyzeCustomImage();">
                            <div class="row g-2 align-items-center">
                                <div class="col-md-8">
                                    <div class="input-group">
                                        <input type="file" class="form-control" id="customImageInput" name="file" accept="image/*">
                                        <select class="form-select" id="customAnalysisType" name="analysis_type">
                                            <option value="full" selected>综合分析</option>
                                            <option value="volume">脑体积分析</option>
                                            <option value="lesion">病灶检测</option>
                                            <option value="motion">运动伪影检测</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="col-md-4">
                                    <button type="submit" class="btn btn-success w-100" id="customAnalysisBtn">
                                        <i class="bi bi-lightning-fill me-1"></i>分析上传图像
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-success" id="diagnosisAlert">
            <i class="bi bi-clipboard2-pulse me-2"></i>等待分析结果...
        </div>
        
        <!-- 分析模式选择按钮组 -->
        <div class="btn-group w-100 mb-3" role="group">
            <button type="button" class="btn btn-outline-secondary analysis-mode-btn active" id="volumeAnalysisBtn">
                <i class="bi bi-lungs me-1"></i>脑体积分析
            </button>
            <button type="button" class="btn btn-outline-secondary analysis-mode-btn" id="lesionAnalysisBtn">
                <i class="bi bi-badge-8k me-1"></i>病灶检测
            </button>
            <button type="button" class="btn btn-outline-secondary analysis-mode-btn" id="motionAnalysisBtn">
                <i class="bi bi-arrows-move me-1"></i>运动伪影检测
            </button>
            <button type="button" class="btn btn-outline-secondary analysis-mode-btn" id="fullAnalysisBtn">
                <i class="bi bi-card-checklist me-1"></i>综合分析
            </button>
        </div>
        
        <div class="row">
            <!-- 左侧：分析结果 -->
            <div class="col-md-6">
                <div class="tab-content">
                    <!-- 体积分析标签页 -->
                    <div class="tab-pane fade show active" id="volumeAnalysisTab">
                        <h5 class="border-bottom pb-2 mb-3">脑体积分析 <span class="badge bg-success" id="volumeAbnormalIndicator">正常</span></h5>
                        <table class="table table-bordered">
                            <thead class="table-light">
                                <tr>
                                    <th>指标</th>
                                    <th>数值 (cm³)</th>
                                    <th>正常范围</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>总脑体积</td>
                                    <td id="totalBrainVolume">-</td>
                                    <td>1100 - 1400</td>
                                </tr>
                                <tr>
                                    <td>灰质体积</td>
                                    <td id="grayMatterVolume">-</td>
                                    <td>600 - 700</td>
                                </tr>
                                <tr>
                                    <td>白质体积</td>
                                    <td id="whiteMatterVolume">-</td>
                                    <td>400 - 500</td>
                                </tr>
                                <tr>
                                    <td>脑脊液体积</td>
                                    <td id="csfVolume">-</td>
                                    <td>100 - 200</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- 病灶检测标签页 -->
                    <div class="tab-pane fade" id="lesionAnalysisTab">
                        <h5 class="border-bottom pb-2 mb-3">病灶检测 <span class="badge bg-success" id="lesionAbnormalIndicator">正常</span></h5>
                        <table class="table table-bordered">
                            <thead class="table-light">
                                <tr>
                                    <th>指标</th>
                                    <th>数值</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>病灶数量</td>
                                    <td id="lesionsCount">-</td>
                                </tr>
                                <tr>
                                    <td>病灶总体积 (cm³)</td>
                                    <td id="lesionsTotalVolume">-</td>
                                </tr>
                                <tr>
                                    <td>检测置信度</td>
                                    <td id="lesionsConfidence">-</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- 运动伪影检测标签页 -->
                    <div class="tab-pane fade" id="motionAnalysisTab">
                        <h5 class="border-bottom pb-2 mb-3">运动伪影检测 <span class="badge bg-success" id="motionAbnormalIndicator">正常</span></h5>
                        <table class="table table-bordered">
                            <thead class="table-light">
                                <tr>
                                    <th>指标</th>
                                    <th>数值</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>运动伪影</td>
                                    <td id="motionArtifactValue">-</td>
                                </tr>
                                <tr>
                                    <td>严重程度 (0-10)</td>
                                    <td id="motionSeverity">-</td>
                                </tr>
                                <tr>
                                    <td>检测置信度</td>
                                    <td id="motionConfidence">-</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <!-- 雷达图 -->
                <div class="mt-4">
                    <h5 class="border-bottom pb-2 mb-3">综合评估</h5>
                    <canvas id="radarChart" width="100%" height="250"></canvas>
                </div>
                
                <!-- 异常列表 -->
                <div class="mt-4">
                    <h5 class="border-bottom pb-2 mb-3">异常检测结果</h5>
                    <ul class="list-group" id="abnormalitiesList">
                        <li class="list-group-item text-muted">等待分析结果...</li>
                    </ul>
                </div>
            </div>
            
            <!-- 右侧：3D可视化 -->
            <div class="col-md-6">
                <div class="card h-100">
                    <div class="card-header bg-dark text-white">
                        <i class="bi bi-cube me-2"></i>三维可视化
                    </div>
                    <div class="card-body p-0">
                        <div id="brain3DView" style="width: 100%; height: 400px;"></div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 重新绑定必要的事件处理
    const startAnalysisBtn = document.getElementById('startAnalysisBtn');
    if (startAnalysisBtn) {
        startAnalysisBtn.addEventListener('click', startAnalysis);
    }
    
    const volumeAnalysisBtn = document.getElementById('volumeAnalysisBtn');
    if (volumeAnalysisBtn) {
        volumeAnalysisBtn.addEventListener('click', () => switchAnalysisMode('volume'));
    }
    
    const lesionAnalysisBtn = document.getElementById('lesionAnalysisBtn');
    if (lesionAnalysisBtn) {
        lesionAnalysisBtn.addEventListener('click', () => switchAnalysisMode('lesion'));
    }
    
    const motionAnalysisBtn = document.getElementById('motionAnalysisBtn');
    if (motionAnalysisBtn) {
        motionAnalysisBtn.addEventListener('click', () => switchAnalysisMode('motion'));
    }
    
    const fullAnalysisBtn = document.getElementById('fullAnalysisBtn');
    if (fullAnalysisBtn) {
        fullAnalysisBtn.addEventListener('click', () => switchAnalysisMode('full'));
    }
    
    const exportReportBtn = document.getElementById('exportReportBtn');
    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', exportReport);
    }
    
    // 重新初始化3D渲染器
    initRenderer();
} 