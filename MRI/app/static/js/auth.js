/**
 * 认证工具类 - 处理系统的用户认证和授权
 */

class AuthManager {
    constructor() {
        this.tokenKey = 'access_token';
        this.tokenTypeKey = 'token_type';
        this.usernameKey = 'username';
        this.initialized = false;
        this.apiBaseUrl = '/api';
        this.tokenUrl = '/api/auth/token'; // 确保这个URL与后端路由匹配
        
        // 受保护的路径列表，访问这些路径需要登录
        this.protectedPaths = [
            '/dashboard',
            '/reconstruction',
            '/medical-qa'
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
        
        // 为所有API请求添加认证头
        this.setupRequestInterceptor();
        
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
     * 判断路径是否是受保护的
     */
    isProtectedPath(path) {
        return this.protectedPaths.some(protectedPath => 
            path === protectedPath || path.startsWith(`${protectedPath}/`));
    }
    
    /**
     * 设置API请求拦截器
     */
    setupRequestInterceptor() {
        const originalFetch = window.fetch;
        const self = this;
        
        window.fetch = function(url, options = {}) {
            // 只拦截对API的请求
            if (url.toString().includes('/api/') || url.toString().includes('/dashboard')) {
                // 获取授权头
                const token = localStorage.getItem(self.tokenKey);
                const tokenType = localStorage.getItem(self.tokenTypeKey) || 'Bearer';
                
                if (token) {
                    // 创建新的options对象
                    options = options || {};
                    options.headers = options.headers || {};
                    
                    // 添加Authorization头 (确保首字母大写)
                    const headerValue = `${tokenType} ${token}`;
                    options.headers['Authorization'] = headerValue;
                    console.log(`添加认证头: ${headerValue}`);
                    
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
     * 登出
     */
    logout() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.tokenTypeKey);
        localStorage.removeItem(this.usernameKey);
        
        // 重定向到登录页面
        window.location.href = '/login';
    }
    
    /**
     * 获取当前用户名
     */
    getUsername() {
        return localStorage.getItem(this.usernameKey);
    }
}

// 创建全局认证管理器实例
const authManager = new AuthManager();

// 文档加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 查找登出按钮并绑定事件
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            authManager.logout();
        });
    }
    
    // 显示当前用户名
    const usernameElement = document.getElementById('currentUsername');
    if (usernameElement) {
        usernameElement.textContent = authManager.getUsername() || '用户';
    }
});

// 导出认证管理器
window.authManager = authManager; 