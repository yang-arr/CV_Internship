/**
 * 重建历史记录管理
 * 
 * 包含功能：
 * - 历史记录弹窗
 * - 历史记录列表展示
 * - 历史记录详情查看
 * - 历史记录笔记编辑
 * - 历史记录删除
 */

// 全局变量
const historyAPI = `${window.location.origin}/api/reconstruction-history`;
let historyData = [];
let currentPage = 1;
let pageSize = 10;
let totalPages = 1;

// DOM元素 - 这些将在函数中初始化
let historyBtn, historyModal, historyTableBody, historyPagination;
let historyDetailModal, historyDetailContent, historyDetailTitle;
let noteEditModal, noteEditForm, noteEditTextarea, currentHistoryId;

// 初始化函数
document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) {
        return;
    }
    
    initHistoryElements();
    setupHistoryEventListeners();
});

/**
 * 初始化历史记录DOM元素引用
 */
function initHistoryElements() {
    // 获取历史记录按钮和弹窗
    historyBtn = document.getElementById('historyBtn');
    historyModal = document.getElementById('historyModal');
    historyTableBody = document.getElementById('historyTableBody');
    historyPagination = document.getElementById('historyPagination');
    
    // 获取详情弹窗元素
    historyDetailModal = document.getElementById('historyDetailModal');
    historyDetailContent = document.getElementById('historyDetailContent');
    historyDetailTitle = document.getElementById('historyDetailTitle');
    
    // 获取笔记编辑弹窗元素
    noteEditModal = document.getElementById('noteEditModal');
    noteEditForm = document.getElementById('noteEditForm');
    noteEditTextarea = document.getElementById('noteEditTextarea');
}

/**
 * 设置历史记录相关的事件监听
 */
function setupHistoryEventListeners() {
    // 如果历史记录按钮存在，添加点击事件处理器
    if (historyBtn) {
        historyBtn.addEventListener('click', () => {
            openHistoryModal();
        });
    }
    
    // 如果笔记编辑表单存在，添加提交事件处理器
    if (noteEditForm) {
        noteEditForm.addEventListener('submit', (e) => {
            e.preventDefault();
            updateHistoryNote();
        });
    }
}

/**
 * 打开历史记录弹窗并加载数据
 */
function openHistoryModal() {
    currentPage = 1;
    loadHistoryData();
    // 使用Bootstrap的modal方法显示弹窗
    var modal = new bootstrap.Modal(historyModal);
    modal.show();
}

/**
 * 加载历史记录数据
 * @param {number} page - 页码，默认为1
 */
async function loadHistoryData(page = 1) {
    try {
        showLoading();
        currentPage = page;
        
        // 构建API URL，包含分页参数
        const url = `${historyAPI}?page=${page}&page_size=${pageSize}`;
        
        // 添加认证头
        const headers = {
            'Authorization': getAuthHeader()
        };
        
        const response = await fetch(url, { headers });
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/login';
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        historyData = data.records || [];
        totalPages = Math.ceil(data.total / data.page_size);
        
        renderHistoryTable(historyData);
        renderPagination(currentPage, totalPages);
        
        hideLoading();
    } catch (error) {
        console.error('加载历史记录数据时出错:', error);
        showMessage('加载历史记录失败: ' + error.message, 'danger');
        hideLoading();
    }
}

/**
 * 渲染历史记录表格
 * @param {Array} records - 历史记录数组
 */
function renderHistoryTable(records) {
    if (!historyTableBody) return;
    
    historyTableBody.innerHTML = '';
    
    if (records.length === 0) {
        // 如果没有记录，显示提示信息
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = `
            <td colspan="6" class="text-center">暂无历史记录</td>
        `;
        historyTableBody.appendChild(emptyRow);
        return;
    }
    
    // 遍历记录并创建表格行
    records.forEach((record, index) => {
        const row = document.createElement('tr');
        
        // 格式化日期时间
        const createdAt = new Date(record.created_at);
        const formattedDate = createdAt.toLocaleDateString('zh-CN');
        const formattedTime = createdAt.toLocaleTimeString('zh-CN');
        
        // 设置行内容
        row.innerHTML = `
            <td>${index + 1 + (currentPage - 1) * pageSize}</td>
            <td>${record.model_name || record.model_id}</td>
            <td>${formattedDate} ${formattedTime}</td>
            <td>
                <span class="badge ${record.status === 'completed' ? 'bg-success' : 'bg-warning'} rounded-pill">
                    ${record.status === 'completed' ? '完成' : '处理中'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-info view-history" data-id="${record.id}">
                    <i class="bi bi-eye-fill"></i> 查看
                </button>
                <button class="btn btn-sm btn-outline-danger delete-history" data-id="${record.id}">
                    <i class="bi bi-trash-fill"></i> 删除
                </button>
            </td>
        `;
        
        // 添加行到表格
        historyTableBody.appendChild(row);
        
        // 添加事件监听器
        const viewBtn = row.querySelector('.view-history');
        const deleteBtn = row.querySelector('.delete-history');
        
        viewBtn.addEventListener('click', () => viewHistoryDetail(record.id));
        deleteBtn.addEventListener('click', () => confirmDeleteHistory(record.id));
    });
}

