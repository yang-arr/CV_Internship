const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendButton = document.getElementById('sendButton');
const typingIndicator = document.getElementById('typingIndicator');
const voiceInputButton = document.getElementById('voiceInputButton');
const voiceOutputButton = document.getElementById('voiceOutputButton');
const voiceSettings = document.getElementById('voiceSettings');
const voiceSelect = document.getElementById('voiceSelect');
const rateRange = document.getElementById('rateRange');
const pitchRange = document.getElementById('pitchRange');
const rateValue = document.getElementById('rateValue');
const pitchValue = document.getElementById('pitchValue');
const testVoiceButton = document.getElementById('testVoiceButton');
const autoReadToggle = document.getElementById('autoReadToggle');
const voiceStopButton = document.getElementById('voiceStopButton');

// 历史会话相关元素
const toggleSidebarBtn = document.getElementById('toggleSidebarBtn');
const historySidebar = document.getElementById('historySidebar');
const historyList = document.getElementById('historyList');
const historySearchInput = document.getElementById('historySearchInput');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const newChatBtn = document.getElementById('newChatBtn');
const historyIcon = document.getElementById('historyIcon');
const newChatIcon = document.getElementById('newChatIcon');
const deleteHistoryModal = new bootstrap.Modal(document.getElementById('deleteHistoryModal'));
const clearAllHistoryModal = new bootstrap.Modal(document.getElementById('clearAllHistoryModal'));
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const confirmClearAllBtn = document.getElementById('confirmClearAllBtn');
const containerElement = document.querySelector('.container');

const brainWave = document.getElementById('brainWave');
const medicalLoader = document.getElementById('medicalLoader');
const thinkingState = document.getElementById('thinkingState');
const logoutBtn = document.getElementById('logoutBtn');

let lastQuestion = ''; // 存储最后一个问题，用于重试功能
let isListening = false; // 是否正在进行语音识别
let isSpeaking = false; // 是否正在朗读中
let recognition = null; // 语音识别对象
let synth = window.speechSynthesis; // 语音合成对象
let voices = []; // 可用的语音列表
let currentUtterance = null; // 当前正在播放的语音
let currentAudio = null; // 当前正在播放的服务器音频
let baseFontSize = 16; // 基础字体大小
let isModelThinking = false; // 模型是否在思考中
let currentHistoryId = null; // 当前活跃的会话ID
let historyToDelete = null; // 要删除的会话ID
let chatHistories = []; // 存储所有会话记录
let filteredHistories = []; // 过滤后的会话记录
let isSidebarExpanded = false; // 侧边栏是否展开，默认为收起状态

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', () => {
    // 应用主题设置
    applyThemeSettings();
    
    // 初始化语音设置
    initVoiceSettings();
    
    // 初始化聊天历史
    initChatHistory();
    
    // 检查Ollama服务是否可用
    checkOllamaService();
    
    // 添加一个系统消息，告诉用户AI助手已准备好
    // addSystemMessage('AI医疗助手已准备完成，您可以开始提问。');
    
    // 登出按钮事件处理
    logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        // 清除本地存储中的认证信息
        localStorage.removeItem('access_token');
        localStorage.removeItem('token_type');
        localStorage.removeItem('username');
        // 跳转到登录页面
        window.location.href = '/login';
    });
    
    // 绑定用户输入事件
    userInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 绑定发送按钮点击事件
    sendButton.addEventListener('click', () => {
        sendMessage();
    });
    
    // 初始化语音输入按钮事件
    voiceInputButton.addEventListener('click', toggleSpeechRecognition);
    
    // 初始化语音输出按钮事件
    voiceOutputButton.addEventListener('click', () => {
        voiceSettings.style.display = voiceSettings.style.display === 'block' ? 'none' : 'block';
    });
    
    // 停止朗读按钮
    voiceStopButton.addEventListener('click', stopSpeaking);
});

// 应用主题设置
function applyThemeSettings() {
    // 检查本地存储中的主题偏好
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('night-mode');
    }
    
    // 应用高对比度设置
    if (localStorage.getItem('highContrast') === 'true') {
        document.body.classList.add('high-contrast');
    }
    
    // 应用字体大小设置
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        baseFontSize = parseInt(savedFontSize);
        document.documentElement.style.setProperty('--font-size-base', `${baseFontSize}px`);
        document.body.style.fontSize = `${baseFontSize}px`;
    }
}

// 配置Marked.js选项
marked.setOptions({
    breaks: true,           // 支持回车换行
    gfm: true,              // 支持GitHub Flavored Markdown
    headerIds: false,       // 不自动添加header IDs
    mangle: false,          // 不修改@mentions
    sanitize: false,        // 不进行消毒处理(我们使用DOMPurify)
    smartLists: true,       // 使用更智能的列表行为
    smartypants: true,      // 使用智能标点符号
    xhtml: false,           // 不使用XHTML闭合标签
    highlight: function(code, lang) {
        // 添加语法高亮支持
        return code;
    }
});

// 主题切换功能
function initThemeToggle() {
    // 检查本地存储的主题偏好
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('night-mode');
        themeIcon.classList.remove('bi-moon-fill');
        themeIcon.classList.add('bi-sun-fill');
    }

    // 添加主题切换事件
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
}

// 登出按钮事件处理
logoutBtn.addEventListener('click', (e) => {
    e.preventDefault();
    // 清除本地存储中的认证信息
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('username');
    // 跳转到登录页面
    window.location.href = '/login';
});

// 辅助功能面板控制
function initAccessibilityControls() {
    // 显示/隐藏辅助功能面板
    accessibilityToggle.addEventListener('click', () => {
        if (accessibilityPanel.style.display === 'block') {
            accessibilityPanel.style.display = 'none';
        } else {
            accessibilityPanel.style.display = 'block';
        }
    });

    // 高对比度模式切换
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

    // 字体大小控制
    increaseFontBtn.addEventListener('click', () => {
        baseFontSize += 2;
        updateFontSize();
    });

    decreaseFontBtn.addEventListener('click', () => {
        if (baseFontSize > 14) {
            baseFontSize -= 2;
            updateFontSize();
        }
    });

    resetFontBtn.addEventListener('click', () => {
        baseFontSize = 16;
        updateFontSize();
        localStorage.removeItem('fontSize');
    });

    // 从本地存储读取字体大小
    const savedFontSize = localStorage.getItem('fontSize');
    if (savedFontSize) {
        baseFontSize = parseInt(savedFontSize);
        updateFontSize();
    }
}

// 更新字体大小
function updateFontSize() {
    document.documentElement.style.setProperty('--font-size-base', `${baseFontSize}px`);
    document.body.style.fontSize = `${baseFontSize}px`;
    localStorage.setItem('fontSize', baseFontSize.toString());
}

