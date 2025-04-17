/**
 * 认证工具类 - 处理系统的用户认证和授权
 */

class AuthManager {
    constructor() {
        this.tokenKey = 'access_token';
        this.tokenTypeKey = 'token_type';
        this.usernameKey = 'username';
        this.roleKey = 'user_role';
        this.initialized = false;
        this.apiBaseUrl = '/api';
        this.tokenUrl = '/api/auth/token'; // 确保这个URL与后端路由匹配
        
        // 受保护的路径列表，访问这些路径需要登录
        this.protectedPaths = [
            '/dashboard',
            '/reconstruction',
            '/medical-qa',
            '/online-training'
        ];
        
        // 仅管理员可访问的路径
        this.adminPaths = [
            '/admin'
        ];
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化认证管理器
     */
    init() {
        if (this.initialized) return;
        
        console.log('初始化认证管理器...');
        
        // 检查当前路径是否需要保护
        const currentPath = window.location.pathname;
        
        // 如果当前页面是受保护的，且用户未登录，则重定向到登录页面
        if (this.isProtectedPath(currentPath) && !this.isLoggedIn()) {
            console.log('未授权访问受保护页面，重定向到登录页面');
            window.location.href = '/login';
            return;
        }
        
        // 如果当前页面仅管理员可访问，且用户不是管理员，则重定向到仪表盘
        if (this.isAdminPath(currentPath) && !this.isAdmin()) {
            console.log('非管理员访问管理页面，重定向到仪表盘');
            window.location.href = '/dashboard';
            return;
        }
        
        // 为所有API请求添加认证头
        this.setupRequestInterceptor();
        
        // 更新页面上的UI元素
        this.updateUIElements();
        
        this.initialized = true;
    }
    
    /**
     * 判断用户是否已登录
     */
    isLoggedIn() {
        const token = localStorage.getItem(this.tokenKey);
        return !!token;
    }
    
    /**
     * 判断用户是否是管理员
     */
    isAdmin() {
        // 添加调试日志
        console.log('检查管理员权限');
        console.log('用户角色: ' + localStorage.getItem(this.roleKey));
        
        return this.isLoggedIn() && localStorage.getItem(this.roleKey) === 'admin';
    }
    
    /**
     * 判断路径是否是受保护的
     */
    isProtectedPath(path) {
        return this.protectedPaths.some(protectedPath => 
            path === protectedPath || path.startsWith(`${protectedPath}/`));
    }
    
    /**
     * 判断路径是否仅管理员可访问
     */
    isAdminPath(path) {
        return this.adminPaths.some(adminPath => 
            path === adminPath || path.startsWith(`${adminPath}/`));
    }
    
    /**
     * 设置API请求拦截器
     */
    setupRequestInterceptor() {
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = function(url, options = {}) {
            // 只拦截对API的请求
            if (url.toString().includes('/api/')) {
                // 获取授权头
                const token = localStorage.getItem(self.tokenKey);
                const tokenType = localStorage.getItem(self.tokenTypeKey) || 'Bearer';
                
                if (token) {
                    // 创建新的options对象
                    options = options || {};
                    options.headers = options.headers || {};
                    
                    // 添加Authorization头
                    options.headers['Authorization'] = `${tokenType} ${token}`;
                    
                    // 确保包含凭据（cookies）
                    options.credentials = 'include';
                }
            }
            
            // 调用原始fetch方法
            return originalFetch(url, options);
        };
        
        console.log('已设置请求拦截器');
    }
    
    /**
     * 更新页面上的UI元素
     */
    updateUIElements() {
        // 显示当前用户名
        const usernameElement = document.getElementById('currentUsername');
        if (usernameElement) {
            usernameElement.textContent = this.getUsername() || '用户';
        }
        
        // 根据用户角色显示或隐藏管理员入口
        const adminLink = document.getElementById('adminLink');
        if (adminLink) {
            if (this.isAdmin()) {
                console.log('当前用户是管理员，显示管理控制台按钮');
                adminLink.style.display = 'block';
            } else {
                console.log('当前用户不是管理员，隐藏管理控制台按钮');
                adminLink.style.display = 'none';
            }
        } else {
            console.log('未找到管理员链接元素');
        }
    }
    
    /**
     * 登出
     */
    logout() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.tokenTypeKey);
        localStorage.removeItem(this.usernameKey);
        localStorage.removeItem(this.roleKey);
        
        // 重定向到登录页面
        window.location.href = '/login';
    }
    
    /**
     * 获取当前用户名
     */
    getUsername() {
        return localStorage.getItem(this.usernameKey);
    }
    
    /**
     * 获取当前用户角色
     */
    getUserRole() {
        return localStorage.getItem(this.roleKey) || 'user';
    }
    
    // 通用的fetch方法，自动添加认证头
    async fetch(url, options = {}) {
        // 获取令牌
        const token = localStorage.getItem(this.tokenKey);
        const tokenType = localStorage.getItem(this.tokenTypeKey);
        
        if (!token || !tokenType) {
            throw new Error('未登录或令牌已过期');
        }
        
        // 构建请求选项
        const fetchOptions = {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `${tokenType} ${token}`
            }
        };
        
        return fetch(url, fetchOptions);
    }
}

// 创建全局认证管理器实例
const authManager = new AuthManager();

// 文档加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM完全加载，执行初始化');
    
    // 查找登出按钮并绑定事件
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            authManager.logout();
        });
    }
    
    // 立即更新UI元素
    authManager.updateUIElements();
});

// 导出认证管理器
window.authManager = authManager; 