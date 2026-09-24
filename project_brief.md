# My agent: SafeSpend AI (Smart Financial Affordability Concierge)

One-liner: A conversational financial agent that helps users evaluate whether they can safely afford an expense by analyzing cashflow, recurring bills, pending payments, and financing options, delivering personalized pay/wait recommendations.

## Tool coverage

- **Memory**: User's monthly income, risk tolerance, savings goals, recurring bill schedules, and past purchase decision history.
- **Tools**:
  - `get_financial_profile`: Fetches current balance, pending payments, confirmed income, and recurring monthly obligations.
  - `evaluate_payment_options`: Compares payment strategies (Pay in Full, Partial + Cash, BNPL/Installments, Wait N Days, Reject).
  - `analyze_expense_document`: Extracts item cost, merchant, and terms from uploaded receipt/invoice images or text messages.
- **Catalog/UI**: Interactive decision cards comparing payment paths (Full, Installments, Wait) with cashflow impact tables.
- **Image gen**: Generates visual financial health/affordability impact cards and projected cashflow gauge graphics.
- **Sandbox**: Executes cashflow projections and interest/BNPL fee simulations over a 3-6 month window.

## Workshop Integration Summary

- **Recommended for every project**: Memory (user profile/goals), Storage (transaction history & expense requests), Tools (financial lookups), Image generation (visual progress cards), A2UI (decision comparison cards).
- **Agent-specific / stretch**: Code Sandbox for multi-month interest and cashflow projection simulations.