// 显示AI思考状态的脑电波效果
function showThinkingEffect(show) {
    isModelThinking = show;

    // 确保所有思考相关的元素都正确显示或隐藏
    if (show) {
        // 先确保所有元素可见
        thinkingState.classList.remove('hidden');

        // 找到最后一条用户消息，并在其后插入思考状态
        const userMessages = document.querySelectorAll('.user-message');
        if (userMessages.length > 0) {
            // 获取最近的用户消息
            const lastUserMessage = userMessages[userMessages.length - 1];

            // 将思考状态移动到用户消息之后
            if (lastUserMessage.nextSibling) {
                chatContainer.insertBefore(thinkingState, lastUserMessage.nextSibling);
            } else {
                chatContainer.appendChild(thinkingState);
            }
        } else {
            // 如果没有用户消息，将思考状态添加到最上方
            if (chatContainer.firstChild) {
                chatContainer.insertBefore(thinkingState, chatContainer.firstChild);
            } else {
                chatContainer.appendChild(thinkingState);
            }
        }

        thinkingState.style.display = 'flex';

        // 隐藏脑电波和医学加载器，专注于思考状态
        brainWave.style.display = 'none';
        medicalLoader.style.display = 'none';

        // 强制重排，确保CSS动画生效
        void thinkingState.offsetWidth;

        // 滚动以确保思考状态可见
        thinkingState.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    } else {
        // 先添加隐藏类（触发过渡效果）
        thinkingState.classList.add('hidden');

        // 延迟一点再隐藏其他元素，让过渡效果完成
        setTimeout(() => {
            thinkingState.style.display = 'none';
            brainWave.style.display = 'none';
            medicalLoader.style.display = 'none';
        }, 300);
    }
}

// 初始化语音设置
function initVoiceSettings() {
    // 检查浏览器是否支持语音识别
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = false;

        recognition.onstart = () => {
            isListening = true;
            voiceInputButton.classList.add('listening');
            addSystemMessage('正在聆听...');
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            addSystemMessage('语音识别结果：' + transcript);
            sendMessage();
        };

        recognition.onend = () => {
            isListening = false;
            voiceInputButton.classList.remove('listening');
        };

        recognition.onerror = (event) => {
            isListening = false;
            voiceInputButton.classList.remove('listening');
            addSystemMessage('语音识别错误：' + event.error);
        };

        voiceInputButton.addEventListener('click', toggleSpeechRecognition);
    } else {
        voiceInputButton.disabled = true;
        voiceInputButton.title = '您的浏览器不支持语音识别';
        addSystemMessage('您的浏览器不支持语音识别功能');
    }

    // 初始化语音合成
    if ('speechSynthesis' in window) {
        // 获取可用的语音
        function loadVoices() {
            voices = synth.getVoices();

            // 清空选择框
            voiceSelect.innerHTML = '';

            // 优先找到中文语音
            let defaultVoice = voices.find(voice => voice.lang.includes('zh'));
            let defaultIndex = defaultVoice ? voices.indexOf(defaultVoice) : 0;

            voices.forEach((voice, i) => {
                const option = document.createElement('option');
                option.textContent = `${voice.name} (${voice.lang})`;
                option.setAttribute('data-lang', voice.lang);
                option.setAttribute('data-name', voice.name);
                option.value = i;
                voiceSelect.appendChild(option);
            });

            if (defaultIndex > 0) {
                voiceSelect.selectedIndex = defaultIndex;
            }
        }

        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = loadVoices;
        }

        // 立即尝试加载一次
        loadVoices();

        // 设置语音输出按钮事件
        voiceOutputButton.addEventListener('click', () => {
            if (voiceSettings.style.display === 'block') {
                voiceSettings.style.display = 'none';
            } else {
                voiceSettings.style.display = 'block';
            }
        });

        // 更新语速值显示
        rateRange.addEventListener('input', () => {
            rateValue.textContent = rateRange.value;
        });

        // 更新音调值显示
        pitchRange.addEventListener('input', () => {
            pitchValue.textContent = pitchRange.value;
        });

        // 测试语音按钮
        testVoiceButton.addEventListener('click', () => {
            speakText('您好，这是一条测试语音，我是您的AI医疗助手。');
        });

        // 默认开启自动朗读
        autoReadToggle.checked = true;
    } else {
        voiceOutputButton.disabled = true;
        voiceOutputButton.title = '您的浏览器不支持语音合成';
        autoReadToggle.disabled = true;
        addSystemMessage('您的浏览器不支持语音合成功能');
    }
}

// 停止所有语音朗读
function stopSpeaking() {
    // 停止浏览器API朗读
    if (synth && synth.speaking) {
        synth.cancel();
    }

    // 停止服务器端音频播放
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }

    // 重置状态
    isSpeaking = false;
    currentUtterance = null;

    // 更新UI状态
    voiceOutputButton.classList.remove('speaking');
    voiceStopButton.classList.remove('active');
}

// 切换语音识别状态
function toggleSpeechRecognition() {
    // 如果开始语音输入，先停止任何正在播放的语音
    if (!isListening) {
        stopSpeaking();
    }

    if (isListening) {
        recognition.stop();
    } else {
        if (recognition) {
            recognition.start();
        } else {
            // 如果浏览器不支持语音识别，使用服务器端备用方案
            startServerSideRecording();
        }
    }
}

// 服务器端语音识别（录制音频并上传到服务器）
function startServerSideRecording() {
    // 检查是否支持MediaRecorder API
    if (!navigator.mediaDevices || !window.MediaRecorder) {
        addSystemMessage('您的浏览器不支持音频录制功能，请升级或更换浏览器。');
        return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            isListening = true;
            voiceInputButton.classList.add('listening');
            addSystemMessage('正在录音...(请说完后点击麦克风按钮停止)');

            // 创建媒体录制器
            const mediaRecorder = new MediaRecorder(stream);
            let audioChunks = [];

            // 保存录制的音频块
            mediaRecorder.addEventListener('dataavailable', event => {
                audioChunks.push(event.data);
            });

            // 录制完成后处理
            mediaRecorder.addEventListener('stop', () => {
                // 停止所有音轨
                stream.getTracks().forEach(track => track.stop());

                // 创建音频 Blob
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });

                // 创建FormData对象并添加音频文件
                const formData = new FormData();
                formData.append('audio_file', audioBlob, 'recording.wav');

                // 显示正在处理信息
                addSystemMessage('正在处理您的语音...');

                // 发送到服务器进行处理
                fetch('/api/medical/speech-to-text', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.text) {
                        // 显示识别结果
                        userInput.value = data.text;
                        addSystemMessage('语音识别结果：' + data.text);
                        // 自动发送识别的文本
                        sendMessage();
                    } else if (data.error) {
                        addSystemMessage('语音识别错误：' + data.error);
                    }
                })
                .catch(error => {
                    console.error('语音识别请求错误:', error);
                    addSystemMessage('语音识别失败：' + error.message);
                })
                .finally(() => {
                    isListening = false;
                    voiceInputButton.classList.remove('listening');
                });
            });

            // 开始录音
            mediaRecorder.start();

            // 再次点击麦克风按钮停止录音
            voiceInputButton.onclick = () => {
                if (isListening && mediaRecorder.state === 'recording') {
                    mediaRecorder.stop();
                    // 恢复原始点击事件
                    voiceInputButton.onclick = toggleSpeechRecognition;
                }
            };
        })
        .catch(error => {
            console.error('获取麦克风权限失败:', error);
            addSystemMessage('无法访问麦克风：' + error.message);
            isListening = false;
        });
}

