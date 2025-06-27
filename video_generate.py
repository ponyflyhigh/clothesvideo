from moviepy import *
import os
import random
import numpy as np
from PIL import Image


def load_image(path):
    """安全加载图像并转换为 ImageClip"""
    try:
        img = Image.open(path).convert('RGB')
        print(f"✅ 成功加载图像: {path}，尺寸: {img.size}")
        return ImageClip(np.array(img))
    except Exception as e:
        raise ValueError(f"❌ 图像加载失败: {path}, 错误: {e}")


def load_audio(path):
    """安全加载音频文件"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ 音频文件不存在: {path}")
    try:
        audio = AudioFileClip(path)
        print(f"✅ 音频加载成功: {path}, 时长: {audio.duration}s")
        return audio
    except Exception as e:
        raise ValueError(f"❌ 音频加载失败: {path}, 错误: {e}")

def create_dynamic_background(background_path, duration, screen_size=(1280, 720)):
    """创建固定不动的背景"""
    try:
        bg_img = Image.open(background_path)
        print(f"✅ 背景图加载成功: {background_path}, 尺寸: {bg_img.size}")
        
        # 固定大小为屏幕高度匹配，避免 lambda 表达式带来的潜在动画效果
        target_height = screen_size[1]
        aspect_ratio = bg_img.width / bg_img.height
        target_width = int(target_height * aspect_ratio)
        
        # 使用 resized 固定尺寸，不再使用 resized(lambda ...) 避免任何时间相关变换
        bg = (
            ImageClip(np.array(bg_img))
            .resized(height=target_height)  # 固定高度
            .with_position("center")       # 居中显示
            .with_duration(duration)       # 设置持续时间
        )
        
        # 打印最终 clip 尺寸用于调试
        print(f"🖼️ 背景clip最终尺寸: {bg.size}, 持续时间: {bg.duration}s")
        return bg
    except Exception as e:
        raise ValueError(f"❌ 背景图加载失败: {background_path}, 错误: {e}")


def apply_effect(foreground_clip, background_clip, animate_duration, stay_duration, effect, screen_size=(1080, 1920)):
    """叠加动画前景在背景上，先移动到中心再停留"""
    w, h = screen_size
    total_duration = animate_duration + stay_duration
    foreground_clip = foreground_clip.with_duration(total_duration)

    def ease_in_out(t, duration):
        return 3 * (t / duration) ** 2 - 2 * (t / duration) ** 3

    def get_center_position():
        return ((w - foreground_clip.w) / 2, (h - foreground_clip.h) / 2)

    cx, cy = get_center_position()

    if effect == 'slide_vertical':
        def position(t):
            if t < animate_duration:
                progress = ease_in_out(t, animate_duration)
                y = h + foreground_clip.h - progress * (h + foreground_clip.h - cy)
                return (cx, y)
            else:
                return (cx, cy)
    elif effect == 'slide_horizontal':
        def position(t):
            if t < animate_duration:
                progress = ease_in_out(t, animate_duration)
                x = -foreground_clip.w + progress * (cx + foreground_clip.w)
                return (x, cy)
            else:
                return (cx, cy)
    elif effect == 'slide_left_to_right':
        def position(t):
            if t < animate_duration:
                progress = ease_in_out(t, animate_duration)
                x = -foreground_clip.w + progress * (cx + foreground_clip.w)
                return (x, cy)
            else:
                return (cx, cy)

    elif effect == 'slide_right_to_left':
        def position(t):
            if t < animate_duration:
                progress = ease_in_out(t, animate_duration)
                x = w - progress * (w - cx)
                return (x, cy)
            else:
                return (cx, cy)

    elif effect == 'slide_top_to_bottom':
        def position(t):
            if t < animate_duration:
                progress = ease_in_out(t, animate_duration)
                y_start = -foreground_clip.h
                y_end = cy
                y = y_start + progress * (y_end - y_start)
                return (cx, y)
            else:
                return (cx, cy)

    elif effect == 'slide_bottom_to_top':
        def position(t):
            if t < animate_duration:
                progress = ease_in_out(t, animate_duration)
                y_start = h
                y_end = cy
                y = y_start + progress * (y_end - y_start)
                return (cx, y)
            else:
                return (cx, cy)

    elif effect == 'zoom':
        # 缩放放大效果进入
        animated = foreground_clip.resized(lambda t: 0.5 + 0.5 * ease_in_out(t, animate_duration) if t < animate_duration else 1.0)
        animated = animated.with_position((cx, cy)).with_duration(total_duration)
        return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(total_duration)
    else:
        # 默认直接居中
        return CompositeVideoClip([background_clip, foreground_clip.with_position((cx, cy))], size=screen_size).with_duration(total_duration)

    animated = foreground_clip.with_position(position)
    return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(total_duration)


def create_slideshow_with_moving_bg(image_folder, background_path, audio_path=None,
                                    output_file="slideshow_with_bg.mp4", duration_per_image=2,
                                    screen_size=(720,1280), effect='zoom'):
    image_files = sorted([
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])

    if not image_files:
        print("❌ 未找到图片文件")
        return

    clips = []
    for img_path in image_files:
        # 每张图片配一个新背景（带动画）
        background = create_dynamic_background(background_path, duration_per_image, screen_size)

        foreground = load_image(img_path).resized(height=int(screen_size[1] * 0.7))  # 只占70%高度
        animated_clip = apply_effect(foreground, background, duration_per_image, effect, screen_size)
        clips.append(animated_clip)

    final_clip = concatenate_videoclips(clips, method="compose")

    # 添加音频处理
    if audio_path:
        try:
            audio = load_audio(audio_path)
            if audio.duration < final_clip.duration:
                audio = audio.fx(vfx.loop, duration=final_clip.duration)
            else:
                audio = audio.subclipped(0, final_clip.duration)
            final_clip = final_clip.with_audio(audio)
        except Exception as e:
            print(f"⚠️ 音频处理失败，继续生成无音频视频: {e}")

    try:
        final_clip.write_videofile(output_file, fps=24, codec="libx264")
        print(f"✅ 视频已保存为: {output_file}")
    except Exception as e:
        print(f"❌ 视频写入失败: {e}")


def generate_video_clips(image_configs, background_path, screen_size=(1280, 720), progress_callback=None):
    clips = []
    total = len(image_configs)
    for i, config in enumerate(image_configs):
        bg = (
            ImageClip(background_path)
            .resized(height=screen_size[1])  # 固定大小，避免动态缩放
            .with_position("center")
            .with_duration(config['animate_duration'] + config['stay_duration'])
        )

        foreground = ImageClip(config['path']).resized(height=int(screen_size[1] * 0.7))
        animated_clip = apply_effect(
            foreground, bg, config['animate_duration'], config['stay_duration'],
            config['effect'], screen_size
        )
        clips.append(animated_clip)

        if progress_callback:
            progress_callback(i / total)

    final_clip = concatenate_videoclips(clips, method="compose")
    return final_clip


def add_audio(final_clip, audio_path):
    if not os.path.exists(audio_path):
        return final_clip

    audio_clip = AudioFileClip(audio_path)
    if audio_clip.duration < final_clip.duration:
        audio_clip = audio_clip.fx(vfx.loop, duration=final_clip.duration)
    else:
        audio_clip = audio_clip.subclipped(0, final_clip.duration)

    return final_clip.with_audio(audio_clip)


if __name__ == "__main__":
    image_folder = r"C:\Users\pony\Desktop\mine\videoClip\vice\data"
    background_image = r"bg.jpg"
    audio_file = r"audio.mp3"  # 本地音频文件路径

    create_slideshow_with_moving_bg(image_folder, background_image, audio_file)