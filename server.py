from flask import Flask, jsonify, request
import time
import random 
import uuid
import os

app = Flask (__name__)

app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

ADMIN_TOKEN = "the_secure_token"  
MAX_RETRIES = 3
RATE_LIMIT = 5  # Maximum number of requests for FREE users per hour
user_requests = {}  # Track requests for each user

# Configuration via environment variables
TRANSLATION_DELAY = int(os.getenv("TRANSLATION_DELAY", 15)) # Default delay is 15 seconds (integer)
ERROR_RATE = float(os.getenv("ERROR_RATE", 0.2)) # Default error rate is 20% (float)

jobs = {} # Dictionary to store translation jobs

def update_job_status(job_id):
    """
    Update the status and progress of a translation job. Also, handle retries. 
    """
    job = jobs.get(job_id)
    if job is None:
        return None
    
    if job["status"] == "pending":
        time_elapsed = time.time() - job["start_time"]
        if time_elapsed >= TRANSLATION_DELAY:
            progress = 100
        else:
            progress = int((time_elapsed / TRANSLATION_DELAY) * 100)

        job["progress"] = progress
        
        if progress == 100:
            job["status"] = "completed"

    elif job["status"] == "failed" and job.get("retries", 0) < MAX_RETRIES:
        job["retries"] += 1
        job["status"] = "pending"
        job["start_time"] = time.time()
        job["progress"] = 0

    elif job["status"] == "failed" and job.get("retries", 0) >= MAX_RETRIES:
        job["status"] = "permanently failed"
        job["progress"] = 100
        job["retries"] = MAX_RETRIES
    return job
    
@app.route('/translate', methods=['POST'])
def start_translation():
    """
    Start a new translation job and return unique job ID.
    """
    data = request.get_json()
    role = data.get("role", "free")
    user_id = request.headers.get("X-User-Id", "anonymous")
    # if not user_id:
    #     return jsonify({'status': 'failed', 'message': 'user_id header is required'}), 400
    
    # Rate limiting logic for FREE users
    if role == "free":
        if user_id not in user_requests:
            user_requests[user_id] = 0
        user_requests[user_id] += 1


        if user_requests[user_id] > RATE_LIMIT:
            return jsonify({'status': 'failed', 'message': 'Rate limit exceeded'}), 429
    
    job_id = str(uuid.uuid4())
    job = {
        'status': 'pending',
        'start_time': time.time(),
        'role': role,
        'priority': 1 if role == "premium" else 0,
        'delay': TRANSLATION_DELAY if role == "free" else TRANSLATION_DELAY // 2,
        'progress': 0,
        'retries': 0
    }
    jobs[job_id] = job
    return jsonify({'job_id': job_id, 'role': role, 'priority': job['priority']}), 201

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """
    Get status of a specific translation request by job ID.
    """
    job = update_job_status(job_id)

    if job is None:
        return jsonify({'status': 'failed', 'message': 'Job ID not found'}), 404
    
    # Introduce errors based on random chance
    if random.random() < ERROR_RATE:
        error_list = ["none", "timeout", "internal error", "unknown"]
        error_type = random.choice(error_list)
        if error_type == "timeout":
            time.sleep(10)
            return jsonify({'status': 'failed', 'message': 'Request timed out'}), 408
        elif error_type == "internal error":
            return jsonify({'status': 'failed', 'message': 'Internal server error'}), 500
        elif error_type == "unknown":
            return jsonify({'status': 'failed', 'message': 'An unknown error occurred'}), 508

    return jsonify({'status': job['status']})

@app.route('/process', methods=['POST'])
def process_jobs():
    """
    Process jobs from the queue, prioritizing premium jobs.
    """
    current_time = time.time()
    sorted_jobs = sorted(
        jobs.items(),
        key=lambda x: (-x[1]['priority'], x[1]['start_time'])
    )
    for job_id, job in sorted_jobs:
        if job['status'] == 'completed':
            continue

        # Check if the job is ready for processing
        time_elapsed = current_time - job['start_time']
        if time_elapsed >= job['delay']:
            job['status'] = 'completed' 
            return jsonify({'message': f'Processed job {job_id}', 'role': job["role"]}), 200
    return jsonify({'message': 'No jobs ready for processing'}), 204

@app.route('/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """
    Cancel a specific translation request by job ID.

    This endpoint requires an authorization token for security purposes to make sure only authorized users can perform the cancellation.
    And also, a cancellation reason is recorded for future reference.
    """
    auth_header = request.headers.get('Authorization')
    if auth_header is None or auth_header != f'Bearer {ADMIN_TOKEN}':
        return jsonify({'status': 'failed', 'message': 'Unauthorized access'}), 401
    
    data = request.get_json()
    reason = data.get("reason", "No reason provided.")

    job = jobs.get(job_id)
    if job is None:
        return jsonify({'status': 'failed', 'message': 'Job ID not found'}), 404
    
    if job['status'] == 'completed':
        return jsonify({'status': 'failed', 'message': 'Job already completed, cannot cancel a completed job.'}), 400
    
    # del jobs[job_id] # This line is commented out so that the job is not completely removed from the dictionary
    job["status"] = "cancelled"
    job["reason"] = reason
    return jsonify({'status': 'success', 'message': f'Job {job_id} cancelled successfully','reason':reason}), 200

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs and their statuses.
    """
    for job_id in jobs.keys():
        update_job_status(job_id)
    
    categorized_jobs = {
        "pending": {"free": {}, "premium": {}},
        "completed": {"free": {}, "premium": {}},
        "failed": {"free": {}, "premium": {}},
        "permanently_failed": {"free": {}, "premium": {}},
        "cancelled": {"free": {}, "premium": {}}
    }

    for job_id, job in jobs.items():
        role = job.get("role", "unknown") 
        if job["status"] == "pending":
            categorized_jobs["pending"].setdefault(role, {})[job_id] = job
        elif job["status"] == "completed":
            categorized_jobs["completed"].setdefault(role, {})[job_id] = job
        elif job["status"] == "failed":
            categorized_jobs["failed"].setdefault(role, {})[job_id] = job
        elif job["status"] == "permanently failed":
            categorized_jobs["permanently_failed"].setdefault(role, {})[job_id] = job
        elif job["status"] == "cancelled":
            categorized_jobs["cancelled"].setdefault(role, {})[job_id] = job

    return jsonify(categorized_jobs), 200


@app.route('/cleanup', methods=['POST'])
def cleanup_jobs():
    """
    Remove completed jobs from the jobs dictionary. Clean up old jobs to save memory.
    """
    global jobs
    jobs = {job_id: job for job_id, job in jobs.items() if job['status'] != 'completed'}
    return jsonify({'message': 'Processed jobs removed'}), 200

@app.route('/config', methods=['GET', 'POST'])
def config():
    """
    Get or set the configuration values dynamically, when server is running and restart is not ideal.
    """
    global TRANSLATION_DELAY, ERROR_RATE

    if request.method == 'GET':
        return jsonify({'TRANSLATION_DELAY': TRANSLATION_DELAY, 'ERROR_RATE': ERROR_RATE}), 200
    
    if request.method == 'POST':
        data = request.get_json()
        TRANSLATION_DELAY = data.get('TRANSLATION_DELAY', TRANSLATION_DELAY)
        ERROR_RATE = data.get('ERROR_RATE', ERROR_RATE)
        return jsonify({
            'TRANSLATION_DELAY': TRANSLATION_DELAY,
            'ERROR_RATE': ERROR_RATE,
            'message': 'Configuration updated successfully'
        }), 200
    
if __name__ == '__main__':
    app.run(port=4777)
