// 图片预览容器和文件数组
const imageInput = document.getElementById('imageInput');
const preview = document.getElementById('preview');
let fileArray = [];

// 处理文件选择
function handleFiles(files) {
    const newFiles = Array.from(files).filter(file =>
        file.type.startsWith('image/') && !fileArray.some(f => f.name === file.name)
    );
    fileArray = [...fileArray, ...newFiles];
    renderPreview();
}

// 渲染图片预览和动画表单
function renderPreview() {
    preview.innerHTML = '';

    if (fileArray.length === 0) {
        preview.innerHTML = '<div class="text-neutral-400 text-center py-8">未选择图片</div>';
        return;
    }

    // 创建一个flex容器来展示所有图片
    const container = document.createElement('div');
    container.className = 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4';

    fileArray.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = function (e) {
            const card = document.createElement('div');
            card.className = 'bg-white rounded-xl shadow-md overflow-hidden transform hover:shadow-lg transition-all duration-300';

            // 图片预览区域
            const imageContainer = document.createElement('div');
            imageContainer.className = 'relative h-48 overflow-hidden';

            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'w-full h-full object-cover transition-transform duration-500 hover:scale-105';
            img.alt = `图片预览 ${index + 1}`;

            // 删除按钮
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'absolute top-2 right-2 bg-white/80 hover:bg-white text-danger rounded-full w-8 h-8 flex items-center justify-center shadow-md transition-all duration-200';
            deleteBtn.innerHTML = '<i class="fa fa-trash"></i>';
            deleteBtn.onclick = () => {
                fileArray.splice(index, 1);
                renderPreview();
            };

            imageContainer.appendChild(img);
            imageContainer.appendChild(deleteBtn);

            // 动画参数表单
            const formContainer = document.createElement('div');
            formContainer.className = 'p-4 space-y-3';

            // 生成动画参数表单
            formContainer.innerHTML = `
                <h3 class="font-semibold text-neutral-700">图片 ${index + 1}: ${file.name}</h3>
                
                <div class="grid grid-cols-2 gap-3">
                    <div class="space-y-1">
                        <label class="text-sm text-neutral-600">进入动画</label>
                        <select name="effect_in_${index}" class="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all">
                            <option value="zoom">缩放</option>
                            <option value="magnify">放大</option>
                            <option value="slide_left_to_right">左到右滑动</option>
                            <option value="slide_right_to_left">右到左滑动</option>
                            <option value="slide_top_to_bottom">上到下滑动</option>
                            <option value="slide_bottom_to_top">下到上滑动</option>
                                <option value="spin">旋转</option> <!-- 新增旋转选项 -->

                        </select>
                    </div>
                    
                    <div class="space-y-1">
                        <label class="text-sm text-neutral-600">退出动画</label>
                        <select name="effect_out_${index}" class="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all">
                            <option value="zoom">缩放</option>
                            <option value="magnify">放大</option>
                            <option value="slide_left_to_right">左到右滑动</option>
                            <option value="slide_right_to_left">右到左滑动</option>
                            <option value="slide_top_to_bottom">上到下滑动</option>
                            <option value="slide_bottom_to_top">下到上滑动</option>
                                       <option value="spin">旋转</option> <!-- 新增旋转选项 -->

                            </select>
                    </div>
                </div>
                
                <div class="grid grid-cols-3 gap-3">
                    <div class="space-y-1">
                        <label class="text-sm text-neutral-600">进场时长(秒)</label>
                        <input type="number" name="animate_in_duration_${index}" value="1" min="0.5" step="0.5" 
                               class="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all">
                    </div>
                    
                    <div class="space-y-1">
                        <label class="text-sm text-neutral-600">停留时长(秒)</label>
                        <input type="number" name="stay_duration_${index}" value="1" min="0" step="0.5" 
                               class="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all">
                    </div>
                    
                    <div class="space-y-1">
                        <label class="text-sm text-neutral-600">离场时长(秒)</label>
                        <input type="number" name="animate_out_duration_${index}" value="1" min="0.5" step="0.5" 
                               class="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary transition-all">
                    </div>
                </div>
            `;

            card.appendChild(imageContainer);
            card.appendChild(formContainer);
            container.appendChild(card);
        };

        reader.readAsDataURL(file);
    });

    preview.appendChild(container);
}

