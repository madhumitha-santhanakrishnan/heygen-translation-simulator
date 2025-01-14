# HeyGen Translation Simulator

Welcome to the HeyGen Translation Simulator! 

## Overview
This project is an attempt to mimic the simulation of HeyGen's video translation feature. It includes:
1. **Backend Simulation**: A Flask-based backend server to simulate the behavior of the video translation process.
2. **Client Library**: A client library using Python to interact with the server.

---

## Features

- **Server**:
  - Role-based job submissions (`free` and `premium`).
  - Rate limiting for free users to simulate request caps.
  - Progress tracking for jobs.
  - Retry mechanism for failed jobs.
  - Admin-only job cancellation.
  - Prioritize and process jobs from queues manually. 
    - The `process_jobs` endpoint is designed for manual simulation of job processing.
    - Jobs are prioritized by role (`premium` jobs processed before `free` jobs).
    - This endpoint is useful for testing and demonstrating queue prioritization logic.
    - **Note**: Jobs are not processed automatically in this implementation to maintain a controlled simulation environment.
  - Dynamic server configuration.
  - Job cleanup functionality.
  - Configurable delay, error rate, and rate limit via environment variables.
    - Error Simulation: Introduces a configurable error rate (default: 20%) to simulate real-world scenarios. Errors include timeouts, internal server issues, and unexpected failures.
    - Translation Delay: Configurable delay (default: 15 seconds) to mimic the real-world time taken for video translation. Premium jobs are processed faster with reduced delay, and prioritized. 
    - Rate Limit: Configurable limit on the number of requests 'free' users can make per hour (default: 5). This is enforced using the X-User-Id header, simulating real-world user-specific restrictions.


- **Client Library**:
  - Simplifies interaction with the server.
  - Intelligent polling mechanism to optimize status checks (Eg. exponential backoffs to avoid overwhelming the server.)
  - Admin support for job cancellation.
  - Error handling and retries (for status checks).

- **Integration Test**:
  - Spin up the server and test some endpoints using the client library.
  - Validate key workflows (job submission, rate limiting, cancellations, etc.).

---

## Setup Instructions

### Prerequisites

- Python 3.8 or higher.
- `pip` for managing Python packages.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/madhumitha-santhanakrishnan/heygen-translation-simulator.git
   cd heygen-translation-simulator
   ```

2. Create and activate a virtual environment:
    ```bash
   python -m venv venv
   source venv/bin/activate # On Windows: venv\Scripts\activate

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   python server.py
   ```

---

## Usage

### Running the Server

Start the server by running:
```bash
python server.py
```

The server will run on `http://localhost:4777` by default.

### Using the Client Library

The client library is provided in `client.py`. You can use it to interact with the server.

#### Quick Example
```python
from client import TranslationClient

# Initialize the client
client = TranslationClient(base_url="http://localhost:4777")

# Submit a job with premium role
job_id = client.submit_translation_job(role="premium", user_id="user_123")
print(f"Submitted job ID: {job_id}")

# Check the job status & poll the status of the submitted job until it completes or fails
status = client.check_status(job_id)
print(f"Job {job_id} status: {status}")

# List all jobs, categorized by their status
jobs = client.list_jobs()
print("All jobs:", jobs)
```

---

## Integration Test

Run the integration test script to validate the project:
```bash
python test_client.py
```
The script will:
- Start the server.
- Submit free and premium jobs.
- Check statuses of the jobs.
- Test rate limiting for free users. 
- Attempt to cancel jobs.
- Fetch all jobs categorized by status.
- Stop the server. 

#### Note: The provided integration test (`test_client.py`) is designed to be **simple and understandable**, demonstrating the core features of the client library and server interaction. To maintain clarity, the following advanced features were not included in this test file but have been tested independently during development:

1. **Error Rate Testing**:
    - Validation of random server errors (timeouts, internal errors, unknown failures) and how the client library handles it.

2. **Dynamic Server Configuration**:
    - Updating server settings (e.g., rate limits, error rates, delays) dynamically and validating that changes take effect.

3. **Parallel Job Submission**:
    - Simulating real-world scenarios with concurrent job submissions using the `concurrent.futures` module.

#### Features Tested
Despite simplifying the test, the following key features are covered in the integration test:
- **Job submission**: Demonstrates submission of both free and premium jobs.
- **Rate limiting enforcement**: Ensures free users are restricted to the configured request limit.
- **Job cancellation**: Tests the admin-only feature to cancel a job with a reason.
- **Job status checking**: Validates the status progression of submitted jobs.
- **Job categorization and listing**: Fetches and displays all jobs grouped by their statuses.