// 文字转语音（使用服务器端API作为备用）
function speakText(text) {
    // 如果已经在朗读，先停止
    stopSpeaking();

    // 设置状态为正在朗读
    isSpeaking = true;
    voiceStopButton.classList.add('active');

    // 如果浏览器支持语音合成API，则使用浏览器API
    if (synth && window.SpeechSynthesisUtterance) {
        // 创建语音对象
        const utterance = new SpeechSynthesisUtterance(text);

        // 设置语音参数
        if (voices.length > 0) {
            utterance.voice = voices[voiceSelect.value];
        }
        utterance.rate = parseFloat(rateRange.value);
        utterance.pitch = parseFloat(pitchRange.value);
        utterance.lang = 'zh-CN';

        // 开始播放
        currentUtterance = utterance;
        synth.speak(utterance);

        // 添加事件
        utterance.onstart = () => {
            voiceOutputButton.classList.add('speaking');
        };

        utterance.onend = () => {
            voiceOutputButton.classList.remove('speaking');
            currentUtterance = null;
            isSpeaking = false;
            voiceStopButton.classList.remove('active');
        };

        utterance.onerror = (event) => {
            console.error('语音合成错误:', event);
            voiceOutputButton.classList.remove('speaking');
            currentUtterance = null;
            isSpeaking = false;
            voiceStopButton.classList.remove('active');

            // 如果浏览器API失败，尝试使用服务器API
            useServerTTS(text);
        };
    } else {
        // 浏览器不支持语音合成API，使用服务器端TTS
        useServerTTS(text);
    }
}

// 使用服务器端文本转语音API
function useServerTTS(text) {
    voiceOutputButton.classList.add('speaking');
    voiceStopButton.classList.add('active');
    isSpeaking = true;

    // 如果文本太长，分段处理
    if (text.length > 500) {
        const segments = splitTextIntoSegments(text);
        playSegmentsSequentially(segments, 0);
    } else {
        playServerTTS(text)
            .finally(() => {
                voiceOutputButton.classList.remove('speaking');
                voiceStopButton.classList.remove('active');
                isSpeaking = false;
            });
    }
}

// 将长文本分段
function splitTextIntoSegments(text, maxLength = 500) {
    const segments = [];
    let currentIndex = 0;

    while (currentIndex < text.length) {
        // 找到适合的分段点（句号、问号、感叹号或者到达最大长度）
        let endIndex = Math.min(currentIndex + maxLength, text.length);

        if (endIndex < text.length) {
            // 尝试在句子结束处分段
            const punctuationIndex = Math.max(
                text.lastIndexOf('。', endIndex),
                text.lastIndexOf('？', endIndex),
                text.lastIndexOf('！', endIndex),
                text.lastIndexOf('.', endIndex),
                text.lastIndexOf('?', endIndex),
                text.lastIndexOf('!', endIndex)
            );

            if (punctuationIndex > currentIndex && punctuationIndex < endIndex) {
                endIndex = punctuationIndex + 1;
            }
        }

        segments.push(text.substring(currentIndex, endIndex));
        currentIndex = endIndex;
    }

    return segments;
}

// 顺序播放文本段
function playSegmentsSequentially(segments, index) {
    if (index >= segments.length) {
        voiceOutputButton.classList.remove('speaking');
        voiceStopButton.classList.remove('active');
        isSpeaking = false;
        return;
    }

    // 如果已经停止朗读，则中断播放序列
    if (!isSpeaking) {
        return;
    }

    playServerTTS(segments[index])
        .then(() => {
            // 播放下一段（如果仍处于朗读状态）
            if (isSpeaking) {
                playSegmentsSequentially(segments, index + 1);
            }
        })
        .catch(error => {
            console.error('播放语音段落错误:', error);
            voiceOutputButton.classList.remove('speaking');
            voiceStopButton.classList.remove('active');
            isSpeaking = false;
        });
}

// 调用服务器端TTS API播放文本
function playServerTTS(text) {
    return new Promise((resolve, reject) => {
        fetch('/api/medical/text-to-speech', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                lang: 'zh',
                slow: false
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('TTS服务响应错误');
            }
            return response.blob();
        })
        .then(blob => {
            // 创建音频元素播放
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);

            // 保存当前正在播放的音频对象
            currentAudio = audio;

            audio.onended = () => {
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
                resolve();
            };

            audio.onerror = (error) => {
                URL.revokeObjectURL(audioUrl);
                currentAudio = null;
                reject(error);
            };

            audio.play()
                .catch(error => {
                    console.error('播放音频失败:', error);
                    URL.revokeObjectURL(audioUrl);
                    currentAudio = null;
                    reject(error);
                });
        })
        .catch(error => {
            console.error('TTS请求错误:', error);
            reject(error);
        });
    });
}

// 添加系统消息
function addSystemMessage(text) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.innerHTML = text; // 使用innerHTML以支持包含HTML的错误消息
    
    // 直接添加到聊天容器
    chatContainer.appendChild(messageDiv);
    
    // 确保滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 处理播放按钮点击
function handlePlayButtonClick(button, text) {
    event.stopPropagation();

    // 更新所有播放按钮
    document.querySelectorAll('.play-button').forEach(btn => {
        btn.className = 'bi bi-play-fill play-button';
    });

    // 设置当前按钮为暂停图标
    button.className = 'bi bi-pause-fill play-button';

    // 播放文本
    speakText(text);

    // 监听状态变化
    const checkInterval = setInterval(() => {
        if (!isSpeaking) {
            button.className = 'bi bi-play-fill play-button';
            clearInterval(checkInterval);
        }
    }, 500);
}

