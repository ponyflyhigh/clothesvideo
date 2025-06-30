import math
from moviepy import *
import os
import random
import numpy as np
from PIL import Image
from moviepy.video.VideoClip import VideoClip  # 显式引入 VideoClip 支持 make_frame


import math


def load_image(path):
    """安全加载图像并转换为 ImageClip"""
    try:
        img = Image.open(path).convert('RGB')
        #print(f"✅ 成功加载图像: {path}，尺寸: {img.size}")
        return ImageClip(np.array(img))
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
    严格保持前景原始宽高比，初始尺寸为背景的0.7倍（按短边适配）
    缩放/滑动围绕背景中心，不改变图片比例
    """
    w, h = screen_size
    total_duration = animate_in_duration + stay_duration + animate_out_duration
    bg_center_x, bg_center_y = w / 2, h / 2  # 背景中心基准点

    # 关键：计算前景初始缩放比例（保持原始宽高比，最大为背景的0.7倍）
    fg_orig_w, fg_orig_h = foreground_clip.size
    bg_scale = 0.8  # 基准缩放：前景最大尺寸为背景的70%
    # 按比例计算初始缩放（确保不超过背景的0.7倍，且保持宽高比）
    scale_w = (w * bg_scale) / fg_orig_w  # 按宽度的0.7倍计算缩放
    scale_h = (h * bg_scale) / fg_orig_h  # 按高度的0.7倍计算缩放
    base_scale = min(scale_w, scale_h)  # 取较小值，确保前景完全在背景0.7倍范围内

    def get_progress(t: float, duration: float) -> float:
        """平滑缓动，不影响比例"""
        if duration <= 0:
            return 0.0 if t <= 0 else 1.0
        t_clamped = max(0.0, min(t, duration))
        return 0.5 * (1 - math.cos((t_clamped / duration) * math.pi))

    # --------------------------
    # 缩放逻辑（严格保持原始比例）
    # --------------------------
    def get_scale(t: float) -> float:
        # 进场阶段：基于0.7倍基准缩放，不改变比例
        if t < animate_in_duration:
            progress = get_progress(t, animate_in_duration)
            if effect_in == 'zoom':  # 缩小：0.7倍基准 → 0.5倍基准（比例不变）
                return base_scale * (1 - 0.4 * progress)  # 0.7→0.7*0.6=0.42（约0.5倍效果）
            elif effect_in == 'magnify':  # 放大：0.7倍基准 → 1.0倍基准（比例不变）
                return base_scale * (1 + (1/0.7 - 1) * progress)  # 0.7→1.0（同比例放大）
            return base_scale  # 非缩放保持0.7倍基准

        # 停留阶段：保持进场后比例
        elif t < (total_duration - animate_out_duration):
            if effect_in == 'zoom':
                return base_scale * 0.6  # 缩放进场后保持约0.5倍基准
            elif effect_in == 'magnify':
                return base_scale * (1/0.7)  # 放大进场后保持1.0倍基准
            return base_scale  # 非缩放保持0.7倍基准

        # 离场阶段：基于停留比例缩放，不改变原始比例
        else:
            t_out = t - (total_duration - animate_out_duration)
            progress = get_progress(t_out, animate_out_duration)
            current_scale = (base_scale * 0.6) if effect_in == 'zoom' else \
                            (base_scale * (1/0.7)) if effect_in == 'magnify' else base_scale
            if effect_out == 'zoom':  # 继续缩小（比例不变）
                return current_scale * (1 - 0.3 * progress)
            elif effect_out == 'magnify':  # 继续放大（比例不变）
                return current_scale * (1 + (1.3 / current_scale - 1) * progress)
            return current_scale

    # --------------------------
    # 位置逻辑（背景中心为基准，不拉伸比例）
    # --------------------------
    def get_position(t: float) -> tuple[float, float]:
        scale = get_scale(t)
        # 关键：用原始尺寸×缩放比例，保持宽高比不变
        fg_w = fg_orig_w * scale  # 原始宽度×缩放（比例不变）
        fg_h = fg_orig_h * scale  # 原始高度×缩放（比例不变）
        # 始终以背景中心对齐（无论缩放多少，中心点不变）
        base_x = bg_center_x - fg_w / 2
        base_y = bg_center_y - fg_h / 2

        # 进场：从边缘滑向背景中心（不改变比例）
        if t < animate_in_duration:
            progress = get_progress(t, animate_in_duration)
            if effect_in == 'slide_left_to_right':
                return (-fg_w + progress * (bg_center_x - fg_w/2 + fg_w), base_y)
            elif effect_in == 'slide_right_to_left':
                return (w - progress * (w - bg_center_x + fg_w/2), base_y)
            elif effect_in == 'slide_top_to_bottom':
                return (base_x, -fg_h + progress * (bg_center_y - fg_h/2 + fg_h))
            elif effect_in == 'slide_bottom_to_top':
                return (base_x, h - progress * (h - bg_center_y + fg_h/2))
            return (base_x, base_y)

        # 停留：固定在背景中心（比例不变）
        elif t < (total_duration - animate_out_duration):
            return (base_x, base_y)

        # 离场：从中心滑向边缘（不改变比例）
        else:
            t_out = t - (total_duration - animate_out_duration)
            progress = get_progress(t_out, animate_out_duration)
            if effect_out == 'slide_left_to_right':
                return (base_x + progress * (w - base_x), base_y)
            elif effect_out == 'slide_right_to_left':
                return (base_x - progress * (base_x + fg_w), base_y)
            elif effect_out == 'slide_top_to_bottom':
                return (base_x, base_y + progress * (h - base_y))
            elif effect_out == 'slide_bottom_to_top':
                return (base_x, base_y - progress * (base_y + fg_h))
            return (base_x, base_y)

    # 确保背景尺寸正确，前景不强制拉伸（只靠scale控制大小）
    background_clip = background_clip.resized(screen_size) if background_clip.size != screen_size else background_clip
    # 关键：不拉伸前景，只通过后续scale控制大小（保持原始比例）
    if foreground_clip.mask is None:
        foreground_clip = foreground_clip.with_mask()
    if background_clip.mask is None:
        background_clip = background_clip.with_mask()

    # 应用动画（严格保持比例）
    def safe_scale(t: float) -> float:
        return max(0.5 * base_scale, min(get_scale(t), 1.5 * base_scale)) 

    animated_clip = foreground_clip.resized(safe_scale)\
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


# def apply_effect(foreground_clip, background_clip, animate_duration, stay_duration, effect, screen_size=(1080, 1920)):
#     """叠加动画前景在背景上，先移动到中心再停留"""
#     w, h = screen_size
#     total_duration = animate_duration + stay_duration
#     foreground_clip = foreground_clip.with_duration(total_duration)

#     def ease_in_out(t, duration):
#         return 3 * (t / duration) ** 2 - 2 * (t / duration) ** 3

#     def get_center_position():
#         return ((w - foreground_clip.w) / 2, (h - foreground_clip.h) / 2)

#     cx, cy = get_center_position()

    
#     if effect == 'slide_left_to_right':
#         def position(t):
#             if t < animate_duration:
#                 progress = ease_in_out(t, animate_duration)
#                 x = -foreground_clip.w + progress * (cx + foreground_clip.w)
#                 return (x, cy)
#             else:
#                 return (cx, cy)

#     elif effect == 'slide_right_to_left':
#         def position(t):
#             if t < animate_duration:
#                 progress = ease_in_out(t, animate_duration)
#                 x = w - progress * (w - cx)
#                 return (x, cy)
#             else:
#                 return (cx, cy)

#     elif effect == 'slide_top_to_bottom':
#         def position(t):
#             if t < animate_duration:
#                 progress = ease_in_out(t, animate_duration)
#                 y_start = -foreground_clip.h
#                 y_end = cy
#                 y = y_start + progress * (y_end - y_start)
#                 return (cx, y)
#             else:
#                 return (cx, cy)

#     elif effect == 'slide_bottom_to_top':
#         def position(t):
#             if t < animate_duration:
#                 progress = ease_in_out(t, animate_duration)
#                 y_start = h
#                 y_end = cy
#                 y = y_start + progress * (y_end - y_start)
#                 return (cx, y)
#             else:
#                 return (cx, cy)

#     elif effect == 'zoom':
#         # 缩放放大效果进入
#         animated = foreground_clip.resizedddd(lambda t: 0.5 + 0.5 * ease_in_out(t, animate_duration) if t < animate_duration else 1.0)
#         animated = animated.with_position((cx, cy)).with_duration(total_duration)
#         return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(total_duration)
#     else:
#         # 默认直接居中
#         return CompositeVideoClip([background_clip, foreground_clip.with_position((cx, cy))], size=screen_size).with_duration(total_duration)

#     animated = foreground_clip.with_position(position)
#     return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(total_duration)
