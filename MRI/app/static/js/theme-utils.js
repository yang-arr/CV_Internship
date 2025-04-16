/**
 * theme-utils.js - 通用主题工具
 * 用于在所有页面应用主题和辅助功能设置
 */

// 应用所有主题和辅助功能设置
function applyAllSettings() {
    // 应用夜间模式设置
    applyThemeSetting();
    
    // 应用高对比度设置
    applyContrastSetting();
    
    // 应用字体大小设置
    applyFontSizeSetting();
}

// 应用夜间模式设置
function applyThemeSetting() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('night-mode');
    } else {
        document.body.classList.remove('night-mode');
    }
}

// 应用高对比度设置
function applyContrastSetting() {
    if (localStorage.getItem('highContrast') === 'true') {
        document.body.classList.add('high-contrast');
    } else {
        document.body.classList.remove('high-contrast');
    }
}

// 应用字体大小设置
function applyFontSizeSetting() {
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        const baseFontSize = parseInt(savedFontSize);
        document.documentElement.style.setProperty('--font-size-base', `${baseFontSize}px`);
        document.body.style.fontSize = `${baseFontSize}px`;
    } else {
        // 重置为默认值
        document.documentElement.style.setProperty('--font-size-base', '16px');
        document.body.style.fontSize = '16px';
    }
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    console.log('Theme-utils: 正在应用主题设置...');
    // 应用所有设置
    applyAllSettings();
    
    // 设置事件监听，当localStorage变化时更新设置
    window.addEventListener('storage', (event) => {
        console.log('Theme-utils: 接收到存储变更事件', event);
        
        // 处理标准storage事件
        if (event.key === 'theme' || event.key === 'highContrast' || event.key === 'fontSize') {
            console.log(`Theme-utils: 应用${event.key}设置`);
            applyAllSettings();
        }
        
        // 处理自定义storage事件
        if (event.detail && event.detail.key) {
            if (['theme', 'highContrast', 'fontSize'].includes(event.detail.key)) {
                console.log(`Theme-utils: 应用自定义${event.detail.key}设置`);
                applyAllSettings();
            }
        }
    });
});

// 导出函数，使其可在其他文件中使用
window.themeUtils = {
    applyAllSettings,
    applyThemeSetting,
    applyContrastSetting,
    applyFontSizeSetting
}; 