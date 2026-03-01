"""
PPSC Crack — Payment Endpoints (Stripe + JazzCash Integration)
================================================================
POST /payments/create-session   — create Checkout session (Stripe or JazzCash)
POST /payments/webhook          — handle Stripe webhook events
POST /payments/jazzcash/ipn     — handle JazzCash IPN callback
GET  /payments/subscription     — current user's subscription status
POST /payments/cancel           — cancel subscription at period end
GET  /payments/plans            — list available pricing plans
"""

from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config import settings
from app.dependencies import DBSession, get_current_user
from app.models.user import User
from app.schemas.payment import (
    CancelSubscriptionResponse,
    CheckoutSessionResponse,
    CreateCheckoutSessionRequest,
    PricingPlan,
    PricingPlansResponse,
    SubscriptionStatusResponse,
)
from app.services.payment_service import (
    cancel_subscription,
    create_checkout_session,
    create_jazzcash_checkout,
    get_subscription_status,
    handle_checkout_completed,
    handle_jazzcash_ipn,
    handle_subscription_deleted,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════
# POST /payments/create-session
# ═══════════════════════════════════════════════════════════

@router.post(
    "/create-session",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Checkout session (Stripe or JazzCash)",
)
async def create_session(
    body: CreateCheckoutSessionRequest,
    db: DBSession,
    user: User = Depends(get_current_user),
):
    """Create a Checkout Session for the selected subscription tier.

    Supports ``provider='stripe'`` (default) or ``provider='jazzcash'``.
    """
    try:
        if body.provider == "jazzcash":
            result = await create_jazzcash_checkout(db, user, body.price_id)
        else:
            result = await create_checkout_session(db, user, body.price_id)
        return CheckoutSessionResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe error creating checkout session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error. Please try again.",
        )
    except Exception as e:
        logger.exception("Unexpected error creating checkout session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session.",
        )


# ═══════════════════════════════════════════════════════════
# POST /payments/webhook
# ═══════════════════════════════════════════════════════════

@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook handler",
)
async def stripe_webhook(request: Request, db: DBSession):
    """Handle incoming Stripe webhook events.

    Verifies the event signature and dispatches to the appropriate handler.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payload",
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature",
        )

    event_type = event["type"]
    logger.info("Stripe webhook received: %s", event_type)

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        await handle_checkout_completed(db, session)

    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        await handle_subscription_deleted(db, subscription)

    elif event_type == "customer.subscription.updated":
        # Handle plan changes / renewals
        subscription = event["data"]["object"]
        logger.info(
            "Subscription updated: %s status=%s",
            subscription.get("id"),
            subscription.get("status"),
        )

    return {"status": "ok"}


# ═══════════════════════════════════════════════════════════
# POST /payments/jazzcash/ipn
# ═══════════════════════════════════════════════════════════

@router.post(
    "/jazzcash/ipn",
    status_code=status.HTTP_200_OK,
    summary="JazzCash IPN callback",
)
async def jazzcash_ipn(request: Request, db: DBSession):
    """Handle JazzCash Instant Payment Notification callback.

    JazzCash POSTs form-encoded data to this URL after payment.
    """
    form = await request.form()
    form_data = dict(form)
    logger.info("JazzCash IPN received: txn=%s", form_data.get("pp_TxnRefNo"))
    result = await handle_jazzcash_ipn(db, form_data)
    return result


# ═══════════════════════════════════════════════════════════
# GET /payments/jazzcash/return
# ═══════════════════════════════════════════════════════════

@router.get(
    "/jazzcash/return",
    status_code=status.HTTP_200_OK,
    summary="JazzCash return URL redirect",
)
async def jazzcash_return(request: Request):
    """JazzCash redirects the user here after payment.

    We parse query params and redirect to the frontend subscription page.
    """
    params = dict(request.query_params)
    response_code = params.get("pp_ResponseCode", "")
    txn_ref = params.get("pp_TxnRefNo", "")
    status_str = "success" if response_code == "000" else "failed"

    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/dashboard/subscription?status={status_str}&txn_ref={txn_ref}&provider=jazzcash"
    )


# ═══════════════════════════════════════════════════════════
# GET /payments/subscription
# ═══════════════════════════════════════════════════════════

@router.get(
    "/subscription",
    response_model=SubscriptionStatusResponse,
    summary="Get current subscription status",
)
async def get_subscription(
    user: User = Depends(get_current_user),
):
    """Return the current user's subscription details."""
    result = await get_subscription_status(user)
    return SubscriptionStatusResponse(**result)


# ═══════════════════════════════════════════════════════════
# POST /payments/cancel
# ═══════════════════════════════════════════════════════════

@router.post(
    "/cancel",
    response_model=CancelSubscriptionResponse,
    summary="Cancel subscription at period end",
)
async def cancel_sub(
    user: User = Depends(get_current_user),
):
    """Cancel the user's subscription at end of the current billing period."""
    try:
        result = await cancel_subscription(user)
        return CancelSubscriptionResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe error cancelling subscription: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Payment provider error. Please try again.",
        )


# ═══════════════════════════════════════════════════════════
# GET /payments/plans
# ═══════════════════════════════════════════════════════════

@router.get(
    "/plans",
    response_model=PricingPlansResponse,
    summary="Get available subscription plans",
)
async def get_plans():
    """Return all subscription tiers with pricing details."""
    plans = [
        PricingPlan(
            tier="basic",
            name="Basic",
            monthly_price=499,
            annual_price=4190,   # 499 × 12 × 0.70 ≈ 4,190 (30% off)
            monthly_price_id=settings.STRIPE_BASIC_MONTHLY_PRICE_ID,
            annual_price_id=settings.STRIPE_BASIC_ANNUAL_PRICE_ID,
            features=[
                "Access to all past papers",
                "Basic AI predictions",
                "Topic-wise study material",
                "Daily current affairs",
                "Practice tests",
            ],
        ),
        PricingPlan(
            tier="pro",
            name="Pro",
            monthly_price=999,
            annual_price=8390,   # 999 × 12 × 0.70 ≈ 8,390 (30% off)
            monthly_price_id=settings.STRIPE_PRO_MONTHLY_PRICE_ID,
            annual_price_id=settings.STRIPE_PRO_ANNUAL_PRICE_ID,
            features=[
                "Everything in Basic",
                "Advanced AI predictions",
                "Priority pattern analytics",
                "Personalized learning path",
                "Predicted paper generation",
                "Premium story-based learning",
                "Priority support",
            ],
        ),
    ]
    return PricingPlansResponse(plans=plans, currency="PKR", providers=["stripe", "jazzcash"])
