from moviepy import *
import os
import random


def create_dynamic_background(background_path, duration, screen_size=(1280, 720)):
    """创建一个动态背景（轻微缩放），不变形"""
    bg = (
        ImageClip(background_path)
        .resized(height=screen_size[1])  # 以高度为准，保持竖屏
        .resized(lambda t: 1.05 + 0.01 * t)  # 轻微放大动效
        .with_position("center")
        .with_duration(duration)
    )
    return bg


def apply_effect(foreground_clip, background_clip, animate_duration, stay_duration, effect, screen_size=(1280, 720)):
    """叠加动画前景在背景上，先移动到中心再停留"""
    w, h = screen_size

    # 设置动画时长
    total_duration = animate_duration + stay_duration

    foreground_clip = foreground_clip.with_duration(total_duration)

    if effect == 'slide_vertical':
        # 垂直方向滑入中心后停留
        def position(t):
            if t < animate_duration:
                return ("center", h - t * (h / animate_duration))
            else:
                return ("center", "center")
    elif effect == 'slide_horizontal':
        # 水平方向滑入中心后停留
        def position(t):
            if t < animate_duration:
                return (-foreground_clip.w + t * (w / animate_duration), "center")
            else:
                return ("center", "center")
    elif effect == 'zoom':
        # 缩放进入中心后停留
        animated = foreground_clip.resized(lambda t: 1 + 0.5 * (t / animate_duration) if t < animate_duration else 1.5)
        animated = animated.with_position("center").with_duration(total_duration)
        return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(total_duration)
    else:
        # 默认居中显示
        return foreground_clip.with_position("center")

    animated = foreground_clip.with_position(position)

    return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(total_duration)
def create_slideshow_with_moving_bg(image_folder, background_path, audio_path=None, 
                                    output_file="slideshow_with_bg.mp4", duration_per_image=2, 
                                    screen_size=(1280, 720), effect='zoom'):
    image_files = sorted([
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])

    if not image_files:
        print("未找到图片文件")
        return

    clips = []
    for img_path in image_files:
        # 每张图片配一个新背景（带动画）
        background = create_dynamic_background(background_path, duration_per_image, screen_size)

        foreground = ImageClip(img_path).resized(height=int(screen_size[1] * 0.7))  # 只占70%高度
        animated_clip = apply_effect(foreground, background, duration_per_image, effect, screen_size)
        clips.append(animated_clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    
    # 添加音频处理
    if audio_path and os.path.exists(audio_path):
        audio = AudioFileClip(audio_path)
        
        # 如果音频长度不足视频长度，则循环音频
        if audio.duration < final_clip.duration:
            audio = audio.fx(vfx.loop, duration=final_clip.duration)
        # 如果音频长度超过视频长度，则截取前部分
        else:
            audio = audio.subclipped(0, final_clip.duration)
            
        final_clip = final_clip.with_audio(audio)

    final_clip.write_videofile(output_file, fps=24, codec="libx264")
    print(f"视频已保存为: {output_file}")



def generate_video_clips(image_configs, background_path, screen_size=(1280, 720), progress_callback=None):
    clips = []
    total = len(image_configs)
    for i, config in enumerate(image_configs):
        bg = (
            ImageClip(background_path)
            .resized(height=screen_size[1])
            .resized(lambda t: 1.05 + 0.01 * t)
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