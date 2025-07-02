import math
from moviepy import *
import os
import random
import numpy as np
from PIL import Image
from moviepy.video.VideoClip import VideoClip  # 显式引入 VideoClip 支持 make_frame


import math

def load_image(path):
    try:
        img = Image.open(path).convert("RGBA")  # 读取RGBA格式（含透明通道）
        arr = np.array(img)
        rgb = arr[:, :, :3]  # 颜色通道（RGB）
        alpha = arr[:, :, 3] / 255.0  # 透明通道（Alpha），归一化到0-1之间（0=完全透明，1=完全不透明）
        
        # 创建带遮罩的视频片段：将Alpha通道作为遮罩
        clip = ImageClip(rgb)
        clip = clip.with_mask(ImageClip(alpha, is_mask=True))  # 关键：应用透明遮罩
        return clip
    except Exception as e:
        raise ValueError(f"❌ 图像加载失败: {path}, 错误: {e}")
def load_audio(path):
    """安全加载音频文件"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ 音频文件不存在: {path}")
    try:
        audio = AudioFileClip(path)
        #print(f"✅ 音频加载成功: {path}, 时长: {audio.duration}s")
        return audio
    except Exception as e:
        raise ValueError(f"❌ 音频加载失败: {path}, 错误: {e}")

def create_dynamic_background(background_path, duration, screen_size=(720,1280)):
    bg_img = Image.open(background_path)
    target_height = screen_size[1]
    aspect_ratio = bg_img.width / bg_img.height
    target_width = int(target_height * aspect_ratio)
    bg_img = bg_img.resize((target_width, target_height))
    bg_clip = ImageClip(np.array(bg_img)).with_duration(duration).with_position('center')
    return bg_clip
def ease_in_out(t, duration):
    return 3 * (t/duration)**2 - 2 * (t/duration)**3





def apply_effect(
    foreground_clip: VideoClip,
    background_clip: VideoClip,
    animate_in_duration: float,
    stay_duration: float,
    animate_out_duration: float,
    effect_in: str,
    effect_out: str,
    screen_size: tuple[int, int] = (720, 1280)
) -> CompositeVideoClip:
    """
    严格分离缩放和滑动效果：
    - 缩放始终围绕中心进行
    - 滑动只控制位置，不影响缩放
    """
    w, h = screen_size
    
    total_duration = animate_in_duration + stay_duration + animate_out_duration
    bg_center_x, bg_center_y = w / 2, h / 2  # 背景中心基准点

    # 计算前景初始缩放比例（保持宽高比，最大为背景的0.8倍）
    fg_orig_w, fg_orig_h = foreground_clip.size
    bg_scale = 0.8
    scale_w = (w * bg_scale) / fg_orig_w
    scale_h = (h * bg_scale) / fg_orig_h
    base_scale = min(scale_w, scale_h)  # 基准缩放比例

    def get_progress(t: float, duration: float) -> float:
        """平滑缓动曲线（0→1）"""
        if duration <= 0:
            return 0.0 if t <= 0 else 1.0
        t_clamped = max(0.0, min(t, duration))
        return 0.5 * (1 - math.cos((t_clamped / duration) * math.pi))

    # --------------------------
    # 缩放逻辑（仅控制大小，不影响位置）
    # --------------------------
    def get_scale(t: float) -> float:
        if t < animate_in_duration:
            # 进场阶段
            progress = get_progress(t, animate_in_duration)
            if effect_in == 'zoom':
                return base_scale * (0.01 + 0.99 * progress)  # 从极小放大到基准
            elif effect_in == 'magnify':
                return base_scale * (1 + 1 * progress)  # 从基准放大到1.3倍
            return base_scale  # 其他效果保持基准缩放
        elif t < (total_duration - animate_out_duration):
            # 停留阶段
            return base_scale
        else:
            # 离场阶段
            progress = get_progress(t - (total_duration - animate_out_duration), animate_out_duration)
            if effect_out == 'zoom':
                return base_scale * (1 - 0.99 * progress)  # 从基准缩小到极小
            elif effect_out == 'magnify':
                return base_scale * (1 + 1 * progress)  # 从基准放大到1.3倍
            return base_scale

    # --------------------------
    # 位置逻辑（仅控制位置，不影响缩放）
    # --------------------------
    def get_position(t: float) -> tuple[float, float]:
        # 无论缩放如何，先计算完美居中的位置
        current_scale = get_scale(t)
        fg_current_w = fg_orig_w * current_scale
        fg_current_h = fg_orig_h * current_scale
        centered_x = bg_center_x - (fg_current_w / 2)
        centered_y = bg_center_y - (fg_current_h / 2)

        # 进场阶段
        if t < animate_in_duration:
            progress = get_progress(t, animate_in_duration)
            # 滑动类效果：从边缘到中心
            if effect_in == 'slide_left_to_right':
                start_x = -fg_current_w  # 左侧外
                end_x = centered_x
                return (start_x + progress * (end_x - start_x), centered_y)
            elif effect_in == 'slide_right_to_left':
                start_x = w  # 右侧外
                end_x = centered_x
                return (start_x - progress * (start_x - end_x), centered_y)
            elif effect_in == 'slide_top_to_bottom':
                start_y = -fg_current_h  # 顶部外
                end_y = centered_y
                return (centered_x, start_y + progress * (end_y - start_y))
            elif effect_in == 'slide_bottom_to_top':
                start_y = h  # 底部外
                end_y = centered_y
                return (centered_x, start_y - progress * (start_y - end_y))
            # 非滑动效果：直接居中
            return (centered_x, centered_y)

        # 停留阶段：居中
        elif t < (total_duration - animate_out_duration):
            return (centered_x, centered_y)

        # 离场阶段
        else:
            progress = get_progress(t - (total_duration - animate_out_duration), animate_out_duration)
            # 滑动类效果：从中心到边缘
            if effect_out == 'slide_left_to_right':
                end_x = w
                return (centered_x + progress * (end_x - centered_x), centered_y)
            elif effect_out == 'slide_right_to_left':
                end_x = -fg_current_w
                return (centered_x - progress * (centered_x - end_x), centered_y)
            elif effect_out == 'slide_top_to_bottom':
                end_y = h
                return (centered_x, centered_y + progress * (end_y - centered_y))
            elif effect_out == 'slide_bottom_to_top':
                end_y = -fg_current_h
                return (centered_x, centered_y - progress * (centered_y - end_y))
            # 非滑动效果：直接居中
            return (centered_x, centered_y)

    # 应用动画
    background_clip = background_clip.resized(screen_size) if background_clip.size != screen_size else background_clip
    
    # 关键：分别应用缩放和位置
    scaled_clip = foreground_clip.resized(get_scale)
    animated_clip = scaled_clip\
        .with_position(get_position)\
        .with_duration(total_duration)

    return CompositeVideoClip(
        [background_clip.with_duration(total_duration), animated_clip],
        size=screen_size
    )



def generate_video_clips(image_configs, background_path, screen_size=(720,1280)):
    clips = []
    
    # 加载并调整背景图尺寸 - 添加尺寸验证
    bg_img = Image.open(background_path)
    target_height = screen_size[1]
    aspect_ratio = bg_img.width / bg_img.height if bg_img.height > 0 else 1
    target_width = max(1, int(target_height * aspect_ratio))  # 确保宽度至少为1
    
    if target_width <= 0 or target_height <= 0:
        raise ValueError(f"❌ 背景图尺寸计算失败: 计算得到的尺寸为 ({target_width}, {target_height})")
        
    bg_img = bg_img.resize((target_width, target_height))
    background_clip = ImageClip(np.array(bg_img)).with_position('center')  # 不指定时间，避免统一时长

    for i, config in enumerate(image_configs):
        if screen_size[0] <= 0 or screen_size[1] <= 0:
            raise ValueError(f"❌ 无效的屏幕尺寸: {screen_size}")
        
        # 加载并调整前景图尺寸
        fg_clip = load_image(config['path']).resized(height=int(screen_size[1] * 0.7))
        if fg_clip.w <= 0 or fg_clip.h <= 0:
            raise ValueError(f"❌ 前景图片尺寸无效: {config['path']}, 尺寸: {fg_clip.size}")
        
        # 为当前图片生成动画视频
        anim_clip = apply_effect(
        foreground_clip=fg_clip,
        background_clip=background_clip.with_duration(
            config['animate_in_duration'] + config['stay_duration'] + config['animate_out_duration']
        ),
        animate_in_duration=config['animate_in_duration'],
        stay_duration=config['stay_duration'],
        animate_out_duration=config['animate_out_duration'],
        effect_in=config['effect_in'],
        effect_out=config['effect_out'],
        screen_size=screen_size
    )
        
        clips.append(anim_clip)
    
    # 拼接所有动画片段，无过渡效果
    final = concatenate_videoclips(clips, method='compose')
    return final

