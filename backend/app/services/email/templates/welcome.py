"""
Welcome Email — sent on user registration.

Includes account confirmation link and a quick-start guide.
"""

from app.config import settings
from app.services.email.templates.base_layout import wrap_in_layout, PRIMARY


def render_welcome_email(
    user_name: str,
    confirmation_url: str | None = None,
) -> dict[str, str]:
    """Return ``{"subject": ..., "html": ...}`` for the welcome email."""

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    confirm_section = ""
    if confirmation_url:
        confirm_section = f"""
        <div class="text-center mt-24 mb-24">
          <a href="{confirmation_url}" class="btn-primary">
            ✅ Confirm Your Email
          </a>
        </div>
        <p class="text-muted text-small text-center">
          Or paste this link in your browser:<br/>
          <a href="{confirmation_url}" style="color:{PRIMARY};word-break:break-all;">
            {confirmation_url}
          </a>
        </p>
        <hr class="divider" />
        """

    body = f"""
    <h2 style="margin:0 0 8px;">Welcome aboard, {user_name}! 🎉</h2>
    <p class="text-muted mb-24">
      Your PPSC Crack account is ready. Let's dominate your next exam.
    </p>

    {confirm_section}

    <h3 style="margin:0 0 12px;">🚀 Quick Start Guide</h3>

    <div class="card">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:8px 0;">
            <strong>1️⃣ Select Your Job Type</strong><br/>
            <span class="text-muted text-small">
              Choose the PPSC exam you're targeting so we can personalize your experience.
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;">
            <strong>2️⃣ Explore Past Papers</strong><br/>
            <span class="text-muted text-small">
              Browse 15+ years of categorized past papers with detailed analytics.
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;">
            <strong>3️⃣ Practice Smart</strong><br/>
            <span class="text-muted text-small">
              Take AI-powered practice tests that adapt to your weak areas.
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;">
            <strong>4️⃣ Check Predictions</strong><br/>
            <span class="text-muted text-small">
              Our AI analyzes patterns to predict what's likely coming next.
            </span>
          </td>
        </tr>
      </table>
    </div>

    <div class="text-center mt-24">
      <a href="{frontend_url}/dashboard" class="btn-primary">
        Go to Dashboard →
      </a>
    </div>

    <hr class="divider" />

    <p class="text-muted text-small text-center">
      Questions? Reply to this email or visit our help center.
    </p>
    """

    return {
        "subject": f"Welcome to {settings.APP_NAME} — Let's Crack It! 🚀",
        "html": wrap_in_layout(body, f"Welcome to {settings.APP_NAME}, {user_name}!"),
    }
