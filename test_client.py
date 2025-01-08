from client import TranslationClient

# Initialize the client
client = TranslationClient(base_url="http://localhost:4777", polling_interval=5, max_retries=3)

# Submit a translation job
print("Submitting a translation job...")
job_id = client.submit_translation_job(role="free")

if job_id:
    # Check the status of the job
    print(f"Polling the status for job ID: {job_id}")
    status = client.check_status(job_id)
    print(f"Final status of job {job_id}: {status}")
else:
    print("Failed to submit the job.")
