from flask import Flask, request, send_file, jsonify, render_template, make_response, copy_current_request_context
import os
from video_generate import generate_video_clips, add_audio
from tasks import create_task, get_task, update_task_progress, complete_task
from flask_cors import CORS
from threading import Thread

app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/start_generate', methods=['POST'])
def start_generate():
    task_id = create_task()

    @copy_current_request_context
    def background_task(task_id):
        try:
            images = request.files.getlist('images')
            audio = request.files['audio']
            background = request.files['background']

            image_folder = os.path.join(UPLOAD_FOLDER, task_id)
            os.makedirs(image_folder, exist_ok=True)

            image_configs = []
            for i, img in enumerate(images):
                img_path = os.path.join(image_folder, img.filename)
                img.save(img_path)

                effect = request.form.get(f'effect_{i}', 'zoom')
                animate_duration = float(request.form.get(f'animate_duration_{i}', 1))
                stay_duration = float(request.form.get(f'stay_duration_{i}', 2))

                image_configs.append({
                    'path': img_path,
                    'effect': effect,
                    'animate_duration': animate_duration,
                    'stay_duration': stay_duration
                })

            audio_path = os.path.join(image_folder, 'audio.mp3')
            audio.save(audio_path)

            background_path = os.path.join(image_folder, 'bg.jpg')
            if background:
                background.save(background_path)
            else:
                default_bg = 'bg.jpg'
                if not os.path.exists(default_bg):
                    raise FileNotFoundError("默认背景图 bg.jpg 不存在")
                import shutil
                shutil.copy(default_bg, background_path)

            output_path = os.path.join(image_folder, 'output_video.mp4')

            final_clip = generate_video_clips(image_configs, background_path)
            final_clip = add_audio(final_clip, audio_path)

            # 更新进度
            def progress_callback(t):
                update_task_progress(task_id, t)

            final_clip.write_videofile(output_path, fps=24, codec="libx264", progress_bar=False, verbose=False)

            complete_task(task_id)
        except Exception as e:
            print("任务失败:", e)

    # 正确地启动线程
    Thread(target=background_task, args=(task_id,)).start()
    return jsonify({"task_id": task_id})


@app.route('/task_status')
def task_status():
    task_id = request.args.get('task_id')
    task = get_task(task_id)
    if not task:
        return jsonify({"error": "未找到任务"}), 404
    return jsonify(task)


@app.route('/download_video')
def download_video():
    task_id = request.args.get('task_id')
    folder = os.path.join(UPLOAD_FOLDER, task_id)
    file_path = os.path.join(folder, 'output_video.mp4')
    if not os.path.exists(file_path):
        return "文件未生成", 404
    return send_file(file_path, as_attachment=True, download_name='output_video.mp4')


if __name__ == '__main__':
    app.run(debug=True)