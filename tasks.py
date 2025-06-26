# tasks.py
import uuid

tasks = {}

def create_task():
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "processing", "progress": 0}
    return task_id

def update_task_progress(task_id, progress):
    if task_id in tasks:
        tasks[task_id]["progress"] = progress

def complete_task(task_id):
    if task_id in tasks:
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["progress"] = 1.0

def get_task(task_id):
    return tasks.get(task_id)