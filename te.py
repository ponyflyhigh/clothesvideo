from moviepy import *
import os
import random


def random_effect(clip, duration, screen_size=(1280, 720)):
    """对 clip 应用限定的转场特效：上下滑动、左右滑动、放大"""
    effect_type = random.choice(['slide_vertical', 'slide_horizontal', 'zoom'])
    w, h = screen_size

    if effect_type == 'slide_vertical':
        # 从下往上滑入
        animated = clip.with_position(lambda t: ("center", h - t * 400)).with_duration(duration)
    elif effect_type == 'slide_horizontal':
        # 从左往右滑入
        animated = clip.with_position(lambda t: (-clip.w + t * 400, "center")).with_duration(duration)
    elif effect_type == 'zoom':
        # 缩放效果
        animated = clip.resized(lambda t: 1 + 0.1 * t).with_position("center").with_duration(duration)
    else:
        animated = clip.with_position("center").with_duration(duration)

    # ⚠️ 必须包裹成 CompositeVideoClip 才能让动画生效
    return CompositeVideoClip([animated], size=screen_size).with_duration(duration)


def create_slideshow_with_effects(image_folder, output_file="slideshow.mp4", duration_per_image=2, screen_size=(1280, 720)):
    """创建带有转场特效的图片轮播视频"""
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
        clip = ImageClip(img_path).resized(height=screen_size[1])
        animated = random_effect(clip, duration_per_image, screen_size)
        clips.append(animated)

    final_clip = concatenate_videoclips(clips, method="compose")
    final_clip.write_videofile(output_file, fps=24, codec="libx264")
    print(f"视频已保存为: {output_file}")


if __name__ == "__main__":
    image_folder = r"C:\Users\86132\Desktop\视频混剪\data"
    create_slideshow_with_effects(image_folder)
