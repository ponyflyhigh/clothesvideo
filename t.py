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


def apply_effect(foreground_clip, background_clip, duration, screen_size=(1280, 720)):
    """叠加动画前景在背景上"""
    w, h = screen_size
    effect = random.choice(['slide_vertical', 'slide_horizontal', 'zoom'])

    foreground_clip = foreground_clip.with_duration(duration)

    if effect == 'slide_vertical':
        animated = foreground_clip.with_position(lambda t: ("center", h - t * 400))
    elif effect == 'slide_horizontal':
        animated = foreground_clip.with_position(lambda t: (-foreground_clip.w + t * 400, "center"))
    elif effect == 'zoom':
        animated = foreground_clip.resized(lambda t: 1 + 0.1 * t).with_position("center")
    else:
        animated = foreground_clip.with_position("center")

    # 合成背景 + 前景
    return CompositeVideoClip([background_clip, animated], size=screen_size).with_duration(duration)


def create_slideshow_with_moving_bg(image_folder, background_path, output_file="slideshow_with_bg.mp4",
                                    duration_per_image=2, screen_size=(1280, 720)):
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
        animated_clip = apply_effect(foreground, background, duration_per_image, screen_size)
        clips.append(animated_clip)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, fps=24, codec="libx264")
    print(f"视频已保存为: {output_file}")


if __name__ == "__main__":
    image_folder = r"C:\Users\86132\Desktop\视频混剪\data"
    background_image = r"C:\Users\86132\Desktop\视频混剪\bg.jpg"
    create_slideshow_with_moving_bg(image_folder, background_image)
