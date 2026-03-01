"""
Password Reset Email — sent when user requests a password reset.
"""

from app.config import settings
from app.services.email.templates.base_layout import wrap_in_layout, PRIMARY


def render_password_reset_email(
    user_name: str,
    reset_url: str,
    expires_in_minutes: int = 60,
) -> dict[str, str]:
    """Return ``{"subject": ..., "html": ...}`` for the password reset email."""

    body = f"""
    <div class="text-center mb-24">
      <div style="display:inline-block;background-color:#fef3c7;border-radius:50%;
                  width:64px;height:64px;line-height:64px;font-size:28px;">
        🔑
      </div>
    </div>

    <h2 style="margin:0 0 8px;text-align:center;">Reset Your Password</h2>
    <p class="text-muted text-center mb-24">
      Hi {user_name}, we received a request to reset your password.
    </p>

    <div class="text-center mb-24">
      <a href="{reset_url}" class="btn-primary">
        🔒 Reset Password
      </a>
    </div>

    <p class="text-muted text-small text-center">
      Or paste this link in your browser:<br/>
      <a href="{reset_url}" style="color:{PRIMARY};word-break:break-all;">
        {reset_url}
      </a>
    </p>

    <hr class="divider" />

    <div class="card" style="background-color:#fef3c7;border-color:#fde68a;">
      <p style="margin:0;font-size:13px;color:#92400e;">
        ⏰ This link expires in <strong>{expires_in_minutes} minutes</strong>.<br/>
        🛡️ If you didn't request this, you can safely ignore this email.
        Your password won't be changed.
      </p>
    </div>
    """

    return {
        "subject": f"🔑 Password Reset — {settings.APP_NAME}",
        "html": wrap_in_layout(body, "Reset your PPSC Crack password"),
    }
