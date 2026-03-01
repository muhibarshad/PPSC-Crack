"""
Subscription Expiry Warning Email — sent 3 days before expiry.

Includes a renewal link to maintain uninterrupted access.
"""

from datetime import datetime

from app.config import settings
from app.services.email.templates.base_layout import wrap_in_layout, WARNING


def render_subscription_expiry_email(
    user_name: str,
    plan_name: str,
    expiry_date: datetime | str,
    days_remaining: int = 3,
) -> dict[str, str]:
    """Return ``{"subject": ..., "html": ...}`` for the expiry warning."""

    frontend_url = settings.FRONTEND_URL.rstrip("/")

    if isinstance(expiry_date, datetime):
        expiry_str = expiry_date.strftime("%B %d, %Y")
    else:
        expiry_str = str(expiry_date)

    urgency_color = "#ef4444" if days_remaining <= 1 else WARNING

    body = f"""
    <div class="text-center mb-24">
      <div style="display:inline-block;background-color:#fffbeb;border-radius:50%;
                  width:64px;height:64px;line-height:64px;font-size:28px;">
        ⚠️
      </div>
    </div>

    <h2 style="margin:0 0 8px;text-align:center;">
      Your Subscription Expires Soon
    </h2>
    <p class="text-muted text-center mb-16">
      Hi {user_name}, your <strong>{plan_name}</strong> plan expires in
      <span style="color:{urgency_color};font-weight:700;">
        {days_remaining} day{"s" if days_remaining != 1 else ""}
      </span>.
    </p>

    <div class="card" style="border-color:{urgency_color};border-width:2px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:8px 0;"><strong>Current Plan</strong></td>
          <td style="padding:8px 0;text-align:right;">{plan_name}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;">
            <strong>Expiry Date</strong>
          </td>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;
                     color:{urgency_color};font-weight:600;">
            {expiry_str}
          </td>
        </tr>
      </table>
    </div>

    <h3 style="margin:24px 0 12px;">🚫 What You'll Lose</h3>
    <div class="card">
      <ul style="margin:0;padding-left:20px;color:#374151;">
        <li style="padding:4px 0;">AI-Predicted exam papers</li>
        <li style="padding:4px 0;">Advanced pattern analytics</li>
        <li style="padding:4px 0;">Unlimited practice tests</li>
        <li style="padding:4px 0;">Priority feature access</li>
      </ul>
    </div>

    <div class="text-center mt-24 mb-16">
      <a href="{frontend_url}/dashboard/subscription" class="btn-primary">
        🔄 Renew Now →
      </a>
    </div>

    <p class="text-muted text-small text-center">
      If you don't renew, your account will revert to the Free tier on {expiry_str}.
      You won't lose any data — just premium features.
    </p>
    """

    subject_prefix = "⚠️" if days_remaining > 1 else "🚨"
    return {
        "subject": f"{subject_prefix} Your {plan_name} plan expires in {days_remaining} day{'s' if days_remaining != 1 else ''} — {settings.APP_NAME}",
        "html": wrap_in_layout(body, f"Your {plan_name} subscription expires in {days_remaining} days."),
    }
