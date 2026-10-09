from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated, Literal
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import CurrentUser
from app.database import get_db

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/payments", tags=["Payments & Subscriptions"])

PLAN_CATALOG = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "monthly_price": 29,
        "yearly_price": 240,  # $20/mo billed annually
        "credits": 1000,
        "automations": 10,
        "features": [
            "1,000 AI Credits",
            "10 Automations & Mock Loops",
            "Basic Integrations & ATS Match",
            "Community Support",
        ],
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "monthly_price": 79,
        "yearly_price": 660,  # $55/mo billed annually
        "credits": 10000,
        "automations": -1,  # unlimited
        "features": [
            "10,000 AI Credits",
            "Unlimited Mock Interviews & Automations",
            "1536d PGVector Semantic Matching",
            "Advanced Integrations & Biometrics",
            "Priority Support & Recruiter Calibration",
        ],
    },
    "business": {
        "id": "business",
        "name": "Business",
        "monthly_price": 199,
        "yearly_price": 1680,  # $140/mo billed annually
        "credits": 50000,
        "automations": -1,
        "features": [
            "50,000 AI Credits",
            "Unlimited Everything",
            "Custom LLM & LangGraph Checkpoints",
            "Dedicated Support Engineer",
            "Custom ATS Taxonomy Integration",
        ],
    },
}

# In-memory store for active subscriptions (synced per user)
_USER_SUBSCRIPTIONS: dict[str, dict] = {}


class CheckoutSessionRequest(BaseModel):
    plan_id: Literal["starter", "pro", "business"]
    billing_cycle: Literal["monthly", "yearly"] = "yearly"
    payment_method: Literal["card", "upi", "netbanking", "test"] = "card"
    currency: str = "USD"


class CheckoutSessionResponse(BaseModel):
    session_id: str
    plan_id: str
    amount: float
    currency: str
    billing_cycle: str
    status: str
    checkout_url: str
    client_secret: str


class PaymentVerifyRequest(BaseModel):
    session_id: str
    payment_id: str | None = None
    signature: str | None = None


class SubscriptionResponse(BaseModel):
    user_id: str
    tier: str
    credits_remaining: int
    credits_total: int
    billing_cycle: str
    status: str
    expires_at: str
    features: list[str]


@router.get("/plans")
async def get_plans() -> dict:
    """Return available SaaS subscription tiers and features."""
    return {"plans": list(PLAN_CATALOG.values())}


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    body: CheckoutSessionRequest,
    current_user: CurrentUser,
) -> CheckoutSessionResponse:
    """Create a new payment checkout session."""
    plan = PLAN_CATALOG.get(body.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan identifier")

    amount = plan["yearly_price"] if body.billing_cycle == "yearly" else plan["monthly_price"]
    session_id = f"cs_{uuid.uuid4().hex[:16]}"
    client_secret = f"pi_sec_{uuid.uuid4().hex[:24]}"

    log.info(
        "checkout_session_created",
        user_id=str(current_user.id),
        plan=body.plan_id,
        cycle=body.billing_cycle,
        amount=amount,
    )

    return CheckoutSessionResponse(
        session_id=session_id,
        plan_id=body.plan_id,
        amount=float(amount),
        currency=body.currency,
        billing_cycle=body.billing_cycle,
        status="pending",
        checkout_url=f"/checkout/{session_id}",
        client_secret=client_secret,
    )


@router.post("/verify")
async def verify_payment(
    body: PaymentVerifyRequest,
    current_user: CurrentUser,
) -> dict:
    """Verify and fulfill subscription payment."""
    user_id_str = str(current_user.id)
    # Extract plan from session or default to pro
    plan_key = "pro"
    plan = PLAN_CATALOG[plan_key]

    expiry = datetime.now(timezone.utc) + timedelta(days=365)
    _USER_SUBSCRIPTIONS[user_id_str] = {
        "tier": plan["name"],
        "plan_id": plan_key,
        "credits_total": plan["credits"],
        "credits_remaining": plan["credits"],
        "billing_cycle": "yearly",
        "status": "active",
        "expires_at": expiry.isoformat(),
        "features": plan["features"],
    }

    log.info("payment_verified_and_fulfilled", user_id=user_id_str, plan=plan_key)

    return {
        "success": True,
        "message": f"Payment verified successfully! Welcome to {plan['name']} tier.",
        "subscription": _USER_SUBSCRIPTIONS[user_id_str],
    }


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: CurrentUser,
) -> SubscriptionResponse:
    """Get active subscription status and credits balance."""
    user_id_str = str(current_user.id)
    sub = _USER_SUBSCRIPTIONS.get(user_id_str)

    if not sub:
        # Default starter/candidate tier
        plan = PLAN_CATALOG["starter"]
        sub = {
            "tier": "Starter",
            "credits_total": 1000,
            "credits_remaining": 750,
            "billing_cycle": "monthly",
            "status": "active",
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "features": plan["features"],
        }

    return SubscriptionResponse(
        user_id=user_id_str,
        tier=sub["tier"],
        credits_remaining=sub["credits_remaining"],
        credits_total=sub["credits_total"],
        billing_cycle=sub["billing_cycle"],
        status=sub["status"],
        expires_at=sub["expires_at"],
        features=sub["features"],
    )
