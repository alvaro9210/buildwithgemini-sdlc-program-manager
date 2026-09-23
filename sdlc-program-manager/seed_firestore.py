"""Seed script for Firestore with SDLC tasks and pipeline stages."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-0d49d311856f"
COLLECTION_NAME = "sdlc_tasks"

SEED_TASKS = [
    {
        "id": "TASK-101",
        "title": "Draft PRD for Payment Gateway Integration",
        "description": "Specify multi-currency checkout, Stripe/PayPal providers, and security requirements.",
        "stage": "Requirements",
        "sub_agent": "PRD Requirements Agent",
        "status": "Completed",
        "priority": "High",
        "deliverables": ["PRD-Payment-v1.md", "User-Stories.csv"],
        "blockers": [],
    },
    {
        "id": "TASK-102",
        "title": "Implement Checkout Orchestration Service",
        "description": "Build FastAPI endpoints and integrate Stripe SDK for transaction processing.",
        "stage": "Coding",
        "sub_agent": "Coding Agent",
        "status": "In Progress",
        "priority": "High",
        "deliverables": ["src/checkout_service.py", "src/payment_client.py"],
        "blockers": ["Awaiting Stripe webhook test credentials"],
    },
    {
        "id": "TASK-103",
        "title": "Automated End-to-End Payment Flow Tests",
        "description": "Write pytest integration suites and load tests simulating 500 checkout requests/sec.",
        "stage": "Testing",
        "sub_agent": "Testing Agent",
        "status": "Pending",
        "priority": "Medium",
        "deliverables": ["tests/test_e2e_checkout.py", "load_test_report.html"],
        "blockers": ["Blocked by TASK-102 completion"],
    },
    {
        "id": "TASK-104",
        "title": "Canary Deployment & Production Release Gate",
        "description": "Deploy to staging, run smoke tests, verify zero regression, and promote 10% canary to Cloud Run.",
        "stage": "Deployment",
        "sub_agent": "Release Agent",
        "status": "Pending",
        "priority": "High",
        "deliverables": ["cloudbuild.yaml", "release-notes-v1.2.0.md"],
        "blockers": ["Blocked by TASK-103 approval"],
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    for item in SEED_TASKS:
        doc_id = item["id"]
        doc_ref = db.collection(COLLECTION_NAME).document(doc_id)
        doc_ref.set(item)
        print(f"Seeded document: {doc_id} -> '{item['title']}' [{item['stage']}]")
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
