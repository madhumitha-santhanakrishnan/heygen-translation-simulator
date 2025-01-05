from flask import Flask, jsonify
import time
import random 

app = Flask (__name__)

start_time = time.time()
TRANSLATION_DELAY = 15 # Introducing a delay of 15 seconds to simulate translation job
ERROR_RATE = 0.2 # Introducing an error rate of 20%

@app.route('/status', methods=['GET'])
def get_status():
    """
    Get status of the translation request.
    """
    error_list = ["none", "timeout", "internal error", "unknown"]

    # Simulate errors based on random chance
    if random.random() < ERROR_RATE:
        error_type = random.choice(error_list)
        if error_type == "timeout":
            time.sleep(10)
            return jsonify({'status': 'failed', 'message': 'Request timed out'}), 408
        elif error_type == "internal error":
            return jsonify({'status': 'failed', 'message': 'Internal server error'}), 500
        elif error_type == "unknown":
            return jsonify({'status': 'failed', 'message': 'An unknown error occurred'}), 508

    time_elapsed = time.time() - start_time
    if time_elapsed < TRANSLATION_DELAY: 
        return jsonify({'status': 'pending'})
    return jsonify({'status': 'completed'})

if __name__ == '__main__':
    app.run(port=4777)
