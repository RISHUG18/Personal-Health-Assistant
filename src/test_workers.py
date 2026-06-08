import asyncio
import httpx
import time
import uuid

API_URL = "http://127.0.0.1:8000"

async def create_user_and_login(client):
    email = f"test_worker_{uuid.uuid4().hex[:8]}@example.com"
    password = "password123"
    
    # Register
    resp = await client.post(f"{API_URL}/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test Worker",
        "role": "patient"
    })
    if resp.status_code >= 400:
        print(f"Registration failed: {resp.text}")
    resp.raise_for_status()
    data = resp.json()
    return data["user_id"], data["access_token"]

async def process_report(client, user_id, access_token, task_id):
    headers = {"Authorization": f"Bearer {access_token}"}
    
    pdf_path = "sample_reports/healthy/healthy__Aarav_Gupta__24M.pdf"
    with open(pdf_path, "rb") as f:
        dummy_pdf = f.read()
    
    files = {"file": ("healthy__Aarav_Gupta__24M.pdf", dummy_pdf, "application/pdf")}
    data = {"user_id": user_id, "user_name": "Test User"}
    
    start_time = time.time()
    print(f"[Task {task_id}] Uploading report...")
    resp = await client.post(f"{API_URL}/reports/ingest", data=data, files=files, headers=headers)
    if resp.status_code != 202:
        print(f"[Task {task_id}] Failed to upload: {resp.text}")
        return
    
    resp_data = resp.json()
    report_id = resp_data["report_id"]
    print(f"[Task {task_id}] Uploaded. Report ID: {report_id}. Queue backend: {resp_data.get('queue_backend')}")
    
    # Poll status
    while True:
        status_resp = await client.get(f"{API_URL}/reports/status/{report_id}", headers=headers)
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = status_data["processing_status"]
        
        if status in ("done", "completed", "failed"):
            end_time = time.time()
            print(f"[Task {task_id}] Finished with status: {status} in {end_time - start_time:.2f} seconds")
            if status == "failed":
                print(f"[Task {task_id}] Error: {status_data.get('processing_error')}")
            return end_time - start_time
            
        await asyncio.sleep(1)

async def main():
    async with httpx.AsyncClient(timeout=60.0) as client:
        user_id = "a1266b8b-4447-45d2-816f-c99ef07a87bb"
        access_token = "dummy-token"
        print(f"Using dummy user: {user_id}")
        
        num_tasks = 4
        print(f"Spawning {num_tasks} tasks...")
        
        start_time = time.time()
        tasks = []
        for i in range(num_tasks):
            tasks.append(process_report(client, user_id, access_token, i))
            
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        print("All tasks finished.")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        print(f"Individual times: {results}")

if __name__ == "__main__":
    asyncio.run(main())