// 解析并渲染思维链
function parseThinkingChain(text) {
    // 检查是否已经包含思维链HTML结构
    if (text.includes('<div class="thinking-container">') || text.includes('<div class=\'thinking-container\'>')) {
        return { renderedText: text, hasThinkingChain: true };
    }

    // 检查是否包含思考步骤的HTML结构，但没有完整的思考容器
    if (text.includes('<div class="thinking-step">') || text.includes('<div class=\'thinking-step\'>')) {
        // 提取所有的思考步骤
        const stepRegex = /<div class=["']thinking-step["']>([\s\S]*?)<\/div>/g;
        const steps = [];
        let match;
        while ((match = stepRegex.exec(text)) !== null) {
            steps.push(match[1].trim());
        }

        if (steps.length > 0) {
            // 构建完整的思考容器HTML
            let thinkingHtml = '<div class="thinking-container">\n<div class="thinking-badge">思考过程</div>\n';
            steps.forEach(step => {
                thinkingHtml += `<div class="thinking-step">${step}</div>\n`;
            });
            thinkingHtml += '</div>';

            // 从原文中删除思考步骤部分
            let contentText = text.replace(stepRegex, '');

            // 返回清理后的内容和思考过程HTML
            return {
                renderedText: contentText + '\n\n' + thinkingHtml,
                hasThinkingChain: true
            };
        }
    }

    // 检查是否包含思维链标记
    if (!text.includes("<think>") && !text.includes("</think>")) {
        return { renderedText: text, hasThinkingChain: false };
    }

    let hasThinkingChain = false;
    let renderedText = text;

    // 替换思维链部分
    renderedText = renderedText.replace(/<think>([\s\S]*?)<\/think>/g, (match, content) => {
        hasThinkingChain = true;

        // 将思维链内容分成步骤 - 支持数字序号、星号和短横线的列表标记
        const steps = content.split(/\n(?=\d+\.|\*|\-)/g).filter(step => step.trim());

        let stepsHtml = '';
        steps.forEach(step => {
            // 转义HTML标签，防止XSS攻击
            const safeStep = step.trim()
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');

            stepsHtml += `<div class="thinking-step">${safeStep}</div>`;
        });

        return `
        <div class="thinking-container">
            <div class="thinking-badge">思考过程</div>
            ${stepsHtml}
        </div>`;
    });

    return { renderedText, hasThinkingChain };
}

// 添加消息
function addMessage(text, type = 'ai') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    if (type === 'user') {
        // 用户消息直接显示文本
        messageDiv.textContent = text;
    } else if (type === 'ai') {
        try {
            // 尝试从AI响应中检测并生成思考过程
            text = detectAndGenerateThinking(text);

            // 检查是否包含不完整的HTML标签
            text = fixIncompleteHtml(text);

            // AI消息需要处理思维链和渲染Markdown
            // 首先提取思考过程部分
            let thinkingHtml = '';
            let contentHtml = text;

            // 尝试提取思考过程
            const thinkingPattern = extractThinkingProcess(text);
            if (thinkingPattern) {
                if (thinkingPattern.thinkingHtml) {
                    // 如果有HTML格式的思考过程
                    thinkingHtml = thinkingPattern.thinkingHtml;
                    contentHtml = thinkingPattern.contentHtml;
                } else if (thinkingPattern.thinkingSteps) {
                    // 如果只有思考步骤
                    contentHtml = thinkingPattern.contentHtml;
                    // thinkingHtml将在下面创建思考容器时使用
                    thinkingHtml = thinkingPattern;
                }
            }

            // 使用marked渲染剩余的Markdown内容
            const contentMarkdown = marked.parse(contentHtml.trim());

            // 设置主要内容（Markdown部分）
            messageDiv.innerHTML = DOMPurify.sanitize(contentMarkdown, {
                ALLOWED_TAGS: [
                    'div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'ul', 'ol', 'li', 'a', 'strong', 'em', 'code', 'pre',
                    'blockquote', 'table', 'thead', 'tbody', 'tr', 'td', 'th',
                    'br', 'span', 'img', 'b', 'i', 'u', 'sup', 'sub', 'hr',
                    'section', 'mark', 'del', 'ins', 'dl', 'dt', 'dd'
                ],
                ALLOWED_ATTR: ['href', 'src', 'alt', 'class', 'id', 'style', 'data-*', 'title', 'target'],
                ADD_ATTR: ['class', 'target'],
                ADD_CLASS: {
                    'pre': ['code-block'],
                    'code': ['language-*']
                },
                FORBID_TAGS: ['style', 'script'],
                FORBID_ATTR: ['onerror', 'onload', 'onclick']
            });

            // 如果有思考过程，手动创建思考过程元素
            if (thinkingHtml) {
                // 创建思考容器
                const thinkingContainer = document.createElement('div');
                thinkingContainer.className = 'thinking-container';

                // 创建思考徽章
                const thinkingBadge = document.createElement('div');
                thinkingBadge.className = 'thinking-badge';
                thinkingBadge.textContent = '思考过程';
                thinkingContainer.appendChild(thinkingBadge);

                // 解析步骤
                const thinkingSteps = extractThinkingSteps(thinkingHtml);

                // 如果没有提取到步骤但有"思考过程"标记，尝试从原始响应中提取
                if (thinkingSteps.length === 0 && text.includes('思考过程')) {
                    const thinkingPart = text.substring(text.indexOf('思考过程')).trim();
                    const processedSteps = structureThinkingProcess(thinkingPart);

                    if (processedSteps.length > 0) {
                        processedSteps.forEach(step => {
                            const stepElement = document.createElement('div');
                            stepElement.className = 'thinking-step';
                            stepElement.textContent = step;
                            thinkingContainer.appendChild(stepElement);
                        });
                    } else {
                        // 应急处理：如果仍然没有提取到有效步骤，创建一些基本的思考步骤
                        // 从主内容分析生成思考步骤
                        const sentences = contentHtml.split(/。|\.|\?|？|!|！/)
                            .filter(s => s.trim().length > 10) // 只使用有意义的句子
                            .slice(0, 3);  // 最多取前3句

                        if (sentences.length > 0) {
                            // 添加标准的思考步骤
                            addStandardThinkingStep(thinkingContainer, "1. 首先理解用户提出的问题，分析其核心需求。");

                            // 根据内容添加中间步骤
                            sentences.forEach((sentence, index) => {
                                addStandardThinkingStep(thinkingContainer,
                                    `${index + 2}. 分析关键信息"${sentence.trim().substring(0, 30)}..."，整理相关医学知识。`);
                            });

                            // 添加总结步骤
                            addStandardThinkingStep(thinkingContainer,
                                `${sentences.length + 2}. 整合上述信息，形成详细的医学解答。`);
                        } else {
                            // 如果连句子都没有提取到，添加基础思考步骤
                            addStandardThinkingStep(thinkingContainer, "1. 理解问题，确定回答方向。");
                            addStandardThinkingStep(thinkingContainer, "2. 收集医学知识，整理相关信息。");
                            addStandardThinkingStep(thinkingContainer, "3. 组织医学知识点，确保准确性。");
                            addStandardThinkingStep(thinkingContainer, "4. 形成系统性回答，注重医学专业性。");
                        }
                    }
                } else {
                    // 使用提取的步骤
                    thinkingSteps.forEach(step => {
                        const stepElement = document.createElement('div');
                        stepElement.className = 'thinking-step';
                        stepElement.textContent = step;
                        thinkingContainer.appendChild(stepElement);
                    });
                }

                // 先将思考过程插入到消息中，确保思考过程显示在正文前面
                if (thinkingContainer.querySelectorAll('.thinking-step').length > 0) {
                    // 获取当前消息的内容
                    const currentContent = messageDiv.innerHTML;
                    // 清空当前消息
                    messageDiv.innerHTML = '';
                    // 先插入思考容器
                    messageDiv.appendChild(thinkingContainer);
                    // 创建新元素存放原始内容
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'ai-content';
                    contentDiv.innerHTML = currentContent;
                    // 将原始内容添加到思考过程之后
                    messageDiv.appendChild(contentDiv);
                }
            }

            // 为AI消息添加播放按钮
            const playButton = document.createElement('i');
            playButton.className = 'bi bi-play-fill play-button';

            // 移除思考过程的HTML，以便语音朗读不包含思考过程
            let textToSpeak = text;
            if (text.includes('<div class="thinking-container">')) {
                textToSpeak = text.replace(/<div class="thinking-container">[\s\S]*?<\/div><\/div>/g, '');
            } else if (text.includes('<think>')) {
                textToSpeak = text.replace(/<think>[\s\S]*?<\/think>/g, '');
            }

            // 去掉HTML标签，只保留纯文本用于朗读
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = textToSpeak;
            textToSpeak = tempDiv.textContent || tempDiv.innerText || '';

            playButton.setAttribute('data-text', textToSpeak);

            // 为播放按钮添加点击事件
            playButton.addEventListener('click', function(event) {
                const textToSpeak = this.getAttribute('data-text');
                handlePlayButtonClick(this, textToSpeak);
            });

            messageDiv.appendChild(playButton);

            // 如果开启了自动朗读，则自动播放（排除思维链部分）
            if (autoReadToggle.checked) {
                setTimeout(() => speakText(textToSpeak), 500);
            }
        } catch (error) {
            console.error('消息渲染错误:', error);
            messageDiv.textContent = text; // 出错时回退到原始文本
        }
    } else if (type === 'error') {
        messageDiv.textContent = text;

        const retryButton = document.createElement('button');
        retryButton.className = 'retry-button';
        retryButton.textContent = '重试';
        retryButton.onclick = () => {
            if (lastQuestion) {
                sendMessage(lastQuestion);
            }
        };
        messageDiv.appendChild(retryButton);
    }

    // 将消息添加到聊天容器
    chatContainer.appendChild(messageDiv);
    
    // 确保滚动到最新消息
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    return messageDiv;
}

