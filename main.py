from flask import Flask, request, send_file, jsonify, copy_current_request_context,render_template
import os
from video_generate import generate_video_clips, load_audio
from tasks import create_task, complete_task
from flask_cors import CORS
from threading import Thread
from moviepy import  AudioFileClip, vfx
import shutil
import json
from datetime import datetime


app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 使用绝对路径定义上传文件夹
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'video_tasks')  # 任务文件夹
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
TASK_STATUS = {}  # 内存中保存任务状态：{task_id: {"status": "processing", "message": ""}, ...}

@app.route('/')
def index():
    return render_template('index.html')
# 新增：创建任务时初始化状态
def create_task():
    task_id = datetime.now().strftime("%Y%m%d%H%M%S") + str(os.getpid())  # 生成唯一task_id
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    os.makedirs(task_folder, exist_ok=True)
    
    # 初始化任务状态为"处理中"
    TASK_STATUS[task_id] = {
        "status": "processing",
        "message": "视频生成中，请稍候...",
        "progress": 0,  # 进度百分比（0-100）
        "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 状态持久化到文件（防止服务重启后丢失）
    status_file = os.path.join(task_folder, "status.json")
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(TASK_STATUS[task_id], f, ensure_ascii=False, indent=2)
    
    return task_id


# 新增：完成任务时更新状态
def complete_task(task_id, success=True, message="", progress=100):
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    status_file = os.path.join(task_folder, "status.json")
    
    # 更新状态
    TASK_STATUS[task_id] = {
        "status": "success" if success else "failed",
        "message": message,
        "progress": progress,
        "video_url": f"/download_video?task_id={task_id}" if success else None,
        "complete_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 写入文件持久化
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(TASK_STATUS[task_id], f, ensure_ascii=False, indent=2)


# 新增：状态查询接口（供前端轮询）
@app.route('/check_status')
def check_status():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"status": "error", "message": "缺少task_id参数"}), 400
    
    # 1. 先从内存查询
    if task_id in TASK_STATUS:
        return jsonify(TASK_STATUS[task_id])
    
    # 2. 内存中没有则从文件查询（服务重启后恢复状态）
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    status_file = os.path.join(task_folder, "status.json")
    if os.path.exists(status_file):
        with open(status_file, "r", encoding="utf-8") as f:
            try:
                status = json.load(f)
                return jsonify(status)
            except:
                return jsonify({"status": "error", "message": "状态文件损坏"}), 500
    
    # 3. 任务不存在
    return jsonify({"status": "error", "message": "任务不存在"}), 404


# 原生成接口修改（补充进度更新）
@app.route('/start_generate', methods=['POST'])
def start_generate():
    task_id = create_task()
    task_folder = os.path.join(UPLOAD_FOLDER, task_id)
    
    try:
        # 获取上传文件
        images = request.files.getlist('images')
        audio = request.files.get('audio')
        background = request.files.get('background')
        
        if not images:
            raise ValueError("至少需要上传一张图片")
        
        # 保存图片及配置
        saved_images = []
        for i, img in enumerate(images):
            img_path = os.path.join(task_folder, f"img_{i}.jpg")
            img.save(img_path)
            
            # 解析动画参数
            effect_in = request.form.get(f'effect_in_{i}')
            effect_out = request.form.get(f'effect_out_{i}')
            
            if not effect_in or not effect_out:
                raise ValueError(f"图片 {i} 缺少动画类型参数")
            
            saved_images.append({
                'path': img_path,
                'effect_in': effect_in,
                'effect_out': effect_out,
                'animate_in_duration': float(request.form.get(f'animate_in_duration_{i}', 1)),
                'stay_duration': float(request.form.get(f'stay_duration_{i}', 2)),
                'animate_out_duration': float(request.form.get(f'animate_out_duration_{i}', 1)),
            })
        
        # 处理音频和背景
        audio_path = os.path.join(task_folder, 'audio.mp3') if audio else None
        if audio:
            audio.save(audio_path)
        
        background_path = os.path.join(task_folder, 'bg.jpg')
        if background:
            background.save(background_path)
        else:
            # 确保默认背景存在
            if not os.path.exists('default_bg.jpg'):
                raise FileNotFoundError("默认背景图 default_bg.jpg 不存在")
            shutil.copy('default_bg.jpg', background_path)
        
        # 后台执行生成任务
        @copy_current_request_context
        def background_task():
            try:
                # 更新状态为"正在生成视频"
                
                # 生成视频1
                final_clip = generate_video_clips(saved_images, background_path)
                
                # 添加音频（修复后的逻辑）
                if audio_path:
                    audio_clip = AudioFileClip(audio_path)
                    if audio_clip.duration < final_clip.duration:
                        audio_clip = audio_clip.loop(duration=final_clip.duration)
                    else:
                        audio_clip = audio_clip.subclipped(0, final_clip.duration)
                    
                    # 使用 CompositeAudioClip 正确设置音频
                    final_clip = final_clip.with_audio(audio_clip)
                
                # 保存视频
                output_path = os.path.join(task_folder, 'output_video.mp4')
                final_clip.write_videofile(output_path, fps=24, codec="libx264")
                
                # 生成成功
                complete_task(task_id, success=True, message="视频生成成功")
            
            except Exception as e:
                # 生成失败
                complete_task(task_id, success=False, message=f"生成失败: {str(e)}")
        
        # 启动后台任务
        Thread(target=background_task, args=()).start()
        
        # 确保这里返回响应
        return jsonify({"task_id": task_id, "status": "processing"})
    
    except Exception as e:
        # 捕获所有异常并返回错误响应
        error_msg = str(e)
        # 更新任务状态为失败
        complete_task(task_id, success=False, message=error_msg)
        return jsonify({"status": "error", "message": error_msg}), 400



# 下载接口保持不变（无需修改）
@app.route('/download_video')
def download_video():
    task_id = request.args.get('task_id')
    if not task_id:
        return jsonify({"error": "Missing task_id parameter"}), 400
    
    # 使用绝对路径构建视频文件路径
    folder = os.path.join(UPLOAD_FOLDER, task_id)
    file_path = os.path.join(folder, 'output_video.mp4')
    
    # 打印调试信息（仅用于调试，生产环境可删除）
    print(f"Checking file existence: {file_path}")
    
    if not os.path.exists(file_path):
        # 打印更多调试信息
        print(f"Task folder exists: {os.path.exists(folder)}")
        if os.path.exists(folder):
            print(f"Folder content: {os.listdir(folder)}")
        return jsonify({"error": f"File not found: {file_path}"}), 404
    
    try:
        return send_file(file_path, as_attachment=True, download_name='output_video.mp4')
    except Exception as e:
        return jsonify({"error": f"Failed to download video: {str(e)}"}), 500
if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")