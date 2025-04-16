// 主题切换功能
const themeToggle = document.getElementById('themeToggle');
const themeIcon = themeToggle.querySelector('i');

// 检查本地存储中的主题偏好
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    document.body.classList.add('night-mode');
    themeIcon.classList.remove('bi-moon-fill');
    themeIcon.classList.add('bi-sun-fill');
}

// 主题切换事件监听
themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('night-mode');
    
    if (document.body.classList.contains('night-mode')) {
        localStorage.setItem('theme', 'dark');
        themeIcon.classList.remove('bi-moon-fill');
        themeIcon.classList.add('bi-sun-fill');
    } else {
        localStorage.setItem('theme', 'light');
        themeIcon.classList.remove('bi-sun-fill');
        themeIcon.classList.add('bi-moon-fill');
    }
});

document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;
    const adminKey = document.getElementById('adminKey')?.value;
    const messageDiv = document.getElementById('message');
    
    // 验证管理员密钥（如果尝试注册为管理员）
    if (role === 'admin') {
        if (!adminKey || adminKey !== 'admin123') { // 简单示例，实际应使用更安全的方式
            messageDiv.textContent = '管理员密钥无效！';
            messageDiv.className = 'message error';
            messageDiv.style.display = 'block';
            
            // 添加消息淡入动画
            setTimeout(() => {
                messageDiv.style.opacity = '1';
                messageDiv.style.transform = 'translateY(0)';
            }, 10);
            return;
        }
    }
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password,
                role
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            messageDiv.textContent = `注册成功！角色: ${role === 'admin' ? '管理员' : '普通用户'}`;
            messageDiv.className = 'message success';
            document.getElementById('registerForm').reset();
            
            // 注册成功后延迟跳转到登录页面
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            messageDiv.textContent = data.detail || '注册失败，请重试';
            messageDiv.className = 'message error';
        }
    } catch (error) {
        messageDiv.textContent = '注册失败，请检查网络连接';
        messageDiv.className = 'message error';
    }
    
    messageDiv.style.display = 'block';
    
    // 添加消息淡入动画
    setTimeout(() => {
        messageDiv.style.opacity = '1';
        messageDiv.style.transform = 'translateY(0)';
    }, 10);
}); 