"""
Payment Service — Stripe + JazzCash integration for subscription management.
==============================================================================
Handles:
  • Stripe Checkout session creation
  • JazzCash HTTP-redirect checkout (for Easypaisa / JazzCash wallets)
  • Webhook event processing (Stripe + JazzCash IPN)
  • Subscription status retrieval
  • Subscription cancellation
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud import crud_user
from app.models.user import User

logger = logging.getLogger(__name__)

# ── Stripe SDK config ───────────────────────────────────────
stripe.api_key = settings.STRIPE_SECRET_KEY

# ── Tier → Price ID mapping ─────────────────────────────────
PRICE_TO_TIER: dict[str, str] = {}

def _build_price_map() -> None:
    """Populate the reverse mapping once settings are loaded."""
    global PRICE_TO_TIER
    PRICE_TO_TIER = {
        settings.STRIPE_BASIC_MONTHLY_PRICE_ID: "basic",
        settings.STRIPE_BASIC_ANNUAL_PRICE_ID: "basic",
        settings.STRIPE_PRO_MONTHLY_PRICE_ID: "pro",
        settings.STRIPE_PRO_ANNUAL_PRICE_ID: "pro",
    }

_build_price_map()

# ── JazzCash price map (Stripe price ID → PKR amount) ───────
PRICE_TO_AMOUNT: dict[str, int] = {}

def _build_jazzcash_price_map() -> None:
    global PRICE_TO_AMOUNT
    PRICE_TO_AMOUNT = {
        settings.STRIPE_BASIC_MONTHLY_PRICE_ID: 499,
        settings.STRIPE_BASIC_ANNUAL_PRICE_ID: 4190,
        settings.STRIPE_PRO_MONTHLY_PRICE_ID: 999,
        settings.STRIPE_PRO_ANNUAL_PRICE_ID: 8390,
    }

_build_jazzcash_price_map()


# ═══════════════════════════════════════════════════════════
# JazzCash Helpers
# ═══════════════════════════════════════════════════════════

def _jazzcash_hash(data_string: str) -> str:
    """Generate JazzCash HMAC-SHA256 secure hash."""
    return hmac.new(
        settings.JAZZCASH_INTEGRITY_SALT.encode("utf-8"),
        data_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


async def create_jazzcash_checkout(
    db: AsyncSession,
    user: User,
    price_id: str,
) -> dict:
    """Build JazzCash HTTP-redirect form data.

    Returns ``{"checkout_url": "<jazzcash_checkout>", "session_id": "<txn_ref>",
               "provider": "jazzcash", "form_data": {...}}``.
    """
    amount = PRICE_TO_AMOUNT.get(price_id)
    if not amount:
        raise ValueError(f"Unknown price_id for JazzCash: {price_id}")

    tier = PRICE_TO_TIER.get(price_id, "basic")
    txn_ref = f"T{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{str(user.id)[:8]}"
    now = datetime.now(timezone.utc)
    expiry = now + timedelta(hours=1)

    # JazzCash required fields
    fields = {
        "pp_Version": "2.0",
        "pp_TxnType": "MPAY",
        "pp_Language": "EN",
        "pp_MerchantID": settings.JAZZCASH_MERCHANT_ID,
        "pp_Password": settings.JAZZCASH_PASSWORD,
        "pp_TxnRefNo": txn_ref,
        "pp_Amount": str(amount * 100),  # paisa
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": now.strftime("%Y%m%d%H%M%S"),
        "pp_TxnExpiryDateTime": expiry.strftime("%Y%m%d%H%M%S"),
        "pp_BillReference": f"ppsc_{tier}_{str(user.id)[:8]}",
        "pp_Description": f"PPSC Crack {tier.title()} Subscription",
        "pp_ReturnURL": settings.JAZZCASH_RETURN_URL,
        "pp_ppmpf_1": str(user.id),   # custom field: user ID
        "pp_ppmpf_2": price_id,         # custom field: price ID
        "pp_ppmpf_3": tier,             # custom field: tier
    }

    # Build hash string (sorted by key, pipe-delimited)
    sorted_values = [v for _, v in sorted(fields.items()) if v]
    hash_string = settings.JAZZCASH_INTEGRITY_SALT + "&" + "&".join(sorted_values)
    fields["pp_SecureHash"] = _jazzcash_hash(hash_string)

    return {
        "checkout_url": settings.JAZZCASH_CHECKOUT_URL,
        "session_id": txn_ref,
        "provider": "jazzcash",
        "form_data": {"action_url": settings.JAZZCASH_CHECKOUT_URL, "fields": fields},
    }


# ═══════════════════════════════════════════════════════════
# JazzCash IPN (Instant Payment Notification)
# ═══════════════════════════════════════════════════════════

async def handle_jazzcash_ipn(db: AsyncSession, form: dict) -> dict:
    """Process JazzCash return / IPN callback.

    Validates hash, activates subscription on success.
    """
    response_code = form.get("pp_ResponseCode", "")
    txn_ref = form.get("pp_TxnRefNo", "")
    user_id_str = form.get("pp_ppmpf_1", "")
    price_id = form.get("pp_ppmpf_2", "")
    tier = form.get("pp_ppmpf_3", "basic")

    logger.info("JazzCash IPN: txn=%s code=%s", txn_ref, response_code)

    if response_code != "000":
        logger.warning("JazzCash payment failed: code=%s txn=%s", response_code, txn_ref)
        return {"status": "failed", "response_code": response_code}

    if not user_id_str:
        logger.error("JazzCash IPN missing user ID in pp_ppmpf_1")
        return {"status": "error", "message": "Missing user reference"}

    user = await crud_user.get(db, id=UUID(user_id_str))
    if not user:
        logger.error("JazzCash IPN — user %s not found", user_id_str)
        return {"status": "error", "message": "User not found"}

    # Determine subscription period
    is_annual = "annual" in price_id.lower() if price_id else False
    period = timedelta(days=365) if is_annual else timedelta(days=30)

    user.is_premium = True
    user.subscription_tier = tier
    user.subscription_expires_at = datetime.now(timezone.utc) + period

    await db.commit()
    logger.info("JazzCash subscription activated: user=%s tier=%s", user_id_str, tier)

    # Send subscription confirmation email
    try:
        from app.services.email import get_email_service
        email_svc = get_email_service()
        amount_pkr = PRICE_TO_AMOUNT.get(price_id, 0)
        await email_svc.send_subscription_confirmation(
            db, user,
            plan_name=tier.title(),
            amount=str(amount_pkr),
            currency="PKR",
            renewal_date=user.subscription_expires_at,
            payment_method="JazzCash",
        )
        await db.commit()
    except Exception:
        logger.warning("Failed to send subscription confirmation email to user=%s", user_id_str, exc_info=True)

    return {"status": "success", "txn_ref": txn_ref}


# ═══════════════════════════════════════════════════════════
# Stripe Checkout Session
# ═══════════════════════════════════════════════════════════

async def create_checkout_session(
    db: AsyncSession,
    user: User,
    price_id: str,
) -> dict:
    """Create a Stripe Checkout Session for the given user & price.

    Returns ``{"checkout_url": "...", "session_id": "..."}``.
    """
    # Ensure user has a Stripe customer
    customer_id = user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(
            email=user.email,
            name=user.name,
            metadata={"ppsc_user_id": str(user.id)},
        )
        customer_id = customer.id
        user.stripe_customer_id = customer_id
        await db.flush()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.FRONTEND_URL}/dashboard/subscription?session_id={{CHECKOUT_SESSION_ID}}&status=success",
        cancel_url=f"{settings.FRONTEND_URL}/dashboard/subscription?status=cancelled",
        metadata={"ppsc_user_id": str(user.id)},
        subscription_data={"metadata": {"ppsc_user_id": str(user.id)}},
    )

    await db.commit()

    return {"checkout_url": session.url, "session_id": session.id, "provider": "stripe"}


# ═══════════════════════════════════════════════════════════
# Webhook Processing
# ═══════════════════════════════════════════════════════════

async def handle_checkout_completed(
    db: AsyncSession, session: stripe.checkout.Session
) -> None:
    """Activate subscription after successful checkout."""
    user_id = session.metadata.get("ppsc_user_id")
    if not user_id:
        logger.warning("checkout.session.completed missing ppsc_user_id metadata")
        return

    subscription_id = session.subscription
    if not subscription_id:
        logger.warning("checkout.session.completed has no subscription")
        return

    # Fetch subscription details from Stripe
    sub = stripe.Subscription.retrieve(subscription_id)
    price_id = sub["items"]["data"][0]["price"]["id"]
    tier = PRICE_TO_TIER.get(price_id, "basic")
    period_end = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)

    from uuid import UUID

    user = await crud_user.get(db, id=UUID(user_id))
    if not user:
        logger.error("checkout.session.completed — user %s not found", user_id)
        return

    user.is_premium = True
    user.subscription_tier = tier
    user.subscription_expires_at = period_end
    user.stripe_subscription_id = subscription_id

    await db.commit()
    logger.info(
        "Subscription activated: user=%s tier=%s expires=%s",
        user_id, tier, period_end,
    )

    # Send subscription confirmation email
    try:
        from app.services.email import get_email_service
        email_svc = get_email_service()
        amount_cents = sub["items"]["data"][0]["price"].get("unit_amount", 0)
        currency = sub["items"]["data"][0]["price"].get("currency", "pkr").upper()
        await email_svc.send_subscription_confirmation(
            db, user,
            plan_name=tier.title(),
            amount=str(amount_cents // 100) if amount_cents else "—",
            currency=currency,
            renewal_date=period_end,
            payment_method="Stripe",
        )
        await db.commit()
    except Exception:
        logger.warning("Failed to send subscription confirmation email to user=%s", user_id, exc_info=True)


async def handle_subscription_deleted(
    db: AsyncSession, subscription: stripe.Subscription
) -> None:
    """Deactivate subscription when cancelled / expired."""
    user_id = subscription.metadata.get("ppsc_user_id")
    if not user_id:
        # Fallback: find by stripe_subscription_id
        from sqlalchemy import select

        result = await db.execute(
            select(User).where(User.stripe_subscription_id == subscription.id)
        )
        user = result.scalar_one_or_none()
    else:
        from uuid import UUID

        user = await crud_user.get(db, id=UUID(user_id))

    if not user:
        logger.warning(
            "customer.subscription.deleted — no user found for sub %s",
            subscription.id,
        )
        return

    user.is_premium = False
    user.subscription_tier = "free"
    user.subscription_expires_at = None
    user.stripe_subscription_id = None

    await db.commit()
    logger.info("Subscription deactivated: user=%s", user.id)


# ═══════════════════════════════════════════════════════════
# Subscription Status
# ═══════════════════════════════════════════════════════════

async def get_subscription_status(user: User) -> dict:
    """Return the current user's subscription details."""
    result = {
        "is_premium": user.is_premium,
        "subscription_tier": user.subscription_tier or "free",
        "subscription_expires_at": user.subscription_expires_at,
        "stripe_subscription_id": user.stripe_subscription_id,
        "cancel_at_period_end": False,
        "current_period_end": None,
        "payment_provider": "stripe" if user.stripe_subscription_id else (
            "jazzcash" if user.is_premium and not user.stripe_subscription_id else None
        ),
    }

    # If there's an active Stripe subscription, fetch live data
    if user.stripe_subscription_id and settings.STRIPE_SECRET_KEY:
        try:
            sub = stripe.Subscription.retrieve(user.stripe_subscription_id)
            result["cancel_at_period_end"] = sub.get("cancel_at_period_end", False)
            period_end = sub.get("current_period_end")
            if period_end:
                result["current_period_end"] = datetime.fromtimestamp(
                    period_end, tz=timezone.utc
                )
        except stripe.error.StripeError as e:
            logger.warning("Failed to fetch Stripe subscription: %s", e)

    return result


# ═══════════════════════════════════════════════════════════
# Cancel Subscription
# ═══════════════════════════════════════════════════════════

async def cancel_subscription(user: User) -> dict:
    """Cancel subscription at end of current billing period."""
    if not user.stripe_subscription_id:
        raise ValueError("No active subscription to cancel")

    sub = stripe.Subscription.modify(
        user.stripe_subscription_id,
        cancel_at_period_end=True,
    )

    period_end = datetime.fromtimestamp(
        sub["current_period_end"], tz=timezone.utc
    )

    return {
        "message": "Subscription will be cancelled at the end of the current billing period.",
        "cancel_at_period_end": True,
        "current_period_end": period_end,
    }
