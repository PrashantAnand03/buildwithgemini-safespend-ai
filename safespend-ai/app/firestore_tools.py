"""Firestore database integration and function tools for SafeSpend AI."""

import datetime
import uuid
from google.cloud import firestore

# HARDCODED Project ID string as required by Agent Platform
PROJECT_ID = "qwiklabs-gcp-01-fa8e86a4b8f6"


def get_firestore_client() -> firestore.Client:
    return firestore.Client(project=PROJECT_ID)


def get_financial_profile(user_id: str = "default_user") -> dict:
    """Fetches the user's current financial profile, including bank balance, monthly income, safety buffer, and discretionary budget.

    Args:
        user_id: The identifier for the user profile (defaults to 'default_user').

    Returns:
        A dictionary containing financial parameters (current_balance, confirmed_monthly_income, minimum_safety_buffer, etc.).
    """
    db = get_firestore_client()
    doc = db.collection("financial_profiles").document(user_id).get()
    if doc.exists:
        data = doc.to_dict()
        data.pop("last_updated", None)
        return data
    return {"error": f"No financial profile found for user_id '{user_id}'."}


def get_recurring_obligations() -> list[dict]:
    """Fetches all registered monthly recurring obligations and expenses (e.g., rent, car payment, utilities, subscriptions).

    Returns:
        A list of dictionaries representing recurring expenses, including amount, due day, and whether it is essential.
    """
    db = get_firestore_client()
    docs = db.collection("recurring_obligations").stream()
    return [doc.to_dict() for doc in docs]


def save_purchase_evaluation(
    item_name: str,
    cost: float,
    recommendation: str,
    reasoning: str,
    payment_method: str = "pay_in_full",
) -> dict:
    """Saves a purchase evaluation decision to Firestore database history.

    Args:
        item_name: Name of the requested item or expense (e.g. 'Laptop', '4K Monitor').
        cost: The monetary cost of the item in USD.
        recommendation: Recommendation decision ('pay_in_full', 'pay_partially', 'installments', 'wait', 'do_not_proceed').
        reasoning: Detailed reasoning explaining the cashflow calculation and decision.
        payment_method: Preferred payment method or arrangement strategy.

    Returns:
        A dictionary with status 'success' and the created document_id.
    """
    db = get_firestore_client()
    doc_id = f"eval_{uuid.uuid4().hex[:8]}"
    record = {
        "id": doc_id,
        "item_name": item_name,
        "cost": float(cost),
        "recommendation": recommendation,
        "reasoning": reasoning,
        "payment_method": payment_method,
        "evaluated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection("purchase_evaluations").document(doc_id).set(record)
    return {"status": "success", "document_id": doc_id, "record": record}


def get_purchase_history() -> list[dict]:
    """Retrieves previous purchase evaluations and spending decision history.

    Returns:
        A list of previous evaluation records.
    """
    db = get_firestore_client()
    docs = db.collection("purchase_evaluations").stream()
    return [doc.to_dict() for doc in docs]


def simulate_cashflow_projection(item_cost: float, days: int = 30) -> dict:
    """Simulates a day-by-day cashflow balance projection over the next N days to evaluate purchase safety.

    Args:
        item_cost: The cost of the proposed purchase in USD.
        days: Number of future days to simulate (defaults to 30 days).

    Returns:
        A dictionary summarizing starting balance, lowest projected balance, safety buffer status, and recommendation flag.
    """
    profile = get_financial_profile()
    if "error" in profile:
        return profile

    current_balance = float(profile.get("current_balance", 0.0))
    monthly_income = float(profile.get("confirmed_monthly_income", 0.0))
    minimum_safety_buffer = float(profile.get("minimum_safety_buffer", 1500.0))

    semi_monthly_pay = monthly_income / 2.0
    obligations = get_recurring_obligations()

    simulated_balance = current_balance - float(item_cost)
    lowest_balance = simulated_balance
    today = datetime.date.today()
    lowest_date = today

    for day_offset in range(days):
        current_date = today + datetime.timedelta(days=day_offset)

        # Check payday income on 1st and 15th
        if current_date.day in (1, 15) and day_offset > 0:
            simulated_balance += semi_monthly_pay

        # Check recurring bill due dates
        for obligation in obligations:
            due_day = int(obligation.get("due_day", 0))
            if current_date.day == due_day and day_offset > 0:
                simulated_balance -= float(obligation.get("amount", 0.0))

        if simulated_balance < lowest_balance:
            lowest_balance = simulated_balance
            lowest_date = current_date

    safety_buffer_violated = lowest_balance < minimum_safety_buffer
    buffer_deficit = max(0.0, minimum_safety_buffer - lowest_balance)

    return {
        "item_cost": float(item_cost),
        "starting_balance": current_balance,
        "balance_after_immediate_purchase": round(current_balance - float(item_cost), 2),
        "lowest_projected_balance": round(lowest_balance, 2),
        "lowest_balance_date": lowest_date.strftime("%Y-%m-%d"),
        "minimum_safety_buffer": minimum_safety_buffer,
        "safety_buffer_violated": safety_buffer_violated,
        "buffer_deficit": round(buffer_deficit, 2),
        "recommendation_flag": (
            "WAIT_OR_INSTALLMENTS" if safety_buffer_violated else "SAFE_TO_PAY_IN_FULL"
        ),
    }


def get_currency_exchange_rates(
    base_currency: str = "USD", target_currencies: str = "EUR,GBP,CAD,JPY"
) -> dict:
    """Fetches real-time foreign exchange conversion rates from an external public currency API.

    Args:
        base_currency: The 3-letter base currency code (defaults to 'USD').
        target_currencies: Comma-separated 3-letter target currency codes (defaults to 'EUR,GBP,CAD,JPY').

    Returns:
        A dictionary containing live exchange rates and timestamp information.
    """
    import json
    import os
    import urllib.request

    api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
    base = base_currency.strip().upper()

    if api_key:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/{base}"
    else:
        url = f"https://open.er-api.com/v6/latest/{base}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SafeSpend-AI/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))

        rates = data.get("rates", {})
        targets = [c.strip().upper() for c in target_currencies.split(",") if c.strip()]
        filtered_rates = {t: rates[t] for t in targets if t in rates}

        return {
            "status": "success",
            "base_currency": base,
            "rates": filtered_rates,
            "updated_at": data.get("time_last_update_utc", "recently"),
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch exchange rates: {str(e)}"}