// 表单提交处理
// 表单提交处理
document.getElementById('videoForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    // 隐藏下载区，显示处理中状态
    document.getElementById('downloadContainer').classList.add('hidden');
    const processingContainer = document.getElementById('processingContainer');
    const processingMessage = document.getElementById('processingMessage');
    processingContainer.classList.remove('hidden');
    processingMessage.textContent = '正在提交素材...';

    // 构建表单数据（与之前相同）
    const formData = new FormData();
    const otherData = new FormData(this);

    fileArray.forEach((file, index) => {
        formData.append('images', file);
        const effectIn = document.querySelector(`[name="effect_in_${index}"]`)?.value || '';
        const effectOut = document.querySelector(`[name="effect_out_${index}"]`)?.value || '';
        const animateInDuration = document.querySelector(`[name="animate_in_duration_${index}"]`)?.value || '1';
        const stayDuration = document.querySelector(`[name="stay_duration_${index}"]`)?.value || '1';
        const animateOutDuration = document.querySelector(`[name="animate_out_duration_${index}"]`)?.value || '1';

        if (!effectIn || !effectOut) {
            alert(`第 ${index + 1} 张图片的动画类型不能为空`);
            processingContainer.classList.add('hidden'); // 隐藏加载状态
            return;
        }

        formData.append(`effect_in_${index}`, effectIn);
        formData.append(`effect_out_${index}`, effectOut);
        formData.append(`animate_in_duration_${index}`, animateInDuration);
        formData.append(`stay_duration_${index}`, stayDuration);
        formData.append(`animate_out_duration_${index}`, animateOutDuration);
    });

    for (let [key, value] of otherData.entries()) {
        if (key !== 'images') {
            formData.append(key, value);
        }
    }

    try {
        // 1. 提交生成请求，获取任务ID
        processingMessage.textContent = '正在提交生成请求...';
        const response = await fetch('/start_generate', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`提交失败: ${await response.text()}`);
        }

        const result = await response.json();
        const taskId = result.task_id; // 假设后端返回任务ID

        if (!taskId) {
            throw new Error('未获取到任务ID');
        }

        // 2. 轮询检测生成状态（每3秒查询一次）
        const checkStatus = async () => {
            try {
                const statusResponse = await fetch(`/check_status?task_id=${taskId}`);
                const statusData = await statusResponse.json();

                switch (statusData.status) {
                    case 'processing':
                        // 生成中，更新提示并继续轮询
                        processingMessage.textContent = statusData.message || `视频生成中（任务ID: ${taskId}）...`;
                        setTimeout(checkStatus, 10000); // 10秒后再次查询
                        break;

                    case 'success':
                        // 生成成功，显示下载按钮
                        processingContainer.classList.add('hidden');
                        const downloadContainer = document.getElementById('downloadContainer');
                        const downloadLink = document.getElementById('downloadLink');
                        downloadLink.href = statusData.video_url;
                        downloadContainer.classList.remove('hidden');
                        break;

                    case 'failed':
                        // 生成失败，显示错误信息
                        processingMessage.textContent = `生成失败: ${statusData.message || '未知错误'}`;
                        // 3秒后隐藏错误状态（可选）
                        setTimeout(() => processingContainer.classList.add('hidden'), 3000);
                        break;

                    default:
                        throw new Error(`未知状态: ${statusData.status}`);
                }
            } catch (error) {
                processingMessage.textContent = `查询状态失败: ${error.message}`;
                setTimeout(() => processingContainer.classList.add('hidden'), 3000);
            }
        };

        // 开始第一次轮询
        processingMessage.textContent = '开始生成视频，请等待...';
        setTimeout(checkStatus, 1000); // 1秒后开始查询

    } catch (error) {
        console.error('提交错误:', error);
        processingMessage.textContent = `提交失败: ${error.message}`;
        // 3秒后隐藏错误状态
        setTimeout(() => processingContainer.classList.add('hidden'), 3000);
    }
});
// 初始化文件输入监听
imageInput.addEventListener('change', function () {
    handleFiles(this.files);
});

// 音频和背景图片预览逻辑（添加空值检查）
document.addEventListener('DOMContentLoaded', function () {
    // 音频预览
    const audioInput = document.getElementById('audioInput');
    if (audioInput) {
        audioInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            const audioPlayer = document.getElementById('audioPlayer');
            const audioFileName = document.getElementById('audioFileName');
            const audioPreview = document.getElementById('audioPreview');

            if (audioPlayer && audioFileName && audioPreview) {
                audioPlayer.src = URL.createObjectURL(file);
                audioFileName.textContent = file.name;
                audioPreview.classList.remove('hidden');
            }
        });
    }

    // 移除音频
    const removeAudio = document.getElementById('removeAudio');
    if (removeAudio) {
        removeAudio.addEventListener('click', function () {
            const audioInput = document.getElementById('audioInput');
            const audioPlayer = document.getElementById('audioPlayer');
            const audioPreview = document.getElementById('audioPreview');

            if (audioInput && audioPlayer && audioPreview) {
                audioInput.value = '';
                audioPlayer.src = '';
                audioPreview.classList.add('hidden');
            }
        });
    }

    // 背景图片预览
    const backgroundInput = document.getElementById('backgroundInput');
    if (backgroundInput) {
        backgroundInput.addEventListener('change', function () {
            const file = this.files[0];
            if (!file) return;

            const backgroundImage = document.getElementById('backgroundImage');
            const backgroundPreview = document.getElementById('backgroundPreview');

            if (backgroundImage && backgroundPreview) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    backgroundImage.src = e.target.result;
                    backgroundPreview.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // 移除背景图片
    const removeBackground = document.getElementById('removeBackground');
    if (removeBackground) {
        removeBackground.addEventListener('click', function () {
            const backgroundInput = document.getElementById('backgroundInput');
            const backgroundImage = document.getElementById('backgroundImage');
            const backgroundPreview = document.getElementById('backgroundPreview');

            if (backgroundInput && backgroundImage && backgroundPreview) {
                backgroundInput.value = '';
                backgroundImage.src = '';
                backgroundPreview.classList.add('hidden');
            }
        });
    }
});

// 初始化预览区域
renderPreview();