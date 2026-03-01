"""PPSC Crack — Email Templates Package.

HTML email templates rendered with Python string formatting.
Designed to mirror React Email component patterns on the backend.
"""

from app.services.email.templates.welcome import render_welcome_email
from app.services.email.templates.subscription_confirmation import render_subscription_confirmation_email
from app.services.email.templates.subscription_expiry import render_subscription_expiry_email
from app.services.email.templates.new_prediction import render_new_prediction_email
from app.services.email.templates.weekly_digest import render_weekly_digest_email
from app.services.email.templates.password_reset import render_password_reset_email

__all__ = [
    "render_welcome_email",
    "render_subscription_confirmation_email",
    "render_subscription_expiry_email",
    "render_new_prediction_email",
    "render_weekly_digest_email",
    "render_password_reset_email",
]
