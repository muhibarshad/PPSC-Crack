"""
New Predicted Paper Email — sent to premium users when a prediction is published.
"""

from app.config import settings
from app.services.email.templates.base_layout import wrap_in_layout, PRIMARY


def render_new_prediction_email(
    user_name: str,
    job_type_name: str,
    prediction_title: str,
    prediction_date: str,
    total_questions: int,
    prediction_id: str,
) -> dict[str, str]:
    """Return ``{"subject": ..., "html": ...}`` for the new prediction alert."""

    frontend_url = settings.FRONTEND_URL.rstrip("/")
    prediction_url = f"{frontend_url}/dashboard/predicted-paper?id={prediction_id}"

    body = f"""
    <div class="text-center mb-24">
      <div style="display:inline-block;background-color:#eef2ff;border-radius:50%;
                  width:64px;height:64px;line-height:64px;font-size:28px;">
        🔮
      </div>
    </div>

    <h2 style="margin:0 0 8px;text-align:center;">
      New Predicted Paper Available!
    </h2>
    <p class="text-muted text-center mb-24">
      Hi {user_name}, a fresh AI prediction has been published for your exam.
    </p>

    <div class="card">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:8px 0;"><strong>Job Type</strong></td>
          <td style="padding:8px 0;text-align:right;">
            <span style="background-color:{PRIMARY};color:#fff;padding:4px 12px;
                         border-radius:12px;font-size:13px;font-weight:600;">
              {job_type_name}
            </span>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;">
            <strong>Paper Title</strong>
          </td>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;">
            {prediction_title}
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;">
            <strong>Target Date</strong>
          </td>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;">
            {prediction_date}
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;">
            <strong>Questions</strong>
          </td>
          <td style="padding:8px 0;border-top:1px solid #e5e7eb;text-align:right;">
            {total_questions} MCQs
          </td>
        </tr>
      </table>
    </div>

    <div class="text-center mt-24 mb-16">
      <a href="{prediction_url}" class="btn-primary">
        📝 View Predicted Paper →
      </a>
    </div>

    <div class="card" style="background-color:#eef2ff;">
      <p style="margin:0;font-size:14px;color:#4338ca;">
        💡 <strong>Pro tip:</strong> Practice this predicted paper 2–3 times before your
        exam. Our AI has identified the most likely topics based on 15+ years of pattern
        analysis.
      </p>
    </div>
    """

    return {
        "subject": f"🔮 New Prediction: {job_type_name} — {prediction_title}",
        "html": wrap_in_layout(body, f"New AI-predicted paper for {job_type_name} is ready!"),
    }
