"""
Shared email layout — base wrapper used by all email templates.

Implements a clean, responsive email design inspired by React Email components.
All templates call ``wrap_in_layout(body_html, preview_text)`` to get a
fully styled, production-ready HTML email.
"""

from app.config import settings

# ── Brand colours ────────────────────────────────────────────
PRIMARY = "#6366f1"         # Indigo-500
PRIMARY_DARK = "#4f46e5"    # Indigo-600
BG_LIGHT = "#f9fafb"        # Gray-50
BG_WHITE = "#ffffff"
TEXT_PRIMARY = "#111827"     # Gray-900
TEXT_SECONDARY = "#6b7280"  # Gray-500
TEXT_MUTED = "#9ca3af"      # Gray-400
BORDER = "#e5e7eb"          # Gray-200
SUCCESS = "#10b981"         # Emerald-500
WARNING = "#f59e0b"         # Amber-500


def wrap_in_layout(body_html: str, preview_text: str = "") -> str:
    """Wrap email body in the shared responsive layout."""
    frontend_url = settings.FRONTEND_URL.rstrip("/")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="X-UA-Compatible" content="IE=edge" />
  <title>{settings.APP_NAME}</title>
  <!--[if mso]>
  <style>table,td,div,p {{font-family: Arial, sans-serif;}}</style>
  <![endif]-->
  <style>
    /* Reset */
    body, table, td, p, a, li, blockquote {{
      -webkit-text-size-adjust: 100%;
      -ms-text-size-adjust: 100%;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                   'Helvetica Neue', Arial, sans-serif;
      background-color: {BG_LIGHT};
      color: {TEXT_PRIMARY};
      line-height: 1.6;
    }}
    .container {{
      max-width: 600px;
      margin: 0 auto;
      background-color: {BG_WHITE};
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .header {{
      background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
      padding: 32px 40px;
      text-align: center;
    }}
    .header h1 {{
      color: #ffffff;
      font-size: 24px;
      font-weight: 700;
      margin: 0;
      letter-spacing: -0.5px;
    }}
    .header p {{
      color: rgba(255,255,255,0.85);
      font-size: 14px;
      margin-top: 4px;
    }}
    .body-content {{
      padding: 40px;
    }}
    .btn-primary {{
      display: inline-block;
      background-color: {PRIMARY};
      color: #ffffff !important;
      text-decoration: none;
      padding: 14px 32px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 15px;
      text-align: center;
      transition: background-color 0.2s;
    }}
    .btn-primary:hover {{
      background-color: {PRIMARY_DARK};
    }}
    .btn-secondary {{
      display: inline-block;
      background-color: {BG_LIGHT};
      color: {TEXT_PRIMARY} !important;
      text-decoration: none;
      padding: 12px 28px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 14px;
      border: 1px solid {BORDER};
    }}
    .card {{
      background-color: {BG_LIGHT};
      border: 1px solid {BORDER};
      border-radius: 8px;
      padding: 20px;
      margin: 16px 0;
    }}
    .divider {{
      border: none;
      border-top: 1px solid {BORDER};
      margin: 24px 0;
    }}
    .footer {{
      padding: 24px 40px;
      text-align: center;
      background-color: {BG_LIGHT};
      border-top: 1px solid {BORDER};
    }}
    .footer p {{
      color: {TEXT_MUTED};
      font-size: 12px;
      margin: 4px 0;
    }}
    .footer a {{
      color: {TEXT_SECONDARY};
      text-decoration: underline;
    }}
    .text-muted {{ color: {TEXT_SECONDARY}; }}
    .text-small {{ font-size: 13px; }}
    .text-center {{ text-align: center; }}
    .mt-16 {{ margin-top: 16px; }}
    .mt-24 {{ margin-top: 24px; }}
    .mb-16 {{ margin-bottom: 16px; }}
    .mb-24 {{ margin-bottom: 24px; }}
    /* Preview text hack */
    .preview-text {{
      display: none;
      font-size: 1px;
      color: {BG_LIGHT};
      line-height: 1px;
      max-height: 0;
      max-width: 0;
      opacity: 0;
      overflow: hidden;
    }}
    @media only screen and (max-width: 620px) {{
      .container {{ margin: 0 !important; border-radius: 0 !important; }}
      .body-content {{ padding: 24px 20px !important; }}
      .header {{ padding: 24px 20px !important; }}
      .footer {{ padding: 20px !important; }}
    }}
  </style>
</head>
<body style="margin:0; padding:20px 0; background-color:{BG_LIGHT};">
  <!-- Preview text -->
  <div class="preview-text">{preview_text}</div>

  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center">
        <div class="container">
          <!-- Header -->
          <div class="header">
            <h1>📚 {settings.APP_NAME}</h1>
            <p>AI-Powered Exam Domination</p>
          </div>

          <!-- Body -->
          <div class="body-content">
            {body_html}
          </div>

          <!-- Footer -->
          <div class="footer">
            <p>© 2026 {settings.APP_NAME}. All rights reserved.</p>
            <p>
              <a href="{frontend_url}/dashboard">Dashboard</a> ·
              <a href="{frontend_url}/dashboard/subscription">Manage Subscription</a> ·
              <a href="{frontend_url}/email-preferences">Email Preferences</a>
            </p>
            <p class="mt-16">
              You received this email because you have an account at {settings.APP_NAME}.
              <br />
              <a href="{frontend_url}/email-preferences">Unsubscribe from this type of email</a>
            </p>
          </div>
        </div>
      </td>
    </tr>
  </table>
</body>
</html>"""
