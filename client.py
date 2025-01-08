import time
import requests

class TranslationClient:
    def __init__(self, base_url, polling_interval=5, max_retries=3):
        self.base_url = base_url
        self.polling_interval = polling_interval
        self.max_retries = max_retries
    
    def submit_translation_job(self, role="free"):
        try:
            response = requests.post(f"{self.base_url}/translate", json={"role": role})
            data = response.json()
            print(f"Job submitted successfully. Job ID: {data['job_id']}")
            return data["job_id"]
        except requests.exceptions.RequestException as e:
            print(f"Failed to submit the job: {e}")
            return None
    
    def check_status(self, job_id):
        url = f"{self.base_url}/status/{job_id}"
        retries = 0

        while retries < self.max_retries:
            try:
                response = requests.get(url)
                data = response.json()

                status = data.get("status")
                if status == "completed":
                    print(f"Job {job_id} completed successfully.")
                    return "completed"
                elif status == "failed":
                    print(f"Job {job_id} failed.")
                    return "failed"
                elif status == "permanently failed":
                    print(f"Job {job_id} is permanently failed.")
                    return "failed"
                elif status == "pending":
                    print(f"Job {job_id} is still pending. Retrying in {self.polling_interval} seconds...")
                    time.sleep(self.polling_interval)
                else:
                    print(f"Unexpected status for job {job_id}: {status}")
                    return "error"
            except requests.exceptions.RequestException as e:
                print(f"Error checking status for job {job_id}: {e}")
                retries += 1
                time.sleep(self.polling_interval * retries)  # Step to prevent the server from being overwhelmed
            
        print(f"Max retries reached for job {job_id}. Marking as 'error'.")
        return "error"

if __name__ == "__main__":
    client = TranslationClient(base_url="http://localhost:4777", polling_interval=5, max_retries=3)

    # Submit a job
    job_id = client.submit_translation_job(role="premium")
    if job_id:
        # Check the job status
        status = client.check_status(job_id)
        print(f"Final status of job {job_id}: {status}")