// 修改发送消息函数，添加历史记录功能
async function sendMessage(text = null) {
    // 如果没有传入文本，使用输入框中的文本
    text = text || userInput.value.trim();
    
    // 如果文本为空，则不发送
    if (!text) {
        return;
    }
    
    // 保存最后一个问题，用于重试
    lastQuestion = text;
    
    // 清空输入框
    userInput.value = '';
    
    // 如果有正在播放的语音，停止它
    stopSpeaking();
    
    // 添加用户消息到聊天窗口
    addMessage(text, 'user');
    
    // 显示AI思考状态
    showThinkingEffect(true);
    
    try {
        // 获取访问令牌
        const token = localStorage.getItem('access_token');
        
        // 如果没有令牌，跳转到登录页面
        if (!token) {
            addSystemMessage('您的登录已过期，请重新登录');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            return;
        }
        
        // 准备请求数据
        const requestData = {
            text: text
        };
        
        // 如果有当前会话ID，添加到请求数据中
        if (currentHistoryId) {
            requestData.chat_history_id = currentHistoryId;
        }
        
        // 发送请求到后端
        const response = await fetch('/api/medical/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestData),
            // 添加重定向处理选项
            redirect: 'manual'
        });
        
        // 处理令牌过期或验证失败的情况
        if (response.status === 401 || response.status === 403 || response.type === 'opaqueredirect') {
            // 隐藏AI思考状态
            showThinkingEffect(false);
            
            // 显示错误消息
            addSystemMessage('您的登录会话已过期，请重新登录');
            
            // 清除本地存储中的认证信息
            localStorage.removeItem('access_token');
            localStorage.removeItem('token_type');
            localStorage.removeItem('username');
            
            // 延迟跳转到登录页面，让用户有时间看到消息
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            
            return;
        }
        
        if (!response.ok) {
            throw new Error(`服务器返回错误: ${response.status}`);
        }
        
        // 解析JSON响应
        const data = await response.json();
        
        // 隐藏AI思考状态
        showThinkingEffect(false);
        
        // 添加AI回复到聊天窗口
        addMessage(data.response, 'ai');
        
        // 如果开启了自动朗读，则朗读AI回复
        if (autoReadToggle.checked) {
            speakText(data.response);
        }
        
        // 如果获取了新的会话ID，更新当前会话ID
        if (data.chat_history_id && !currentHistoryId) {
            currentHistoryId = data.chat_history_id;
            loadChatHistories(); // 重新加载历史记录以显示新会话
        }
        
    } catch (error) {
        console.error('处理请求时出错:', error);
        
        // 隐藏AI思考状态
        showThinkingEffect(false);
        
        // 检查是否是网络错误或CORS问题
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            addSystemMessage('网络连接错误，请检查您的网络连接');
        } else if (error.message.includes('token')) {
            // 令牌相关错误
            addSystemMessage('您的登录已过期，请重新登录');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            // 添加重试按钮的错误消息
            addSystemMessage(`请求发生错误: ${error.message} <button class="retry-button" onclick="sendMessage('${escapeHtml(lastQuestion)}')">重试</button>`);
        }
    }
    
    // 滚动到底部
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 检查Ollama服务状态
async function checkOllamaService() {
    const MODEL_NAME = "hf.co/TimeLoad/deepseek-r1-medical:latest";
    try {
        const response = await fetch('http://localhost:11434/api/tags');
        if (!response.ok) {
            addMessage('警告：Ollama服务可能未启动，请确保服务正在运行。', 'error');
            return;
        }

        const data = await response.json();
        const models = data.models || [];
        if (!models.some(model => model.name === MODEL_NAME)) {
            addMessage(`警告：未找到所需的模型 "${MODEL_NAME}"，请确保已经下载该模型。\n可以使用命令：ollama pull "${MODEL_NAME}" 来下载模型。`, 'error');
        }
    } catch (error) {
        addMessage('警告：无法连接到Ollama服务，请确保服务已启动。', 'error');
    }
}

// 页面加载时初始化
window.addEventListener('load', () => {
    checkOllamaService();
    initVoiceSettings();
    initThemeToggle();
    initAccessibilityControls();

    // 添加停止朗读按钮事件
    voiceStopButton.addEventListener('click', stopSpeaking);

    // 初始化欢迎消息的播放按钮
    document.querySelectorAll('.play-button').forEach(button => {
        button.addEventListener('click', function(event) {
            const textToSpeak = this.getAttribute('data-text') || this.parentElement.textContent.trim();
            handlePlayButtonClick(this, textToSpeak);
        });
    });

    // 添加键盘快捷键支持
    document.addEventListener('keydown', (e) => {
        // Ctrl+Enter: 发送消息
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }

        // Ctrl+Shift+M: 语音输入
        if (e.ctrlKey && e.shiftKey && e.key === 'M') {
            e.preventDefault();
            toggleSpeechRecognition();
        }

        // Ctrl+Shift+S: 停止朗读
        if (e.ctrlKey && e.shiftKey && e.key === 'S') {
            e.preventDefault();
            if (isSpeaking) {
                stopSpeaking();
            }
        }

        // Ctrl+Shift+D: 切换夜间模式
        if (e.ctrlKey && e.shiftKey && e.key === 'D') {
            e.preventDefault();
            themeToggle.click();
        }
    });

    // 初始化历史会话功能
    initChatHistory();
});

