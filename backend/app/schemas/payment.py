"""Payment schemas — Stripe + JazzCash checkout, subscription status, webhook."""

from datetime import datetime
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════
# Checkout Session
# ═══════════════════════════════════════════════════════════

class CreateCheckoutSessionRequest(BaseModel):
    """Request to create a Checkout Session (Stripe or JazzCash)."""
    price_id: str
    """Stripe Price ID for the selected tier & interval."""
    provider: str = Field(default="stripe", pattern="^(stripe|jazzcash)$")
    """Payment provider: 'stripe' or 'jazzcash'."""


class CheckoutSessionResponse(BaseModel):
    """Response with the Checkout URL."""
    checkout_url: str
    session_id: str
    provider: str = "stripe"


class JazzCashFormData(BaseModel):
    """JazzCash redirect form data — frontend posts this to JazzCash."""
    action_url: str
    fields: dict[str, str]


# ═══════════════════════════════════════════════════════════
# Subscription Status
# ═══════════════════════════════════════════════════════════

class SubscriptionStatusResponse(BaseModel):
    """Current user's subscription information."""
    is_premium: bool
    subscription_tier: str
    subscription_expires_at: datetime | None = None
    stripe_subscription_id: str | None = None
    cancel_at_period_end: bool = False
    current_period_end: datetime | None = None
    payment_provider: str | None = None

    model_config = {"from_attributes": True}


# ═══════════════════════════════════════════════════════════
# Cancel
# ═══════════════════════════════════════════════════════════

class CancelSubscriptionResponse(BaseModel):
    """Response after requesting cancellation."""
    message: str
    cancel_at_period_end: bool
    current_period_end: datetime | None = None


# ═══════════════════════════════════════════════════════════
# Pricing Plans (for the frontend)
# ═══════════════════════════════════════════════════════════

class PricingPlan(BaseModel):
    tier: str
    name: str
    monthly_price: int
    annual_price: int
    monthly_price_id: str
    annual_price_id: str
    features: list[str]


class PricingPlansResponse(BaseModel):
    plans: list[PricingPlan]
    currency: str = "PKR"
    providers: list[str] = ["stripe", "jazzcash"]