/**
 * 渲染分页控件
 * @param {number} currentPage - 当前页码
 * @param {number} totalPages - 总页数
 */
function renderPagination(currentPage, totalPages) {
    if (!historyPagination) return;
    
    historyPagination.innerHTML = '';
    
    if (totalPages <= 1) {
        return; // 如果只有一页，不显示分页控件
    }
    
    // 创建上一页按钮
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" aria-label="Previous"><span aria-hidden="true">&laquo;</span></a>`;
    historyPagination.appendChild(prevLi);
    
    // 添加页码按钮
    for (let i = 1; i <= totalPages; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        historyPagination.appendChild(pageLi);
        
        // 添加点击事件处理器
        pageLi.addEventListener('click', (e) => {
            e.preventDefault();
            loadHistoryData(i);
        });
    }
    
    // 创建下一页按钮
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" aria-label="Next"><span aria-hidden="true">&raquo;</span></a>`;
    historyPagination.appendChild(nextLi);
    
    // 添加上一页、下一页事件处理器
    if (currentPage > 1) {
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            loadHistoryData(currentPage - 1);
        });
    }
    
    if (currentPage < totalPages) {
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            loadHistoryData(currentPage + 1);
        });
    }
}

/**
 * 查看历史记录详情
 * @param {number} id - 历史记录ID
 */
