"""
Weekly Current Affairs Digest — sent every Monday.

Summarises the week's top current affairs items with embedded MCQs.
Sent to ALL users (free + premium) as a conversion driver.
"""

from __future__ import annotations

from app.config import settings
from app.services.email.templates.base_layout import wrap_in_layout, PRIMARY, BG_LIGHT


def _render_affair_card(item: dict, index: int) -> str:
    """Render a single current affairs item card with its MCQ."""
    title = item.get("title", "Untitled")
    summary = item.get("summary", "")
    category = item.get("category", "General")
    mcq = item.get("mcq")  # dict with question, options, answer

    mcq_html = ""
    if mcq:
        options_html = ""
        for key in ["a", "b", "c", "d"]:
            opt = mcq.get(f"option_{key}", mcq.get(key, ""))
            if opt:
                options_html += f"""
                <tr>
                  <td style="padding:4px 0;font-size:13px;">
                    <strong>{key.upper()}.</strong> {opt}
                  </td>
                </tr>"""

        mcq_html = f"""
        <div style="margin-top:12px;padding:12px;background-color:#f0fdf4;
                    border-radius:6px;border:1px solid #bbf7d0;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#166534;">
            📝 Quick MCQ
          </p>
          <p style="margin:0 0 8px;font-size:13px;">{mcq.get("question", "")}</p>
          <table role="presentation" cellpadding="0" cellspacing="0">
            {options_html}
          </table>
          <p style="margin:8px 0 0;font-size:12px;color:#6b7280;">
            Answer: <strong>{mcq.get("correct_answer", "").upper()}</strong>
          </p>
        </div>"""

    return f"""
    <div class="card" style="margin-bottom:16px;">
      <div style="display:flex;align-items:center;margin-bottom:8px;">
        <span style="background-color:{PRIMARY};color:#fff;padding:2px 10px;
                     border-radius:10px;font-size:11px;font-weight:600;
                     margin-right:8px;">{category}</span>
        <span style="color:#9ca3af;font-size:12px;">#{index + 1}</span>
      </div>
      <h3 style="margin:0 0 8px;font-size:16px;">{title}</h3>
      <p style="margin:0;font-size:14px;color:#4b5563;">{summary}</p>
      {mcq_html}
    </div>
    """


def render_weekly_digest_email(
    user_name: str,
    week_label: str,
    items: list[dict],
    total_items_count: int,
    is_premium: bool = False,
) -> dict[str, str]:
    """Return ``{"subject": ..., "html": ...}`` for the weekly digest.

    Parameters
    ----------
    items : list[dict]
        Each dict: ``{"title", "summary", "category", "mcq": {...}}``.
        Send 5–7 items; trim on the caller side.
    """

    frontend_url = settings.FRONTEND_URL.rstrip("/")

    items_html = "".join(
        _render_affair_card(item, i) for i, item in enumerate(items)
    )

    upgrade_cta = ""
    if not is_premium:
        upgrade_cta = f"""
        <div class="card" style="background-color:#eef2ff;border-color:#c7d2fe;
                                 text-align:center;margin-top:24px;">
          <p style="margin:0 0 8px;font-size:15px;font-weight:600;color:#4338ca;">
            🚀 Want AI-Predicted Papers?
          </p>
          <p style="margin:0 0 12px;font-size:13px;color:#6366f1;">
            Upgrade to Pro and get predicted exam papers based on 15+ years of
            pattern analysis. Our AI tells you exactly what to study.
          </p>
          <a href="{frontend_url}/dashboard/subscription"
             class="btn-primary" style="font-size:13px;padding:10px 24px;">
            Upgrade to Pro →
          </a>
        </div>"""

    body = f"""
    <h2 style="margin:0 0 4px;">📰 Weekly Current Affairs</h2>
    <p class="text-muted mb-24">{week_label} · {total_items_count} items this week</p>

    <p style="margin:0 0 20px;">
      Hi {user_name}, here are the top current affairs items from this week,
      complete with practice MCQs. Perfect for your PPSC prep!
    </p>

    {items_html}

    <div class="text-center mt-24">
      <a href="{frontend_url}/dashboard/current-affairs" class="btn-primary">
        See All {total_items_count} Items →
      </a>
    </div>

    {upgrade_cta}
    """

    return {
        "subject": f"📰 Weekly PPSC Current Affairs — {week_label}",
        "html": wrap_in_layout(body, f"Your weekly PPSC current affairs digest: {week_label}"),
    }
