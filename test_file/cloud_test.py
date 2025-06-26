from moviepy import *
import os
import random
import tempfile
import requests
from urllib.parse import urlparse

def random_effect(clip, duration, screen_size=(720, 1280)):
    effect_type = random.choice(['slide_vertical', 'slide_horizontal', 'zoom'])
    w, h = screen_size
    if effect_type == 'slide_vertical':
        animated = clip.with_position(lambda t: ("center", h - t * 400)).with_duration(duration)
    elif effect_type == 'slide_horizontal':
        animated = clip.with_position(lambda t: (-clip.w + t * 400, "center")).with_duration(duration)
    elif effect_type == 'zoom':
        animated = clip.resized(lambda t: 0.7 * (1 + 0.1 * t)).with_position("center").with_duration(duration)
    else:
        animated = clip.with_position("center").with_duration(duration)
    return CompositeVideoClip([animated], size=screen_size).with_duration(duration)

def is_url(path):
    return path.startswith("http://") or path.startswith("https://")

def download_image_to_tempfile(url):
    response = requests.get(url)
    response.raise_for_status()
    ext = os.path.splitext(urlparse(url).path)[-1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
        tmp_file.write(response.content)
        return tmp_file.name

def create_slideshow_with_effects(image_urls, bg_path, output_file="slideshow.mp4", duration_per_image=2, screen_size=(720, 1280)):
    if not image_urls:
        print("未找到图片链接")
        return

    # 下载并准备背景图
    if is_url(bg_path):
        bg_path = download_image_to_tempfile(bg_path)

    bg_raw = ImageClip(bg_path)
    bg_aspect = bg_raw.w / bg_raw.h
    target_aspect = screen_size[0] / screen_size[1]

    if bg_aspect > target_aspect:
        bg = bg_raw.resized(height=screen_size[1])
    else:
        bg = bg_raw.resized(width=screen_size[0])
    bg = bg.with_position(('center', 'center'))

    clips = []
    for url in image_urls:
        try:
            img_path = download_image_to_tempfile(url)

            # 前景图处理 + 动画
            fg = ImageClip(img_path).resized(height=screen_size[1] * 0.7)
            animated = random_effect(fg, duration_per_image, screen_size)

            # 每一段视频复用背景
            composite = CompositeVideoClip(
                [bg.with_duration(duration_per_image), animated],
                size=screen_size
            ).with_duration(duration_per_image)

            clips.append(composite)
        except Exception as e:
            print(f"处理图片失败: {url}，原因: {e}")
            continue

    if not clips:
        print("未能生成任何视频片段")
        return

    final_clip = concatenate_videoclips(clips, method="compose")
    print(f"正在生成视频: {output_file}")
    final_clip.write_videofile(output_file, fps=24, codec="libx264")
    print(f"✅ 视频已成功保存为: {output_file}")

if __name__ == "__main__":
    image_urls = [
        "https://s.coze.cn/t/6iG6iFq5hsE/",
        "https://s.coze.cn/t/BObrwEvLkA4/",
        "https://s.coze.cn/t/ALe-bqkhuNk/",
        "https://s.coze.cn/t/gbAY_6cYPJA/"
    ]
    background_url = "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/076a6aef2ec64776b4aea46d50e42a2d.jpg~tplv-mdko3gqilj-image.image?rk3s=81d4c505&x-expires=1781956263&x-signature=m8Z3YDOyUAKteAYbK18YBU6dH%2F8%3D"  # ✅ 设置你的背景图 URL
    create_slideshow_with_effects(image_urls, background_url)
