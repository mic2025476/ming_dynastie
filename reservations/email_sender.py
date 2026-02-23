from __future__ import annotations

import requests
from django.conf import settings
import html

def send_reservation_confirmation_via_gas(
    *,
    to_email: str,
    edit_cancel_url: str,
    restaurant_name: str = "Ming Dynastie Jannowitzbrücke",
    reservation_date: str | None = None,   # e.g. "17.02.2026"
    reservation_time: str | None = None,   # e.g. "19:30"
    party_size: int | None = None,
    customer_name: str | None = None,
) -> None:
    url = getattr(settings, "GOOGLE_APPS_SCRIPT_EMAIL_WEBHOOK_URL", "")
    if not url:
        raise RuntimeError("GOOGLE_APPS_SCRIPT_EMAIL_WEBHOOK_URL is not set")

    secret = getattr(settings, "GOOGLE_APPS_SCRIPT_EMAIL_WEBHOOK_SECRET", "")

    # ---- Build a short details line for text + HTML ----
    details_parts = []
    if reservation_date:
        details_parts.append(f"Datum: {reservation_date}")
    if reservation_time:
        details_parts.append(f"Uhrzeit: {reservation_time}")
    if party_size is not None:
        details_parts.append(f"Personen: {party_size}")
    if customer_name:
        details_parts.append(f"Name: {customer_name}")

    details_text = "\n".join(details_parts) if details_parts else ""

    subject = "Ihre Reservierung ist bestätigt"

    body_lines = [
        f"Vielen Dank! Ihre Reservierung bei {restaurant_name} ist bestätigt.",
    ]
    if details_text:
        body_lines += ["", details_text]
    body_lines += [
        "",
        "Über folgenden Link können Sie Ihre Reservierung ändern oder stornieren:",
        edit_cancel_url,
        "",
        "Wenn Sie diese Reservierung nicht erstellt haben, ignorieren Sie bitte diese E-Mail.",
    ]

    # Escape for HTML safety
    safe_url = html.escape(edit_cancel_url, quote=True)
    safe_restaurant = html.escape(restaurant_name)
    safe_details_html = ""
    if details_parts:
        safe_details_html = "<ul>" + "".join(
            f"<li>{html.escape(x)}</li>" for x in details_parts
        ) + "</ul>"

    html_body = f"""
      <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.5;">
        <p><b>Vielen Dank!</b> Ihre Reservierung bei <b>{safe_restaurant}</b> ist bestätigt.</p>
        {safe_details_html}
        <p>Über folgenden Link können Sie Ihre Reservierung <b>ändern</b> oder <b>stornieren</b>:</p>
        <p>
          <a href="{safe_url}" style="display:inline-block;padding:10px 14px;border-radius:10px;
             background:#111;color:#fff;text-decoration:none;">
            Reservierung ändern / stornieren
          </a>
        </p>
        <p style="color:#666;font-size:12px;">
          Wenn Sie diese Reservierung nicht erstellt haben, ignorieren Sie bitte diese E-Mail.
        </p>
      </div>
    """

    payload = {
        "secret": secret,
        "to": to_email,
        "subject": subject,
        "body": "\n".join(body_lines),
        "htmlBody": html_body,
        "name": restaurant_name,
    }

    r = requests.post(url, json=payload, timeout=12)

    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"GAS returned non-JSON: {r.status_code} {r.text[:200]}")

    if not data.get("ok"):
        raise RuntimeError(f"GAS failed: {r.status_code} {data}")
    
def send_magic_link_via_gas(*, to_email: str, magic_url: str) -> None:
    url = getattr(settings, "GOOGLE_APPS_SCRIPT_EMAIL_WEBHOOK_URL", "")
    if not url:
        raise RuntimeError("GOOGLE_APPS_SCRIPT_EMAIL_WEBHOOK_URL is not set")

    secret = getattr(settings, "GOOGLE_APPS_SCRIPT_EMAIL_WEBHOOK_SECRET", "")

    payload = {
        "secret": secret,
        "to": to_email,
        "subject": "Ihr Login-Link für Reservierungen",
        "body": (
            "Hier ist Ihr Link, um Ihre Reservierungen zu sehen:\n\n"
            f"{magic_url}\n\n"
            "Wenn Sie diesen Link nicht angefordert haben, ignorieren Sie bitte diese E-Mail."
        ),
        # optional nicer HTML
        "htmlBody": (
            "<p>Hier ist Ihr Link, um Ihre Reservierungen zu sehen:</p>"
            f"<p><a href='{magic_url}'>{magic_url}</a></p>"
            "<p>Wenn Sie diesen Link nicht angefordert haben, ignorieren Sie bitte diese E-Mail.</p>"
        ),
        "name": "Ming Dynastie",
    }

    r = requests.post(url, json=payload, timeout=12)

    # Apps Script often returns 200 even on "errors", so check JSON body
    try:
        data = r.json()
    except Exception:
        raise RuntimeError(f"GAS returned non-JSON: {r.status_code} {r.text[:200]}")

    if not data.get("ok"):
        raise RuntimeError(f"GAS failed: {r.status_code} {data}")
