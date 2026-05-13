// API 配置
const API_BASE_URL = 'http://localhost:8000';
const API_ENDPOINT = `${API_BASE_URL}/api/v1/analyze-repair`;

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const btnText = document.getElementById('btnText');
const btnLoader = document.getElementById('btnLoader');
const clearBtn = document.getElementById('clearBtn');
const retryBtn = document.getElementById('retryBtn');

const previewSection = document.getElementById('previewSection');
const previewImage = document.getElementById('previewImage');
const resultSection = document.getElementById('resultSection');
const resultContainer = document.getElementById('resultContainer');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');

// 全局变量
let selectedFile = null;
let selectedOptionIndex = null;  // 用户选中的选项索引

// 初始化事件监听
function init() {
    // 点击上传区域
    uploadArea.addEventListener('click', () => fileInput.click());

    // 文件选择
    fileInput.addEventListener('change', handleFileSelect);

    // 拖拽上传
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);

    // 分析按钮
    analyzeBtn.addEventListener('click', analyzeImage);

    // 清除按钮
    clearBtn.addEventListener('click', clearImage);

    // 重试按钮
    retryBtn.addEventListener('click', () => {
        hideError();
        analyzeImage();
    });
}

// 处理文件选择
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

// 处理拖拽
function handleDragOver(event) {
    event.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    uploadArea.classList.remove('dragover');

    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        processFile(file);
    } else {
        showError('请上传图片文件');
    }
}

// 处理文件
function processFile(file) {
    // 验证文件类型
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'];
    if (!validTypes.includes(file.type)) {
        showError('不支持的文件格式，请上传 JPEG, PNG, WebP, GIF, BMP 或 TIFF 格式的图片');
        return;
    }

    // 验证文件大小（最大 10MB）
    if (file.size > 10 * 1024 * 1024) {
        showError('图片文件过大，请上传小于 10MB 的图片');
        return;
    }

    selectedFile = file;

    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewSection.hidden = false;
        analyzeBtn.disabled = false;
        hideResult();
        hideError();
    };
    reader.readAsDataURL(file);
}

// 清除图片
function clearImage() {
    selectedFile = null;
    selectedOptionIndex = null;
    fileInput.value = '';
    previewSection.hidden = true;
    analyzeBtn.disabled = true;
    hideResult();
    hideError();
}

// 分析图片
async function analyzeImage() {
    if (!selectedFile) return;

    // 显示加载状态
    setLoading(true);
    hideResult();
    hideError();

    try {
        // 构建 FormData
        const formData = new FormData();
        formData.append('file', selectedFile);

        // 发送请求
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (response.ok && result.success) {
            showResult(result);
        } else {
            const errorMsg = result.message || result.error?.message || '分析失败，请重试';
            showError(errorMsg);
        }
    } catch (error) {
        console.error('API 调用失败:', error);
        showError('无法连接到服务器，请确保后端服务已启动（python main.py）');
    } finally {
        setLoading(false);
    }
}

// 显示结果
function showResult(result) {
    const options = result.suggested_options || [];
    const metadata = result.metadata || {};

    if (options.length === 0) {
        showError('未能识别出有效的维修选项');
        return;
    }

    let html = '';

    // 单选项：直接展示 + 确认按钮
    if (options.length === 1) {
        const option = options[0];
        html = `
            <div class="result-single">
                <div class="result-header">
                    <div class="result-icon">✅</div>
                    <h3>分析完成</h3>
                </div>
                <div class="result-text">${escapeHtml(option.frontend_display_text)}</div>
                <div class="result-category">分类：${escapeHtml(option.category)}</div>
                <button class="confirm-btn" onclick="confirmRepair(0)">确认报修</button>
            </div>
        `;
    }
    // 多选项：单选框 + 提示语
    else {
        const optionsHtml = options.map((option, index) => `
            <label class="option-card ${selectedOptionIndex === index ? 'selected' : ''}" data-index="${index}">
                <input type="radio" name="repair-option" value="${index}" ${selectedOptionIndex === index ? 'checked' : ''}>
                <div class="option-content">
                    <div class="option-text">${escapeHtml(option.frontend_display_text)}</div>
                    <div class="option-category">${escapeHtml(option.category)}</div>
                </div>
            </label>
        `).join('');

        html = `
            <div class="result-multiple">
                <div class="result-header">
                    <div class="result-icon">🤔</div>
                    <h3>我们发现了多种可能</h3>
                </div>
                <p class="result-hint">请选择最符合您遇到的情况：</p>
                <div class="options-container">
                    ${optionsHtml}
                </div>
                <button class="confirm-btn" id="confirmBtn" disabled>确认报修</button>
            </div>
        `;
    }

    // 添加元数据（处理时间）
    if (metadata.processing_time) {
        html += `<div class="result-metadata">处理时间: ${metadata.processing_time}s</div>`;
    }

    resultContainer.innerHTML = html;
    resultSection.hidden = false;

    // 为多选项绑定事件
    if (options.length > 1) {
        const optionCards = document.querySelectorAll('.option-card');
        const confirmBtn = document.getElementById('confirmBtn');

        optionCards.forEach(card => {
            card.addEventListener('click', () => {
                const index = parseInt(card.dataset.index);
                selectedOptionIndex = index;

                // 更新选中状态
                optionCards.forEach(c => c.classList.remove('selected'));
                card.classList.add('selected');
                card.querySelector('input').checked = true;

                // 启用确认按钮
                confirmBtn.disabled = false;
            });
        });

        confirmBtn.addEventListener('click', () => {
            if (selectedOptionIndex !== null) {
                confirmRepair(selectedOptionIndex);
            }
        });
    }
}

// 确认报修
function confirmRepair(optionIndex) {
    // 这里可以添加提交报修的逻辑
    console.log('用户确认报修，选项索引:', optionIndex);
    alert('报修已提交！');
}

// 显示错误
function showError(message) {
    errorMessage.textContent = message;
    errorSection.hidden = false;
}

// 隐藏错误
function hideError() {
    errorSection.hidden = true;
}

// 隐藏结果
function hideResult() {
    resultSection.hidden = true;
}

// 设置加载状态
function setLoading(loading) {
    analyzeBtn.disabled = loading;
    btnText.hidden = loading;
    btnLoader.hidden = !loading;

    if (loading) {
        btnText.textContent = '分析中...';
    } else {
        btnText.textContent = '开始分析';
    }
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
