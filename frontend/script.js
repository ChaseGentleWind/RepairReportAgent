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
            const errorMsg = result.error?.message || '分析失败，请重试';
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
    const { data, metadata } = result;

    let html = '';

    if (data.is_valid_image) {
        // 有效图片
        html = `
            <div class="result-valid">
                <div class="result-header">
                    <div class="result-icon">✅</div>
                    <div class="result-status">
                        <h3>分析成功</h3>
                        <span class="status-badge badge-valid">图片有效</span>
                    </div>
                </div>

                <div class="result-details">
                    <div class="detail-item">
                        <div class="detail-label">识别物件</div>
                        <div class="detail-value">${escapeHtml(data.object_name)}</div>
                    </div>

                    <div class="detail-item">
                        <div class="detail-label">故障描述</div>
                        <div class="detail-value">${escapeHtml(data.issue_description)}</div>
                    </div>

                    <div class="detail-item">
                        <div class="detail-label">问题分类</div>
                        <div class="detail-value">${escapeHtml(data.category)}</div>
                    </div>

                    <div class="detail-item">
                        <div class="detail-label">紧急程度</div>
                        <div class="detail-value">
                            <span class="urgency-badge urgency-${data.urgency.toLowerCase()}">
                                ${getUrgencyText(data.urgency)}
                            </span>
                        </div>
                    </div>

                    ${data.location ? `
                    <div class="detail-item">
                        <div class="detail-label">位置信息</div>
                        <div class="detail-value">${escapeHtml(data.location)}</div>
                    </div>
                    ` : ''}

                    <div class="detail-item">
                        <div class="detail-label">置信度</div>
                        <div class="detail-value">
                            <span class="confidence-badge confidence-${data.confidence.toLowerCase()}">
                                ${data.confidence}
                            </span>
                            ${getConfidenceHint(data.confidence)}
                        </div>
                    </div>

                    <div class="detail-item">
                        <div class="detail-label">推理过程</div>
                        <div class="detail-value detail-reasoning">${escapeHtml(data.reasoning)}</div>
                    </div>
                </div>
            </div>
        `;
    } else {
        // 无效图片
        html = `
            <div class="result-invalid">
                <div class="result-header">
                    <div class="result-icon">❌</div>
                    <div class="result-status">
                        <h3>图片无效</h3>
                        <span class="status-badge badge-invalid">已驳回</span>
                    </div>
                </div>

                <div class="result-details">
                    <div class="detail-item">
                        <div class="detail-label">驳回原因</div>
                        <div class="detail-value">${escapeHtml(data.rejection_reason)}</div>
                    </div>
                </div>
            </div>
        `;
    }

    resultContainer.innerHTML = html;
    resultSection.hidden = false;
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

// 获取置信度提示
function getConfidenceHint(confidence) {
    const hints = {
        'High': '<br><small style="color: #155724;">✓ 高置信度，可直接处理</small>',
        'Medium': '<br><small style="color: #856404;">⚠ 中等置信度，建议复核</small>',
        'Low': '<br><small style="color: #721c24;">⚠ 低置信度，建议人工确认</small>'
    };
    return hints[confidence] || '';
}

// 获取紧急程度文本
function getUrgencyText(urgency) {
    const texts = {
        'High': '🔴 紧急',
        'Medium': '🟡 一般',
        'Low': '🟢 不紧急'
    };
    return texts[urgency] || urgency;
}

// HTML 转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
