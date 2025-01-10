import time
import requests
import logging

class TranslationClient:
    """
    A client library to interact with the translation server.

    This library provides methods to submit translation jobs, check their statuses,
    cancel jobs, and list all jobs. It is designed to interact seamlessly with the
    provided translation server.

    Args:
        base_url (str): The base URL of the translation server.
        polling_interval (int): The interval (in seconds) to wait between status checks.
        max_retries (int): The maximum number of retries to check the status of a job.
        admin_token (str): An admin token is required to cancel jobs. If not provided, only job submission and status checks are allowed.

    1. Initialize the client:
            >>> client = TranslationClient(
            ...     base_url="http://localhost:4777",
            ...     polling_interval=5,
            ...     max_retries=3,
            ...     admin_token="<ADMIN_TOKEN>"
            ... )

        2. Submit a translation job (Free or Premium) with a user ID:
            >>> free_job_id = client.submit_translation_job(role="free", user_id="f_user123")
            >>> print(f"Free job submitted. Job ID: {free_job_id}")

            >>> premium_job_id = client.submit_translation_job(role="premium", user_id="p_user456")
            >>> print(f"Premium job submitted. Job ID: {premium_job_id}")

        3. Check job status:
            >>> status = client.check_status(free_job_id)
            >>> print(f"Free job status: {status}")

        4. Cancel a job (Admin-only):
            >>> cancel_message = client.cancel_job(free_job_id, reason="No longer needed")
            >>> print(f"Cancel response: {cancel_message}")

        5. List all jobs:
            >>> jobs = client.list_jobs()
            >>> print("All jobs categorized by status:", jobs)
        
    Notes:
        - Ensure the server is running and accessible at `base_url` before using the library.
        - Adjust `polling_interval` and `max_retries` based on server performance and requirements.

    Common Errors:
        - `requests.exceptions.RequestException`: Network or HTTP issues (Eg. server unreachable).
        - 429 Rate Limit Exceeded: Warns and skips job submission for free users exceeding limits.
        - Missing Admin Token: Prevents job cancellations if `admin_token` is not provided.
    """

    def __init__(self, base_url, polling_interval=5, max_retries=3, admin_token=None):
        self.base_url = base_url
        self.polling_interval = polling_interval
        self.max_retries = max_retries
        self.admin_token = admin_token
        logging.basicConfig(level=logging.INFO) # DEBUG will be ignored by default
    
    def submit_translation_job(self, role="free",user_id="anonymous"):
        """
        Submit a new translation job with a specific role and user ID. 
        """
        headers = {"X-User-Id": user_id}
        try:
            response = requests.post(f"{self.base_url}/translate", json={"role": role}, headers=headers)
            response.raise_for_status()
            data = response.json()
            logging.info(f"Job submitted successfully. Job ID: {data['job_id']}")
            return data["job_id"]
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 429:
                logging.warning(f"Rate limit exceeded for user {user_id}. Skipping this request.")
                return None
            logging.error(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request failed: {req_err}")
        return None
    
    def check_status(self, job_id):
        """
        Check status of a translation job and return the final status.
        """
        url = f"{self.base_url}/status/{job_id}"
        retries = 0

        while retries < self.max_retries:
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()

                status = data.get("status")
                if status in ["completed", "failed", "permanently failed", "cancelled"]:
                    logging.info(f"Job {job_id} is {status}.")
                    return status
                elif status == "pending":
                    logging.info(f"Job {job_id} is still pending. Retrying in {self.polling_interval} seconds...")
                    time.sleep(self.polling_interval)
                else:
                    logging.warning(f"Unexpected status for job {job_id}: {status}")
                    return "error"
            except requests.exceptions.RequestException as e:
                print(f"Error checking status for job {job_id}: {e}")
                retries += 1
                time.sleep(self.polling_interval * retries)  # Step to prevent the server from being overwhelmed
            
        logging.error(f"Max retries reached for job {job_id}. Marking as 'error'.")
        return "error"
    
    def cancel_job(self, job_id, reason="No reason provided"):
        """
        ADMIN-ONLY: Cancel a translation job with a reason.
        """
        url = f"{self.base_url}/cancel/{job_id}"
        headers = {"Authorization": f"Bearer {self.admin_token}"} if self.admin_token else {}
        try:
            response = requests.post(url, headers=headers, json={"reason": reason})
            response.raise_for_status()
            data = response.json()
            logging.info(f"Job {job_id} cancelled successfully: {data['message']}")
            return data["message"]
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to cancel job {job_id}: {e}")
            return "Failed to cancel job."

    def list_jobs(self):
        """
        List all the jobs, categorized and their statuses.
        """
        url = f"{self.base_url}/jobs"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            logging.info("Fetched job list successfully.")
            return data
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch job list: {e}")
            return {}
        
if __name__ == "__main__":
    print("This is the client library. Import this module to use its features.")
    
    # To test client library directly, uncomment the following code:
    # client = TranslationClient(base_url="http://localhost:4777", polling_interval=5, max_retries=3)
    # # Submit a job
    # job_id = client.submit_translation_job(role="premium")
    # if job_id:
    #     # Check the job status
    #     final_status = client.check_status(job_id)
    #     print(f"Final status of job {job_id}: {final_status}")
    #     # List all jobs
    #     jobs = client.list_jobs()
    #     print("Job list:", jobs)
