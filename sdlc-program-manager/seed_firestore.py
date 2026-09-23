"""Seed script for Firestore with SDLC projects, tasks, and pipeline stages."""

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-0d49d311856f"
TASKS_COLLECTION = "sdlc_tasks"
PROJECTS_COLLECTION = "sdlc_projects"

SEED_PROJECTS = [
    {
        "id": "proj-payments",
        "name": "Payment Gateway & Checkout",
        "description": "Multi-currency checkout orchestration with Stripe & PayPal integration.",
        "status": "NO-GO",
        "stage": "Testing",
        "completion_score": "50%",
        "holding_release": [
            "[TASK-103 - Testing] Blocked by TASK-102 completion: Automated End-to-End Payment Flow Tests pending execution.",
            "[TASK-104 - Deployment] Blocked by TASK-103 approval: Canary deployment gate pending E2E test verification."
        ],
        "next_steps": [
            "Update TASK-103 to remove dependency on TASK-102 and start test suite.",
            "Run 500 checkout req/sec load tests and generate load_test_report.html.",
            "Complete TASK-104 canary promotion to Cloud Run and sign off release notes."
        ]
    },
    {
        "id": "proj-auth",
        "name": "Customer Identity & Auth SSO",
        "description": "OAuth2 / OIDC authentication service with multi-tenant Google & GitHub sign-in.",
        "status": "GO",
        "stage": "Deployment",
        "completion_score": "100%",
        "holding_release": [],
        "next_steps": [
            "Initiative fully ready for release with zero blockers (100% complete).",
            "Promote 100% production traffic on Cloud Run.",
            "Notify security compliance and archive sprint milestone."
        ]
    },
    {
        "id": "proj-analytics",
        "name": "Real-time Event Analytics",
        "description": "BigQuery streaming ingestion pipeline for real-time order and telemetry events.",
        "status": "NO-GO",
        "stage": "Coding",
        "completion_score": "25%",
        "holding_release": [
            "[TASK-202 - Coding] Awaiting BigQuery write streaming quota increase approval.",
            "[TASK-203 - Testing] Pending schema migration and dead-letter queue verification."
        ],
        "next_steps": [
            "Escalate GCP quota increase request with Cloud Infrastructure team.",
            "Implement Dead Letter Queue (DLQ) retry backoff in Pub/Sub subscriber.",
            "Run integration tests against BigQuery sandbox dataset."
        ]
    },
    {
        "id": "proj-mobile",
        "name": "Mobile Order Tracking App",
        "description": "Cross-platform Flutter mobile client for real-time dispatch and delivery tracking.",
        "status": "GO",
        "stage": "Deployment",
        "completion_score": "100%",
        "holding_release": [],
        "next_steps": [
            "All test suites and security scans passed with zero blockers.",
            "Submit iOS build v2.1.0 to App Store Review.",
            "Roll out 20% phased staged rollout on Google Play Console."
        ]
    }
]

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
        "status": "Completed",
        "priority": "High",
        "deliverables": ["src/checkout_service.py", "src/payment_client.py"],
        "blockers": [],
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
    for proj in SEED_PROJECTS:
        doc_id = proj["id"]
        db.collection(PROJECTS_COLLECTION).document(doc_id).set(proj)
        print(f"Seeded project: {doc_id} -> '{proj['name']}' [{proj['status']}]")

    for item in SEED_TASKS:
        doc_id = item["id"]
        db.collection(TASKS_COLLECTION).document(doc_id).set(item)
        print(f"Seeded task: {doc_id} -> '{item['title']}' [{item['stage']}]")

    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
