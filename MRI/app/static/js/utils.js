// MRI系统公共工具函数库

/**
 * 主题切换功能
 * @param {HTMLElement} themeToggleElement 主题切换按钮元素
 * @param {HTMLElement} themeIconElement 主题图标元素(可选)
 */
function initThemeToggle(themeToggleElement, themeIconElement) {
    // 检查本地存储的主题偏好
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('night-mode');
        if (themeIconElement) {
            themeIconElement.classList.remove('bi-moon-fill');
            themeIconElement.classList.add('bi-sun-fill');
        }
    }

    // 添加主题切换事件
    if (themeToggleElement) {
        themeToggleElement.addEventListener('click', () => {
            document.body.classList.toggle('night-mode');

            if (document.body.classList.contains('night-mode')) {
                localStorage.setItem('theme', 'dark');
                if (themeIconElement) {
                    themeIconElement.classList.remove('bi-moon-fill');
                    themeIconElement.classList.add('bi-sun-fill');
                }
            } else {
                localStorage.setItem('theme', 'light');
                if (themeIconElement) {
                    themeIconElement.classList.remove('bi-sun-fill');
                    themeIconElement.classList.add('bi-moon-fill');
                }
            }
        });
    }
}

/**
 * 旧版主题切换支持（兼容旧代码）
 * @param {HTMLElement} themeToggleCheckbox 主题切换复选框元素
 */
function initLegacyThemeToggle(themeToggleCheckbox) {
    // 检查本地存储的主题偏好
    if (localStorage.getItem('nightMode') === 'true') {
        document.body.classList.add('night-mode');
        if (themeToggleCheckbox) {
            themeToggleCheckbox.checked = true;
        }
    }
    
    // 添加主题切换事件
    if (themeToggleCheckbox) {
        themeToggleCheckbox.addEventListener('change', () => {
            if (themeToggleCheckbox.checked) {
                document.body.classList.add('night-mode');
                localStorage.setItem('nightMode', 'true');
            } else {
                document.body.classList.remove('night-mode');
                localStorage.setItem('nightMode', 'false');
            }
        });
    }
}

/**
 * 辅助功能面板控制
 * @param {HTMLElement} accessibilityToggle 辅助功能切换按钮
 * @param {HTMLElement} accessibilityPanel 辅助功能面板
 * @param {HTMLElement} highContrastToggle 高对比度切换开关
 * @param {HTMLElement} increaseFontBtn 增大字体按钮
 * @param {HTMLElement} decreaseFontBtn 减小字体按钮
 * @param {HTMLElement} resetFontBtn 重置字体按钮
 */
function initAccessibilityControls(accessibilityToggle, accessibilityPanel, highContrastToggle, increaseFontBtn, decreaseFontBtn, resetFontBtn) {
    let baseFontSize = parseInt(localStorage.getItem('fontSize')) || 16; // 基础字体大小
    
    // 显示/隐藏辅助功能面板
    if (accessibilityToggle && accessibilityPanel) {
        accessibilityToggle.addEventListener('click', () => {
            if (accessibilityPanel.style.display === 'block') {
                accessibilityPanel.style.display = 'none';
            } else {
                accessibilityPanel.style.display = 'block';
            }
        });
    }

    // 高对比度模式切换
    if (highContrastToggle) {
        highContrastToggle.addEventListener('change', () => {
            if (highContrastToggle.checked) {
                document.body.classList.add('high-contrast');
                localStorage.setItem('highContrast', 'true');
            } else {
                document.body.classList.remove('high-contrast');
                localStorage.setItem('highContrast', 'false');
            }
        });

        // 检查本地存储的高对比度偏好
        if (localStorage.getItem('highContrast') === 'true') {
            document.body.classList.add('high-contrast');
            highContrastToggle.checked = true;
        }
    }

    // 字体大小控制
    if (increaseFontBtn) {
        increaseFontBtn.addEventListener('click', () => {
            baseFontSize += 2;
            updateFontSize(baseFontSize);
        });
    }

    if (decreaseFontBtn) {
        decreaseFontBtn.addEventListener('click', () => {
            if (baseFontSize > 14) {
                baseFontSize -= 2;
                updateFontSize(baseFontSize);
            }
        });
    }

    if (resetFontBtn) {
        resetFontBtn.addEventListener('click', () => {
            baseFontSize = 16;
            updateFontSize(baseFontSize);
            localStorage.removeItem('fontSize');
        });
    }

    // 从本地存储读取字体大小
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        baseFontSize = parseInt(savedFontSize);
        updateFontSize(baseFontSize);
    }
}

