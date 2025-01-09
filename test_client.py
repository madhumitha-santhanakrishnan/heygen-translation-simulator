import json
from client import TranslationClient

ADMIN_TOKEN = "the_secure_token"

def main():
    # Initialize the client
    client = TranslationClient(
        base_url="http://localhost:4777",  
        polling_interval=5,
        max_retries=3,
        admin_token="the_secure_token"
    )

    # Step 1: Submit a free job
    print("Submitting a free translation job...")
    free_job_id = client.submit_translation_job(role="free")
    if free_job_id:
        print(f"Free job submitted successfully. Job ID: {free_job_id}")

    # Try out cancellation logic
    if free_job_id:
        print("\nAttempting to cancel the free job...")
        if client.admin_token == ADMIN_TOKEN:
            cancel_message = client.cancel_job(free_job_id, reason="Testing cancellation")
            print(f"Cancel response: {cancel_message}")
        else:
            print("Admin token not set or incorrect. Cannot cancel the job.")


    # Step 2: Submit a premium job
    print("\nSubmitting a premium translation job...")
    premium_job_id = client.submit_translation_job(role="premium")
    if premium_job_id:
        print(f"Premium job submitted successfully. Job ID: {premium_job_id}")

    # Step 3: Check status of the free job
    if free_job_id:
        print("\nChecking status for the free job...")
        free_job_status = client.check_status(free_job_id)
        print(f"Final status of free job {free_job_id}: {free_job_status}")

    # Step 4: Check status of the premium job
    if premium_job_id:
        print("\nChecking status for the premium job...")
        premium_job_status = client.check_status(premium_job_id)
        print(f"Final status of premium job {premium_job_id}: {premium_job_status}")

    # Step 5: List all jobs
    print("\nFetching all jobs categorized by status...")
    jobs = client.list_jobs()
    print("Jobs:\n", json.dumps(jobs,indent=4))

if __name__ == "__main__":
    main()