sendButton.addEventListener('click', () => sendMessage());
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// 修复不完整的HTML代码
function fixIncompleteHtml(text) {
    // 检查是否包含不完整的</div>标签
    if (text.includes('</div>') && !text.includes('<div')) {
        text = text.replace('</div>', '');
    }

    // 检查是否有思考过程标记但没有内容
    if (text.includes('思考过程') && !text.includes('<div class="thinking-container">')) {
        // 提取思考过程前的内容
        const contentBeforeThinking = text.substring(0, text.indexOf('思考过程')).trim();

        // 提取"思考过程"之后的内容
        let thinkingContent = text.substring(text.indexOf('思考过程') + 4).trim();

        // 如果内容为空或只有"</div>"，则根据上下文生成思考步骤
        if (!thinkingContent || thinkingContent === '</div>') {
            // 从主内容中提取关键内容生成思考步骤
            const sentences = contentBeforeThinking.split(/。|\.|\?|？|!|！/)
                .filter(s => s.trim().length > 5) // 只使用有意义的句子
                .slice(0, 3);  // 最多取前3句

            if (sentences.length > 0) {
                // 构建简单的思考步骤
                let thinkingHtml = '<div class="thinking-container"><div class="thinking-badge">思考过程</div>';

                // 第一步：理解问题
                thinkingHtml += `<div class="thinking-step">1. 首先理解用户提出的问题，分析其核心需求。</div>`;

                // 第二步：基于句子分析
                sentences.forEach((sentence, index) => {
                    thinkingHtml += `<div class="thinking-step">${index + 2}. ${sentence.trim()}，这一点很重要。</div>`;
                });

                // 最后一步：总结
                thinkingHtml += `<div class="thinking-step">${sentences.length + 2}. 整合上述信息，得出完整的回答。</div>`;

                thinkingHtml += '</div>';

                // 替换原文中的思考过程部分
                text = contentBeforeThinking + '\n\n' + thinkingHtml;
            }
        } else {
            // 思考过程有内容，但不是标准格式，进行标准化处理
            // 移除可能的</div>标签
            thinkingContent = thinkingContent.replace('</div>', '').trim();

            // 将思考内容转换为结构化格式
            const thinkingSteps = structureThinkingProcess(thinkingContent);

            if (thinkingSteps.length > 0) {
                let thinkingHtml = '<div class="thinking-container"><div class="thinking-badge">思考过程</div>';
                thinkingSteps.forEach(step => {
                    thinkingHtml += `<div class="thinking-step">${step}</div>`;
                });
                thinkingHtml += '</div>';

                // 替换原文中的思考过程部分
                text = contentBeforeThinking + '\n\n' + thinkingHtml;
            }
        }
    }

    // 处理图中显示的特殊情况："</div>"直接显示在文本中
    if (text.includes('思考过程') && text.includes('</div>')) {
        // 尝试提取可能包含思考步骤的部分
        const thinkingSection = text.substring(text.indexOf('思考过程'));
        // 创建适当的HTML结构
        const steps = thinkingSection
            .replace('</div>', '')
            .replace('思考过程', '')
            .split('\n')
            .filter(line => line.trim().length > 0)
            .map(line => line.trim());

        if (steps.length > 0) {
            // 构建正确的思考过程HTML
            let thinkingHtml = '<div class="thinking-container"><div class="thinking-badge">思考过程</div>';
            steps.forEach((step, index) => {
                thinkingHtml += `<div class="thinking-step">${(index + 1)}. ${step}</div>`;
            });
            thinkingHtml += '</div>';

            // 从原文中移除思考部分
            const contentText = text.substring(0, text.indexOf('思考过程')).trim();

            // 返回修复后的文本
            return contentText + '\n\n' + thinkingHtml;
        }
    }

    // 修复thinking-container的闭合问题
    if (text.includes('<div class="thinking-container">') &&
        !text.includes('</div></div>') &&
        text.match(/<div class="thinking-container">/g).length !== text.match(/<\/div>/g).length) {
        // 如果有thinking-container但缺少闭合标签
        text = text.replace(/<div class="thinking-container">[\s\S]*?$/, function(match) {
            // 计算需要添加的闭合标签数量
            const openDivs = (match.match(/<div/g) || []).length;
            const closeDivs = (match.match(/<\/div>/g) || []).length;
            const missingCloseDivs = openDivs - closeDivs;

            // 添加缺少的闭合标签
            if (missingCloseDivs > 0) {
                return match + '</div>'.repeat(missingCloseDivs);
            }
            return match;
        });
    }

    return text;
}

// 提取思考过程，处理各种格式情况
function extractThinkingProcess(text) {
    // 特殊情况：有"思考过程"字样但没有内容结构化的情况
    if (text.includes('思考过程') && !text.includes('<div class="thinking-container">') && !text.includes('<div class="thinking-step">')) {
        const contentPart = text.substring(0, text.indexOf('思考过程')).trim();
        const thinkingPart = text.substring(text.indexOf('思考过程')).trim();

        // 分析思考过程部分
        const lines = thinkingPart.split('\n')
            .filter(line => line.trim() && line.trim() !== '思考过程' && line.trim() !== '</div>')
            .map(line => line.trim());

        if (lines.length > 0) {
            return {
                thinkingSteps: lines,
                contentHtml: contentPart
            };
        } else {
            // 如果没有找到有效的步骤行，则尝试用句号分割
            const sentences = thinkingPart.replace('思考过程', '').replace('</div>', '')
                .split(/。|\./)
                .filter(sent => sent.trim())
                .map(sent => sent.trim());

            if (sentences.length > 0) {
                return {
                    thinkingSteps: sentences,
                    contentHtml: contentPart
                };
            }
        }
    }

    // 检查是否是HTML格式的思考过程
    if (text.includes('<div class="thinking-container">')) {
        // 尝试匹配完整的思考容器
        const thinkingMatch = text.match(/<div class="thinking-container">[\s\S]*?<\/div><\/div>/);
        if (thinkingMatch) {
            return {
                thinkingHtml: thinkingMatch[0],
                contentHtml: text.replace(thinkingMatch[0], '')
            };
        }

        // 尝试匹配不完整的思考容器（可能缺少闭合标签）
        const incompleteMatch = text.match(/<div class="thinking-container">[\s\S]*?(<\/div>)?$/);
        if (incompleteMatch) {
            // 提取思考步骤
            const stepsMatch = text.match(/<div class="thinking-step">[\s\S]*?<\/div>/g);
            if (stepsMatch && stepsMatch.length > 0) {
                const steps = stepsMatch.map(step => {
                    return step.replace(/<div class="thinking-step">([\s\S]*?)<\/div>/, '$1').trim();
                });

                // 从原文中移除思考容器部分
                let contentText = text;
                contentText = contentText.replace(/<div class="thinking-container">[\s\S]*/, '');

                return {
                    thinkingSteps: steps,
                    contentHtml: contentText.trim()
                };
            } else {
                // 如果没有找到思考步骤，尝试从文本中提取
                const containerContent = incompleteMatch[0].replace('<div class="thinking-container">', '').replace('<div class="thinking-badge">思考过程</div>', '').replace('</div>', '');
                const lines = containerContent.split('\n')
                    .filter(line => line.trim())
                    .map(line => line.trim());

                if (lines.length > 0) {
                    let contentText = text;
                    contentText = contentText.replace(/<div class="thinking-container">[\s\S]*/, '');

                    return {
                        thinkingSteps: lines,
                        contentHtml: contentText.trim()
                    };
                }
            }
        }
    }

    // 检查是否只包含思考步骤标签
    if (text.includes('<div class="thinking-step">')) {
        const stepMatches = text.match(/<div class="thinking-step">[\s\S]*?<\/div>/g);
        if (stepMatches) {
            const steps = stepMatches.map(step => {
                return step.replace(/<div class="thinking-step">([\s\S]*?)<\/div>/, '$1').trim();
            });

            // 从原文中移除思考步骤
            let contentText = text;
            stepMatches.forEach(match => {
                contentText = contentText.replace(match, '');
            });

            return {
                thinkingSteps: steps,
                contentHtml: contentText.trim()
            };
        }
    }

    // 检查<think>标签格式
    if (text.includes('<think>') && text.includes('</think>')) {
        const thinkMatch = text.match(/<think>([\s\S]*?)<\/think>/);
        if (thinkMatch) {
            const thinkContent = thinkMatch[1];
            const steps = thinkContent.split(/\n(?=\d+\.|\*|\-)/g)
                .filter(step => step.trim())
                .map(step => step.trim());

            return {
                thinkingSteps: steps,
                contentHtml: text.replace(thinkMatch[0], '')
            };
        }
    }

    return null;
}