/**
 * 更新字体大小
 * @param {number} baseFontSize 基础字体大小
 */
function updateFontSize(baseFontSize) {
    document.documentElement.style.setProperty('--font-size-base', `${baseFontSize}px`);
    document.body.style.fontSize = `${baseFontSize}px`;
    localStorage.setItem('fontSize', baseFontSize.toString());
}

/**
 * 显示消息
 * @param {HTMLElement} messageElement 消息容器元素
 * @param {string} text 消息文本
 * @param {string} type 消息类型（'success', 'error'等）
 */
function showMessage(messageElement, text, type) {
    if (!messageElement) return;
    
    messageElement.textContent = text;
    messageElement.className = `message ${type}`;
    messageElement.style.display = 'block';
    
    // 应用动画
    requestAnimationFrame(() => {
        messageElement.style.animation = 'message-fade-in 0.3s forwards';
    });
}

/**
 * 显示加载状态
 * @param {HTMLElement} button 提交按钮元素
 * @param {HTMLElement} loadingIndicator 加载指示器元素
 * @param {HTMLElement} buttonText 按钮文本元素
 * @param {string} loadingText 加载中显示的文本
 */
function showLoading(button, loadingIndicator, buttonText, loadingText) {
    if (button) button.disabled = true;
    if (loadingIndicator) loadingIndicator.style.display = 'inline-block';
    if (buttonText && loadingText) buttonText.textContent = loadingText;
}

/**
 * 隐藏加载状态
 * @param {HTMLElement} button 提交按钮元素
 * @param {HTMLElement} loadingIndicator 加载指示器元素
 * @param {HTMLElement} buttonText 按钮文本元素
 * @param {string} originalText 原始按钮文本
 */
function hideLoading(button, loadingIndicator, buttonText, originalText) {
    if (button) button.disabled = false;
    if (loadingIndicator) loadingIndicator.style.display = 'none';
    if (buttonText && originalText) buttonText.textContent = originalText;
}

/**
 * 用户认证管理器
 */
const authManager = {
    // 获取当前存储的令牌
    getToken: function() {
        return localStorage.getItem('access_token');
    },
    
    // 获取令牌类型
    getTokenType: function() {
        return localStorage.getItem('token_type');
    },
    
    // 获取用户名
    getUsername: function() {
        return localStorage.getItem('username');
    },
    
    // 检查是否已登录
    isLoggedIn: function() {
        return !!this.getToken();
    },
    
    // 设置认证信息
    setAuth: function(username, token, tokenType) {
        localStorage.setItem('username', username);
        localStorage.setItem('access_token', token);
        localStorage.setItem('token_type', tokenType);
    },
    
    // 登出
    logout: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        localStorage.removeItem('username');
        window.location.href = '/login';
    }
};

/**
 * 获取默认的HTTP请求头
 * @returns {Object} 包含认证信息的请求头对象
 */
function getDefaultHeaders() {
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (authManager.isLoggedIn()) {
        headers['Authorization'] = `${authManager.getTokenType()} ${authManager.getToken()}`;
    }
    
    return headers;
}

/**
 * 安全的JSON解析
 * @param {string} jsonString JSON字符串
 * @param {*} defaultValue 解析失败时返回的默认值
 * @returns {*} 解析结果或默认值
 */
function safeJSONParse(jsonString, defaultValue = {}) {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error('JSON解析错误:', error);
        return defaultValue;
    }
}

/**
 * 防抖函数
 * @param {Function} func 要执行的函数
 * @param {number} wait 等待时间(毫秒)
 * @returns {Function} 防抖处理后的函数
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/**
 * 节流函数
 * @param {Function} func 要执行的函数
 * @param {number} limit 限制时间(毫秒)
 * @returns {Function} 节流处理后的函数
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}
