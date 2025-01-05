from flask import Flask, jsonify, request
import time
import random 
import uuid
import os

app = Flask (__name__)

start_time = time.time()

# Configuration via environment variables
TRANSLATION_DELAY = int(os.getenv("TRANSLATION_DELAY", 15)) # Default delay is 15 seconds (integer)
ERROR_RATE = float(os.getenv("ERROR_RATE", 0.2)) # Default error rate is 20% (float)

jobs = {} # Dictionary to store translation jobs

def update_job_status(job_id):
    """
    Update the status of a translation job.
    """
    job = jobs.get(job_id)
    if job is None:
        return None
    
    if job["status"] == "pending":
        time_elapsed = time.time() - job["start_time"]
        if time_elapsed >= TRANSLATION_DELAY:
            job["status"] = "completed"
    return job
    
@app.route('/translate', methods=['POST'])
def start_translation():
    """
    Start a new translation job and return unique job ID.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'pending',
        'start_time': time.time()
    }
    return jsonify({'job_id': job_id}), 201

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

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs and their statuses.
    """
    for job_id in jobs.keys():
        update_job_status(job_id)
    return jsonify(jobs), 200

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