// 将纯文本思考过程转换为结构化的步骤
function structureThinkingProcess(text) {
    if (!text || typeof text !== 'string') return [];

    // 移除常见的前缀
    text = text.replace(/^思考过程[:：]?\s*/i, '');

    // 尝试各种分割方式
    let steps = [];

    // 方法1: 使用数字编号分割 (例如: "1. 步骤一")
    const numberedSteps = text.match(/\d+\.\s+[^\n]+/g);
    if (numberedSteps && numberedSteps.length > 0) {
        return numberedSteps.map(step => step.trim());
    }

    // 方法2: 使用换行符分割
    steps = text.split('\n')
        .filter(line => line.trim() && line.trim() !== '</div>')
        .map((line, index) => {
            // 如果行没有数字前缀，添加一个
            if (!/^\d+\./.test(line)) {
                return `${index + 1}. ${line.trim()}`;
            }
            return line.trim();
        });

    if (steps.length > 0) {
        return steps;
    }

    // 方法3: 使用句号分割
    steps = text.split(/。|\./)
        .filter(sentence => sentence.trim())
        .map((sentence, index) => `${index + 1}. ${sentence.trim()}`);

    if (steps.length > 0) {
        return steps;
    }

    // 如果以上都失败，将整个文本作为一个步骤返回
    if (text.trim()) {
        return [`1. ${text.trim()}`];
    }

    return [];
}

// 修改extractThinkingSteps函数，使用structureThinkingProcess处理纯文本
function extractThinkingSteps(thinkingText) {
    // 如果已经有步骤数组
    if (Array.isArray(thinkingText)) {
        return thinkingText;
    }

    // 如果是对象且包含thinkingSteps
    if (thinkingText && thinkingText.thinkingSteps) {
        return thinkingText.thinkingSteps;
    }

    // 如果是HTML字符串，尝试提取步骤
    if (typeof thinkingText === 'string') {
        // 检查是否包含thinking-step标签
        const stepMatches = thinkingText.match(/<div class="thinking-step">([\s\S]*?)<\/div>/g);
        if (stepMatches) {
            return stepMatches.map(step => {
                return step.replace(/<div class="thinking-step">([\s\S]*?)<\/div>/, '$1').trim();
            });
        }

        // 如果是纯文本，使用structureThinkingProcess函数处理
        return structureThinkingProcess(thinkingText);
    }

    // 默认返回空数组
    return [];
}

// 尝试从AI响应中检测并生成思考过程
function detectAndGenerateThinking(text) {
    // 如果已经包含思考过程结构，则不处理
    if (text.includes('<div class="thinking-container">') ||
        text.includes('<div class="thinking-step">') ||
        text.includes('<think>')) {
        return text;
    }

    // 检查响应中是否有明确的思考过程标记
    if (text.includes('思考过程')) {
        return text; // 已经在fixIncompleteHtml中处理了
    }

    // 尝试检测可能包含思考过程的部分
    const thinkingIndicators = [
        '我的推理过程', '分析步骤', '思考如下', '我的分析', '推理过程',
        '解题思路', '解决思路', '思路如下', '解答过程', '思维过程',
        '推导过程', '我是这样思考的', '考虑因素'
    ];

    for (const indicator of thinkingIndicators) {
        if (text.includes(indicator)) {
            // 提取思考内容
            const parts = text.split(indicator);
            if (parts.length >= 2) {
                // 提取思考内容的部分
                let thinkingPart = parts[1].trim();
                // 限制提取的范围，避免提取太多
                if (thinkingPart.length > 500) {
                    thinkingPart = thinkingPart.substring(0, 500) + '...';
                }

                // 组织成思考步骤
                const steps = structureThinkingProcess(thinkingPart);

                if (steps.length > 0) {
                    // 构建思考过程HTML
                    let thinkingHtml = '<div class="thinking-container"><div class="thinking-badge">思考过程</div>';
                    steps.forEach(step => {
                        thinkingHtml += `<div class="thinking-step">${step}</div>`;
                    });
                    thinkingHtml += '</div>';

                    // 替换原始内容，并添加思考过程HTML
                    const contentBeforeIndicator = parts[0].trim();

                    return contentBeforeIndicator + '\n\n' + thinkingHtml;
                }
            }
        }
    }

    return text;
}

// 添加标准的思考步骤元素
function addStandardThinkingStep(container, text) {
    const stepElement = document.createElement('div');
    stepElement.className = 'thinking-step';
    stepElement.textContent = text;
    container.appendChild(stepElement);
}

// 初始化历史会话功能
function initChatHistory() {
    // 切换侧边栏展开/收起状态
    toggleSidebarBtn.addEventListener('click', toggleSidebar);
    historyIcon.addEventListener('click', expandSidebar);
    
    // 新建会话
    newChatBtn.addEventListener('click', startNewChat);
    newChatIcon.addEventListener('click', startNewChat);
    
    // 搜索历史会话
    historySearchInput.addEventListener('input', searchHistories);
    
    // 清空所有历史
    clearHistoryBtn.addEventListener('click', () => {
        clearAllHistoryModal.show();
    });
    
    // 确认删除单个会话
    confirmDeleteBtn.addEventListener('click', () => {
        if (historyToDelete) {
            deleteChatHistory(historyToDelete);
        }
        deleteHistoryModal.hide();
    });
    
    // 确认清空所有会话
    confirmClearAllBtn.addEventListener('click', clearAllChatHistories);
    
    // 添加点击页面其他区域收起侧边栏功能
    document.addEventListener('click', (e) => {
        // 如果侧边栏已展开，并且点击的不是侧边栏内的元素，也不是展开侧边栏的按钮
        if (isSidebarExpanded && 
            !e.target.closest('#historySidebar') && 
            !e.target.closest('#historyIcon') &&
            !e.target.closest('#newChatIcon')) {
            collapseSidebar();
        }
    });
    
    // 初始加载历史会话记录
    loadChatHistories();
}

// 切换侧边栏展开/收起状态
function toggleSidebar() {
    historySidebar.classList.toggle('sidebar-expanded');
    containerElement.classList.toggle('sidebar-expanded');
    isSidebarExpanded = historySidebar.classList.contains('sidebar-expanded');
    
    // 如果展开了侧边栏，重新加载历史记录确保数据是最新的
    if (isSidebarExpanded) {
        loadChatHistories();
    }
}

// 展开侧边栏
function expandSidebar() {
    if (!historySidebar.classList.contains('sidebar-expanded')) {
        historySidebar.classList.add('sidebar-expanded');
        containerElement.classList.add('sidebar-expanded');
        isSidebarExpanded = true;
        loadChatHistories();
    }
}

// 收起侧边栏
function collapseSidebar() {
    if (historySidebar.classList.contains('sidebar-expanded')) {
        historySidebar.classList.remove('sidebar-expanded');
        containerElement.classList.remove('sidebar-expanded');
        isSidebarExpanded = false;
    }
}

// 开始新会话
function startNewChat() {
    // 清空聊天窗口
    chatContainer.innerHTML = '';
    
    // 重置当前会话ID
    currentHistoryId = null;
    
    // 添加欢迎消息
    const welcomeMsg = `<p>您好！我是您的AI医疗助手。请问有什么可以帮您？</p>`;
    addMessage(welcomeMsg, 'ai');
    
    // 更新UI，移除历史项的活动状态
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 收起侧边栏（在小屏幕上）
    if (window.innerWidth < 768) {
        collapseSidebar();
    }
    
    // 聚焦到输入框
    userInput.focus();
}

