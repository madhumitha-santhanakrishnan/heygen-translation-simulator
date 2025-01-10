import json
import subprocess
import time
from client import TranslationClient
import requests

ADMIN_TOKEN = "the_secure_token"

def get_server_config(client):
    """
    Fetch server configuration dynamically.
    """
    url = f"{client.base_url}/config"
    try:
        response = requests.get(url)
        response.raise_for_status()
        config = response.json()
        return config
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch server configuration: {e}")
        return {}
    
def main():
    # Start the server
    print("Starting the server...")
    server_process = subprocess.Popen(["python", "server.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)  # Allow the server time to start

    try:
        # Initialize the client
        client = TranslationClient(
            base_url="http://localhost:4777",
            polling_interval=5,
            max_retries=3,
            admin_token=ADMIN_TOKEN
        )

        # Fetch server configuration
        server_config = get_server_config(client)
        rate_limit = server_config.get('RATE_LIMIT', 5)  # Default to 5 if not available

        # Initialize User IDs
        free_user_id = "free_user_123"
        premium_user_id = "premium_user_456"

        # Submit a free job
        print("Submitting a free translation job...")
        free_job_id = client.submit_translation_job(role="free", user_id=free_user_id)
        assert free_job_id is not None, "Free job submission failed!"
        print(f"Free job submitted successfully. Job ID: {free_job_id}")

        # Attempt to cancel the free job
        print("\nAttempting to cancel the free job...")
        cancel_message = client.cancel_job(free_job_id, reason="Testing cancellation of a free job.")
        print(f"Cancel response: {cancel_message}")
        assert "cancelled successfully" in cancel_message, "Free job cancellation failed!"

        # Submit a premium job
        print("\nSubmitting a premium translation job...")
        premium_job_id = client.submit_translation_job(role="premium", user_id=premium_user_id)
        assert premium_job_id is not None, "Premium job submission failed!"
        print(f"Premium job submitted successfully. Job ID: {premium_job_id}")

        # Check status of the free job
        print("\nChecking status for the free job...")
        free_job_status = client.check_status(free_job_id)
        print(f"Final status of free job {free_job_id}: {free_job_status}")
        assert free_job_status in ["completed", "cancelled", "failed", "permanently failed"], "Unexpected free job status!"

        # Check status of the premium job
        print("\nChecking status for the premium job...")
        premium_job_status = client.check_status(premium_job_id)
        print(f"Final status of premium job {premium_job_id}: {premium_job_status}")
        assert premium_job_status in ["completed", "failed", "permanently failed"], "Unexpected premium job status!"

        # Test rate limiting
        print("\nTesting rate limiting for free user...")
        exceeded_limit = False
        for i in range(rate_limit+2):  # Attempt 7 requests (RATE_LIMIT is 5)
            print(f"Submitting job {i + 1} for free user {free_user_id}...")
            job_id = client.submit_translation_job(role="free", user_id=free_user_id)
            if job_id:
                print(f"Job {i + 1} submitted successfully. Job ID: {job_id}")
            else:
                exceeded_limit = True
                print(f"Job {i + 1} submission failed due to rate limiting.")
    
        # Ensure rate limit was hit
        assert exceeded_limit, "Rate limit was not enforced as expected!"

        # Fetch all jobs
        print("\nFetching all jobs categorized by status...")
        jobs = client.list_jobs()
        assert "pending" in jobs, "Job listing does not include pending jobs!"
        print("Jobs:\n", json.dumps(jobs, indent=4))

    finally:
        # Stop the server
        print("\nTest completed successfully!")
        print("\nStopping the server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
