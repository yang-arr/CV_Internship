// 设置页面脚本 - 主题和辅助功能的控制

// 获取DOM元素
const themeToggle = document.getElementById('themeToggle');
const highContrastToggle = document.getElementById('highContrastToggle');
const increaseFontBtn = document.getElementById('increaseFontBtn');
const decreaseFontBtn = document.getElementById('decreaseFontBtn');
const resetFontBtn = document.getElementById('resetFontBtn');
const currentFontSize = document.getElementById('currentFontSize');
const imageDescriptionToggle = document.getElementById('imageDescriptionToggle');
const browserInfo = document.getElementById('browserInfo');
const screenInfo = document.getElementById('screenInfo');
const logoutBtn = document.getElementById('logoutBtn');

// 基础字体大小
let baseFontSize = 16;

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    // 初始化主题设置
    initThemeSettings();
    
    // 初始化字体大小设置
    initFontSizeSettings();
    
    // 初始化高对比度设置
    initHighContrastSettings();
    
    // 初始化图像描述设置
    initImageDescriptionSettings();
    
    // 显示系统信息
    displaySystemInfo();
    
    // 初始化退出按钮
    initLogoutButton();
});

// 初始化主题设置
function initThemeSettings() {
    // 检查本地存储中的主题偏好
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('night-mode');
        themeToggle.checked = true;
    }
    
    // 主题切换事件监听
    themeToggle.addEventListener('change', () => {
        if (themeToggle.checked) {
            document.body.classList.add('night-mode');
            localStorage.setItem('theme', 'dark');
            
            // 使用自定义事件通知其他标签页
            dispatchStorageUpdateEvent('theme', 'dark');
        } else {
            document.body.classList.remove('night-mode');
            localStorage.setItem('theme', 'light');
            
            // 使用自定义事件通知其他标签页
            dispatchStorageUpdateEvent('theme', 'light');
        }
    });
}

// 初始化字体大小设置
function initFontSizeSettings() {
    // 从本地存储读取字体大小
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        baseFontSize = parseInt(savedFontSize);
        updateFontSize();
    }
    
    // 更新当前字体大小显示
    updateFontSizeDisplay();
    
    // 增大字体事件
    increaseFontBtn.addEventListener('click', () => {
        if (baseFontSize < 24) {  // 设置最大字体上限
            baseFontSize += 2;
            updateFontSize();
            updateFontSizeDisplay();
            
            // 使用自定义事件通知其他标签页
            dispatchStorageUpdateEvent('fontSize', baseFontSize.toString());
        }
    });
    
    // 减小字体事件
    decreaseFontBtn.addEventListener('click', () => {
        if (baseFontSize > 12) {  // 设置最小字体下限
            baseFontSize -= 2;
            updateFontSize();
            updateFontSizeDisplay();
            
            // 使用自定义事件通知其他标签页
            dispatchStorageUpdateEvent('fontSize', baseFontSize.toString());
        }
    });
    
    // 重置字体事件
    resetFontBtn.addEventListener('click', () => {
        baseFontSize = 16;
        updateFontSize();
        updateFontSizeDisplay();
        localStorage.removeItem('fontSize');
        
        // 使用自定义事件通知其他标签页
        dispatchStorageUpdateEvent('fontSize', null);
    });
}

// 更新字体大小
function updateFontSize() {
    document.documentElement.style.setProperty('--font-size-base', `${baseFontSize}px`);
    document.body.style.fontSize = `${baseFontSize}px`;
    localStorage.setItem('fontSize', baseFontSize.toString());
}

// 更新字体大小显示
function updateFontSizeDisplay() {
    if (baseFontSize === 16) {
        currentFontSize.textContent = '默认';
    } else {
        currentFontSize.textContent = `${baseFontSize}px`;
    }
}

// 初始化高对比度设置
function initHighContrastSettings() {
    // 检查本地存储的高对比度偏好
    if (localStorage.getItem('highContrast') === 'true') {
        document.body.classList.add('high-contrast');
        highContrastToggle.checked = true;
    }
    
    // 高对比度模式切换
    highContrastToggle.addEventListener('change', () => {
        if (highContrastToggle.checked) {
            document.body.classList.add('high-contrast');
            localStorage.setItem('highContrast', 'true');
            
            // 使用自定义事件通知其他标签页
            dispatchStorageUpdateEvent('highContrast', 'true');
        } else {
            document.body.classList.remove('high-contrast');
            localStorage.setItem('highContrast', 'false');
            
            // 使用自定义事件通知其他标签页
            dispatchStorageUpdateEvent('highContrast', 'false');
        }
    });
}

// 初始化图像描述设置
function initImageDescriptionSettings() {
    // 检查本地存储的图像描述偏好
    if (localStorage.getItem('imageDescription') === 'true') {
        imageDescriptionToggle.checked = true;
    }
    
    // 图像描述模式切换
    imageDescriptionToggle.addEventListener('change', () => {
        localStorage.setItem('imageDescription', imageDescriptionToggle.checked.toString());
        
        // 使用自定义事件通知其他标签页
        dispatchStorageUpdateEvent('imageDescription', imageDescriptionToggle.checked.toString());
    });
}

// 触发自定义存储更新事件，用于跨标签页通信
function dispatchStorageUpdateEvent(key, value) {
    // 创建一个与原生storage事件类似的自定义事件
    const event = new CustomEvent('storage', {
        detail: {
            key: key,
            newValue: value,
            oldValue: localStorage.getItem(key),
            storageArea: localStorage,
            url: window.location.href
        }
    });
    
    // 分发事件
    window.dispatchEvent(event);
}

// 显示系统信息
function displaySystemInfo() {
    // 获取浏览器信息
    const userAgent = navigator.userAgent;
    let browserName = "未知浏览器";
    
    if (userAgent.indexOf("Firefox") > -1) {
        browserName = "Firefox";
    } else if (userAgent.indexOf("Chrome") > -1) {
        browserName = "Chrome";
    } else if (userAgent.indexOf("Safari") > -1) {
        browserName = "Safari";
    } else if (userAgent.indexOf("Edge") > -1 || userAgent.indexOf("Edg") > -1) {
        browserName = "Edge";
    } else if (userAgent.indexOf("MSIE") > -1 || userAgent.indexOf("Trident") > -1) {
        browserName = "Internet Explorer";
    }
    
    browserInfo.textContent = `${browserName} (${navigator.appVersion.split(')')[0].split('(')[1]})`;
    
    // 获取屏幕分辨率
    screenInfo.textContent = `${window.screen.width} x ${window.screen.height}`;
}

// 初始化退出按钮
function initLogoutButton() {
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        // 如果存在authManager对象，使用它进行登出
        if (typeof authManager !== 'undefined') {
            authManager.logout();
        } else {
            // 备用登出逻辑
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('username');
            window.location.href = '/login';
        }
    });
} 