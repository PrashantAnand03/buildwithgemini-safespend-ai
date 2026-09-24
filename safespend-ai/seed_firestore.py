"""Seed Firestore database with initial financial profile, recurring obligations, and purchase requests."""

from google.cloud import firestore

# HARDCODED Project ID string as required by Agent Platform
PROJECT_ID = "qwiklabs-gcp-01-fa8e86a4b8f6"


def seed_database():
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    db = firestore.Client(project=PROJECT_ID)

    # 1. Seed Financial Profile
    profile_ref = db.collection("financial_profiles").document("default_user")
    profile_data = {
        "user_id": "default_user",
        "user_name": "Alex",
        "current_balance": 4250.00,
        "confirmed_monthly_income": 6500.00,
        "payday_schedule": "1st and 15th of the month",
        "minimum_safety_buffer": 1500.00,
        "discretionary_budget_monthly": 1000.00,
        "risk_tolerance": "conservative",
        "last_updated": firestore.SERVER_TIMESTAMP,
    }
    profile_ref.set(profile_data)
    print("✓ Seeded financial_profiles/default_user")

    # 2. Seed Recurring Obligations
    obligations = [
        {
            "id": "rent",
            "name": "Apartment Rent",
            "amount": 2100.00,
            "due_day": 1,
            "category": "housing",
            "is_essential": True,
        },
        {
            "id": "car_payment",
            "name": "Car Loan Payment",
            "amount": 350.00,
            "due_day": 15,
            "category": "transportation",
            "is_essential": True,
        },
        {
            "id": "utilities",
            "name": "Electric & Water Utility",
            "amount": 180.00,
            "due_day": 20,
            "category": "utilities",
            "is_essential": True,
        },
        {
            "id": "groceries_budget",
            "name": "Essential Monthly Groceries",
            "amount": 600.00,
            "due_day": 5,
            "category": "food",
            "is_essential": True,
        },
        {
            "id": "student_loan",
            "name": "Student Loan Minimum Payment",
            "amount": 250.00,
            "due_day": 25,
            "category": "debt",
            "is_essential": True,
        },
        {
            "id": "subscriptions",
            "name": "Streaming & Cloud Subscriptions",
            "amount": 65.00,
            "due_day": 10,
            "category": "entertainment",
            "is_essential": False,
        },
    ]

    for item in obligations:
        doc_id = item["id"]
        db.collection("recurring_obligations").document(doc_id).set(item)
        print(f"✓ Seeded recurring_obligations/{doc_id}")

    # 3. Seed Purchase Requests / Evaluations History
    evaluations = [
        {
            "id": "req_001",
            "item_name": "Ergonomic Desk Chair",
            "cost": 320.00,
            "recommendation": "pay_in_full",
            "reasoning": "Fits well within discretionary cash flow ($1,000 budget) without touching safety buffer.",
            "payment_method": "Debit / Cash",
            "evaluated_at": "2026-09-01T14:30:00Z",
        },
        {
            "id": "req_002",
            "item_name": "4K OLED Gaming Monitor",
            "cost": 1200.00,
            "recommendation": "wait",
            "reasoning": "Purchasing now would drop liquid balance below $1,500 safety buffer before the 15th payday.",
            "payment_method": "Deferred",
            "evaluated_at": "2026-09-10T10:15:00Z",
        },
    ]

    for req in evaluations:
        doc_id = req["id"]
        db.collection("purchase_evaluations").document(doc_id).set(req)
        print(f"✓ Seeded purchase_evaluations/{doc_id}")

    print("\nDatabase seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