By focusing on these core functionalities, the test ensures the client-server interaction is robust and reliable. The advanced features listed above can be integrated into future iterations if needed.

---

## API Documentation

#### `POST /translate`
Submit a new translation job.
- **Headers**: `X-User-Id` (string, required for rate limiting).
- **Body Parameters**:
  - `role`: `free` or `premium` (default: `free`).
- **Response**:
  ```json
  { "job_id": "unique-job-id", "role": "free", "priority": 0 }
  ```

#### `GET /status/<job_id>`
Fetch the status of a translation job.
- **Response**:
  ```json
  { "status": "pending/completed/cancelled/failed/permanently_failed" }
  ```

#### `POST /cancel/<job_id>`
Cancel a job (Admin-only).
- **Headers**:
  - `Authorization`: `Bearer <admin_token>`.
- **Body Parameters**:
  - `reason`: Reason for cancellation (optional).
- **Response**:
  ```json
  { "message": "Job cancelled successfully" }
  ```

#### `GET /jobs`
List all jobs categorized by status.
- **Response**:
  ```json
  {
    "pending": { "free": {}, "premium": {} },
    "completed": { "free": {}, "premium": {} },
    "cancelled": { "free": {}, "premium": {} },
    "failed": { "free": {}, "premium": {} },
    "permanently_failed": { "free": {}, "premium": {} }
  }
  ```

#### `POST /cleanup`
Removes completed jobs from the dictionary to optimize memory usage.
- **Response**:
  ```json
  { "message": "Processed jobs removed" }
  ```

#### `GET /config`
Fetch the current server configuration.
- **Response**:
  ```json
  { "TRANSLATION_DELAY": 15, "ERROR_RATE": 0.2, "RATE_LIMIT": 5 }
  ```

#### `POST /config`
Update server configuration dynamically.
- **Body Parameters**:
  - `TRANSLATION_DELAY` (integer).
  - `ERROR_RATE` (float).
  - `RATE_LIMIT` (integer).
- **Response**:
  ```json
  { "message": "Configuration updated successfully" }
  ```

### API Testing

To test the API endpoints, we can use tools like **Postman** or **cURL** for testing.

#### Using Postman:
1. Create requests, or use the API documentation.
2. Add required headers (e.g., `Authorization`, `X-User-Id`) and body parameters as specified in the API documentation.
3. Send requests and view responses in Postman.

#### Using cURL:
You can use the following examples to test the endpoints via the command line:

- **Submit a Translation Job**:
  ```bash
  curl -X POST http://localhost:4777/translate \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user123" \
  -d '{"role": "free"}'
  ```
    - **Response**:
    ```json
    { "job_id": "unique-job-id", "role": "free", "priority": 0 }
    ```
- **Check Job Status**:
  ```bash
  curl -X POST http://localhost:4777/status/<unique-job-id>
  ```
    - **Response**:
    ```json
    { "job_id": "unique-job-id", "role": "free", "priority": 0 }
    ```
- **Cancel a Job**:
  ```bash
  curl -X POST http://localhost:4777/cancel/<unique-job-id> \
  -H "Authorization: Bearer the_secure_token" \
  -d '{"reason": "Testing cancellation"}'
  ```
    - **Response**:
    ```json
    { "message": "Job cancelled successfully" }
    ```

### Sample Test Output

A sample output of the integration test (`test_client.py`) is included in this repository for reference. 
```bash
python test_client.py > test_output.txt
```
To view the test output, simply open the `test_output.txt` file in this repository.

**Note**: While running `test_client.py` is quite straightforward, the `test_output.txt` file is included for your convenience. The actual test output may vary based on your server configuration (e.g., error rate, rate limit, translation delay) and usage patterns. 

### Troubleshooting

- **Server Port Conflict**: If the server port `4777` is already in use, update the `app.run(port=...)` line in `server.py` to use a different port.

### Planned Work

While the current implementation is fully functional, I have planned the following features for future iterations.

1. Log server performance metrics like request processing times, errors, and completed jobs. 
2. Develop a web interface to visualize job statuses, queue priorities, and other metrics in real-time. 
3. Add unit tests and more complex integration tests to handle edge cases like submitting cancellations simultaneously, high error-rate scenarios etc. 
4. Switch to FastAPI for asynchronous processing of jobs. 
5. An additional endpoint/feature to handle user-specific job history.
6. Add support for **actual video file uploads** to simulate the complete video translation process. Integrate libraries like 'ffmpeg' for handling video operations. 