// 加载所有历史会话记录
async function loadChatHistories() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            // 未登录，无法获取历史记录
            return;
        }
        
        const response = await fetch('/api/medical/chat-history', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('获取历史会话记录失败');
        }
        
        chatHistories = await response.json();
        filteredHistories = [...chatHistories]; // 复制一份用于过滤
        renderChatHistories(chatHistories);
    } catch (error) {
        console.error('加载历史会话记录时出错:', error);
        // 可以添加一个错误提示
        historyList.innerHTML = `
            <div class="history-empty">
                <i class="bi bi-exclamation-triangle"></i>
                <p>加载历史记录失败，请稍后重试</p>
            </div>
        `;
    }
}

// 渲染历史会话列表
function renderChatHistories(histories) {
    if (histories.length === 0) {
        historyList.innerHTML = `
            <div class="history-empty">
                <i class="bi bi-chat-square-text"></i>
                <p>暂无历史会话记录</p>
            </div>
        `;
        return;
    }
    
    historyList.innerHTML = '';
    
    // 按日期对会话进行分组
    const groupedHistories = groupHistoriesByDate(histories);
    
    // 遍历分组并渲染
    for (const [dateGroup, items] of Object.entries(groupedHistories)) {
        // 添加日期分隔符
        const dateDivider = document.createElement('div');
        dateDivider.className = 'history-date-divider';
        dateDivider.textContent = dateGroup;
        historyList.appendChild(dateDivider);
        
        // 添加该日期下的所有会话
        items.forEach(history => {
            const date = new Date(history.updated_at);
            const formattedTime = formatTime(date);
            
            const historyItem = document.createElement('div');
            historyItem.className = `history-item${history.id === currentHistoryId ? ' active' : ''}`;
            historyItem.dataset.id = history.id;
            historyItem.innerHTML = `
                <div class="history-item-title">${escapeHtml(history.title)}</div>
                <div class="history-item-meta">
                    <span>${formattedTime}</span>
                    <span>${history.message_count}条</span>
                </div>
                <button class="history-item-delete" title="删除此会话">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            
            // 点击加载会话
            historyItem.addEventListener('click', (e) => {
                // 如果点击的是删除按钮，则不加载会话
                if (e.target.closest('.history-item-delete')) {
                    e.stopPropagation();
                    historyToDelete = history.id;
                    deleteHistoryModal.show();
                    return;
                }
                loadChatHistoryDetail(history.id);
            });
            
            historyList.appendChild(historyItem);
        });
    }
}

// 按日期对历史记录进行分组
function groupHistoriesByDate(histories) {
    const groups = {};
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // 清除时分秒，便于比较日期
    today.setHours(0, 0, 0, 0);
    yesterday.setHours(0, 0, 0, 0);
    
    histories.forEach(history => {
        const date = new Date(history.updated_at);
        const historyDate = new Date(date);
        historyDate.setHours(0, 0, 0, 0);
        
        let groupName;
        
        if (historyDate.getTime() === today.getTime()) {
            groupName = '今天';
        } else if (historyDate.getTime() === yesterday.getTime()) {
            groupName = '昨天';
        } else {
            // 计算是否在7天内
            const daysDiff = Math.floor((today - historyDate) / (1000 * 60 * 60 * 24));
            if (daysDiff <= 7) {
                groupName = '7天内';
            } else {
                groupName = '更早';
            }
        }
        
        if (!groups[groupName]) {
            groups[groupName] = [];
        }
        
        groups[groupName].push(history);
    });
    
    // 为每个组内的历史记录按更新时间排序
    for (const groupName in groups) {
        groups[groupName].sort((a, b) => {
            return new Date(b.updated_at) - new Date(a.updated_at);
        });
    }
    
    return groups;
}

// 格式化日期
function formatDate(date) {
    const now = new Date();
    const diff = now - date;
    const day = 24 * 60 * 60 * 1000;
    
    if (diff < day) {
        return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else if (diff < 2 * day) {
        return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } else {
        return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }) + ' ' + 
               date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
}

// 只格式化时间部分
function formatTime(date) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
}

// 加载特定会话的详细内容
async function loadChatHistoryDetail(historyId) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            return;
        }
        
        // 显示加载动画
        chatContainer.innerHTML = `<div class="d-flex justify-content-center my-5"><div class="spinner-border text-primary" role="status"></div></div>`;
        
        const response = await fetch(`/api/medical/chat-history/${historyId}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('获取会话详情失败');
        }
        
        const history = await response.json();
        currentHistoryId = history.id;
        
        // 更新UI，标记当前活动的会话
        document.querySelectorAll('.history-item').forEach(item => {
            if (parseInt(item.dataset.id) === currentHistoryId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // 清空聊天容器
        chatContainer.innerHTML = '';
        
        // 确保messages数组存在并有内容
        if (history.messages && history.messages.length > 0) {
            // 渲染消息
            history.messages.forEach(message => {
                const type = message.is_user ? 'user' : 'ai';
                const content = message.content;
                
                // 使用已有的addMessage函数渲染消息
                addMessage(content, type);
            });
        } else {
            // 如果没有消息，显示提示
            addSystemMessage('此会话没有消息记录');
        }
        
        // 确保侧边栏收起状态正确
        if (window.innerWidth < 768) {
            collapseSidebar();
        }
        
        // 滚动到底部
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch (error) {
        console.error('加载会话详情时出错:', error);
        addSystemMessage('加载历史会话记录失败，请稍后重试');
    }
}

// 创建消息元素，复用部分addMessage函数的逻辑
function createMessageElement(content, type) {
    // 直接使用addMessage函数复用其逻辑
    return addMessage(content, type);
}

// 搜索历史会话
function searchHistories() {
    const query = historySearchInput.value.toLowerCase().trim();
    
    if (!query) {
        // 如果没有搜索词，显示所有历史记录
        filteredHistories = [...chatHistories];
    } else {
        // 根据标题过滤
        filteredHistories = chatHistories.filter(history => 
            history.title.toLowerCase().includes(query)
        );
    }
    
    // 渲染过滤后的结果
    renderChatHistories(filteredHistories);
}

// 删除单个会话记录
async function deleteChatHistory(historyId) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        const response = await fetch(`/api/medical/chat-history/${historyId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('删除会话记录失败');
        }
        
        // 如果删除的是当前会话，清空聊天窗口
        if (historyId === currentHistoryId) {
            chatContainer.innerHTML = '';
            currentHistoryId = null;
            addSystemMessage('当前会话已被删除');
        }
        
        // 重新加载会话记录
        loadChatHistories();
        
    } catch (error) {
        console.error('删除会话记录时出错:', error);
        addSystemMessage('删除会话记录失败，请稍后重试');
    }
}

// 清空所有会话记录
async function clearAllChatHistories() {
    try {
        const promises = [];
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        // 逐个删除所有会话记录
        for (const history of chatHistories) {
            const promise = fetch(`/api/medical/chat-history/${history.id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            promises.push(promise);
        }
        
        await Promise.all(promises);
        
        // 清空聊天窗口
        chatContainer.innerHTML = '';
        currentHistoryId = null;
        
        // 重新加载会话记录（应该为空）
        loadChatHistories();
        
        // 关闭modal
        clearAllHistoryModal.hide();
        
        addSystemMessage('所有会话记录已清空');
        
    } catch (error) {
        console.error('清空所有会话记录时出错:', error);
        clearAllHistoryModal.hide();
        addSystemMessage('清空会话记录失败，请稍后重试');
    }
}

// 转义HTML字符
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}