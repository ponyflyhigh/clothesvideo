_tasks = {}

def create_task():
    import uuid
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"status": "pending"}
    return task_id

def complete_task(task_id):
    _tasks[task_id]["status"] = "completed"

# 可选：清理不再需要的 get_task / update_task_progress 等函数