async function viewHistoryDetail(id) {
    try {
        showLoading();
        
        // 获取历史记录详情
        const url = `${historyAPI}/${id}`;
        const headers = {
            'Authorization': getAuthHeader()
        };
        
        const response = await fetch(url, { headers });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const record = await response.json();
        
        // 更新详情弹窗标题
        historyDetailTitle.textContent = `重建记录详情 (#${record.id})`;
        
        // 格式化日期时间
        const createdAt = new Date(record.created_at);
        const formattedDate = createdAt.toLocaleDateString('zh-CN');
        const formattedTime = createdAt.toLocaleTimeString('zh-CN');
        
        // 构建详情内容HTML
        let detailHtml = `
            <div class="row mb-4">
                <div class="col-md-6">
                    <h5>基本信息</h5>
                    <table class="table table-bordered">
                        <tr>
                            <th>模型</th>
                            <td>${record.model_name || record.model_id}</td>
                        </tr>
                        <tr>
                            <th>状态</th>
                            <td>
                                <span class="badge ${record.status === 'completed' ? 'bg-success' : 'bg-warning'} rounded-pill">
                                    ${record.status === 'completed' ? '完成' : '处理中'}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <th>重建时间</th>
                            <td>${formattedDate} ${formattedTime}</td>
                        </tr>
                        <tr>
                            <th>执行耗时</th>
                            <td>${record.execution_time ? record.execution_time.toFixed(2) + ' 秒' : '未记录'}</td>
                        </tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h5>评估指标</h5>
                    <table class="table table-bordered">
                        <tr>
                            <th>PSNR</th>
                            <td>${record.psnr ? record.psnr.toFixed(4) : '未记录'}</td>
                        </tr>
                        <tr>
                            <th>SSIM</th>
                            <td>${record.ssim ? record.ssim.toFixed(4) : '未记录'}</td>
                        </tr>
                        <tr>
                            <th>NSE</th>
                            <td>${record.nse ? record.nse.toFixed(4) : '未记录'}</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-12">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5>笔记</h5>
                        <button class="btn btn-sm btn-outline-primary edit-note" data-id="${record.id}">
                            <i class="bi bi-pencil-fill"></i> 编辑笔记
                        </button>
                    </div>
                    <div class="card">
                        <div class="card-body" id="noteContent">
                            ${record.notes ? record.notes : '<p class="text-muted">暂无笔记</p>'}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-md-6">
                    <h5>原始图像</h5>
                    <div class="image-container" style="min-height: 200px;">
                        <div class="text-center">
                            <img src="/api/upload/view?path=${encodeURIComponent(record.original_image_path)}" 
                                 class="img-fluid" alt="原始图像" id="detailOriginalImage">
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <h5>重建结果</h5>
                    <div class="image-container" style="min-height: 200px;">
                        <div class="text-center">
                            <img src="/api/upload/view?path=${encodeURIComponent(record.reconstructed_image_path)}" 
                                 class="img-fluid" alt="重建结果" id="detailReconstructedImage">
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 更新详情内容
        historyDetailContent.innerHTML = detailHtml;
        
        // 添加编辑笔记按钮事件监听器
        const editNoteBtn = historyDetailContent.querySelector('.edit-note');
        if (editNoteBtn) {
            editNoteBtn.addEventListener('click', () => openNoteEditModal(record.id, record.notes));
        }
        
        // 显示详情弹窗
        var modal = new bootstrap.Modal(historyDetailModal);
        modal.show();
        
        hideLoading();
    } catch (error) {
        console.error('获取历史记录详情时出错:', error);
        showMessage('获取历史记录详情失败: ' + error.message, 'danger');
        hideLoading();
    }
}

/**
 * 打开笔记编辑弹窗
 * @param {number} id - 历史记录ID
 * @param {string} notes - 当前笔记内容
 */
function openNoteEditModal(id, notes) {
    currentHistoryId = id;
    noteEditTextarea.value = notes || '';
    
    // 显示笔记编辑弹窗
    var modal = new bootstrap.Modal(noteEditModal);
    modal.show();
}

/**
 * 更新历史记录笔记
 */
async function updateHistoryNote() {
    try {
        if (!currentHistoryId) return;
        
        showLoading();
        
        const notes = noteEditTextarea.value;
        const url = `${historyAPI}/${currentHistoryId}/notes`;
        
        const response = await fetch(url, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': getAuthHeader()
            },
            body: JSON.stringify({ notes })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        await response.json();
        
        // 关闭笔记编辑弹窗
        const modal = bootstrap.Modal.getInstance(noteEditModal);
        modal.hide();
        
        // 更新详情弹窗中的笔记内容
        const noteContent = document.getElementById('noteContent');
        if (noteContent) {
            noteContent.innerHTML = notes || '<p class="text-muted">暂无笔记</p>';
        }
        
        // 刷新历史记录列表
        loadHistoryData(currentPage);
        
        showMessage('笔记更新成功', 'success');
        hideLoading();
    } catch (error) {
        console.error('更新笔记时出错:', error);
        showMessage('更新笔记失败: ' + error.message, 'danger');
        hideLoading();
    }
}

/**
 * 确认删除历史记录
 * @param {number} id - 历史记录ID
 */
function confirmDeleteHistory(id) {
    if (confirm('确定要删除这条历史记录吗？此操作不可恢复。')) {
        deleteHistory(id);
    }
}

/**
 * 删除历史记录
 * @param {number} id - 历史记录ID
 */
async function deleteHistory(id) {
    try {
        showLoading();
        
        const url = `${historyAPI}/${id}`;
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Authorization': getAuthHeader()
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        await response.json();
        
        // 刷新历史记录列表
        loadHistoryData(currentPage);
        
        showMessage('历史记录删除成功', 'success');
        hideLoading();
    } catch (error) {
        console.error('删除历史记录时出错:', error);
        showMessage('删除历史记录失败: ' + error.message, 'danger');
        hideLoading();
    }
}

/**
 * 获取认证头
 * @returns {string} 认证头
 */
function getAuthHeader() {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    return `${tokenType} ${token}`;
}

/**
 * 显示加载中遮罩
 */
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.remove('d-none');
    }
}

/**
 * 隐藏加载中遮罩
 */
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.classList.add('d-none');
    }
}

/**
 * 显示消息提示
 * @param {string} message - 消息内容
 * @param {string} type - 消息类型：success, info, warning, danger
 */
function showMessage(message, type = 'info') {
    // 创建提示框
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = "9999";
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // 添加到文档
    document.body.appendChild(alertDiv);
    
    // 5秒后自动消失
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(alertDiv);
        }, 300);
    }, 5000);
}

/**
 * 检查用户认证状态
 * @returns {boolean} 是否已认证
 */
function checkAuth() {
    const token = localStorage.getItem('access_token');
    const tokenType = localStorage.getItem('token_type');
    
    if (!token || !tokenType) {
        window.location.href = '/login';
        return false;
    }
    
    return true;
} 