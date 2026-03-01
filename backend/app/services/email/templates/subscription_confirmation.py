"""
Subscription Confirmation Email — sent when payment succeeds.

Shows plan name, amount paid, and renewal date.
"""

from datetime import datetime

from app.config import settings
from app.services.email.templates.base_layout import wrap_in_layout, SUCCESS


def render_subscription_confirmation_email(
    user_name: str,
    plan_name: str,
    amount: str,
    currency: str = "PKR",
    renewal_date: datetime | str | None = None,
    payment_method: str = "Card",
) -> dict[str, str]:
    """Return ``{"subject": ..., "html": ...}`` for subscription confirmation."""

    frontend_url = settings.FRONTEND_URL.rstrip("/")

    renewal_str = ""
    if renewal_date:
        if isinstance(renewal_date, datetime):
            renewal_str = renewal_date.strftime("%B %d, %Y")
        else:
            renewal_str = str(renewal_date)

    body = f"""
    <div class="text-center mb-24">
      <div style="display:inline-block;background-color:#ecfdf5;border-radius:50%;
                  width:64px;height:64px;line-height:64px;font-size:28px;">
        ✅
      </div>
    </div>

    <h2 style="margin:0 0 8px;text-align:center;">Payment Confirmed!</h2>
    <p class="text-muted text-center mb-24">
      Thank you, {user_name}! Your subscription is now active.
    </p>

    <div class="card">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:8px 0;"><strong>Plan</strong></td>
          <td style="padding:8px 0;text-align:right;">
            <span style="background-color:{SUCCESS};color:#fff;padding:4px 12px;
                         border-radius:12px;font-size:13px;font-weight:600;">
              {plan_name}
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;">
            <strong>Amount Paid</strong>
          </td>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;">
            {currency} {amount}
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;">
            <strong>Payment Method</strong>
          </td>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;">
            {payment_method}
          </td>
        </tr>
        {"<tr><td style='padding:8px 0;border-top:1px solid #e5e7eb;'><strong>Next Renewal</strong></td><td style='padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;'>" + renewal_str + "</td></tr>" if renewal_str else ""}
      </table>
    </div>

    <h3 style="margin:24px 0 12px;">🔓 What's Unlocked</h3>
    <div class="card">
      <ul style="margin:0;padding-left:20px;color:#374151;">
        <li style="padding:4px 0;">AI-Predicted Papers for your selected job types</li>
        <li style="padding:4px 0;">Advanced pattern analytics & topic deep-dives</li>
        <li style="padding:4px 0;">Unlimited practice tests with detailed explanations</li>
        <li style="padding:4px 0;">Priority access to new features</li>
      </ul>
    </div>

    <div class="text-center mt-24">
      <a href="{frontend_url}/dashboard" class="btn-primary">
        Start Studying →
      </a>
    </div>

    <hr class="divider" />

    <p class="text-muted text-small text-center">
      Manage your subscription anytime from
      <a href="{frontend_url}/dashboard/subscription">your account settings</a>.
    </p>
    """

    return {
        "subject": f"🎉 {plan_name} Plan Activated — {settings.APP_NAME}",
        "html": wrap_in_layout(body, f"Your {plan_name} subscription is active!"),
    }
