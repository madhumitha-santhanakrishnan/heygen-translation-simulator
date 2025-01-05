from flask import Flask, jsonify
import time
import random 
import uuid

app = Flask (__name__)

start_time = time.time()
# To do: Make the translation delay and error rate configurable
TRANSLATION_DELAY = 15 # Introducing a delay of 15 seconds to simulate translation job
ERROR_RATE = 0.2 # Introducing an error rate of 20%

jobs = {} # Dictionary to store translation jobs

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
    job = jobs.get(job_id)

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

    time_elapsed = time.time() - job["start_time"]
    if time_elapsed < TRANSLATION_DELAY: 
        return jsonify({'status': 'pending'})
    else:
        job["status"] = "completed"
        return jsonify({'status': 'completed'})

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs and their statuses (optional endpoint for debugging).
    """
    return jsonify(jobs), 200

if __name__ == '__main__':
    app.run(port=4777)
