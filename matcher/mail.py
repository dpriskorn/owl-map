"""Send email to admins to about errors or other notworthy things."""

import pprint
import smtplib
import sys
import traceback
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

import requests

from matcher.config import config as app_config
from matcher import wikidata_api


def send_mail(
    subject: str, body: str, config: dict | None = None
) -> None:
    """Send an email to admins, catch and ignore exceptions."""
    try:
        send_mail_main(subject, body, config=config)
    except smtplib.SMTPDataError:
        pass  # ignore email errors


def send_mail_main(
    subject: str, body: str, config: dict | None = None
) -> None:
    """Send an email to admins."""
    cfg = config if config is not None else app_config

    mail_to = cfg["ADMIN_EMAIL"]
    mail_from = cfg["MAIL_FROM"]
    msg = MIMEText(body, "plain", "UTF-8")

    msg["Subject"] = subject
    msg["To"] = mail_to
    msg["From"] = mail_from
    msg["Date"] = formatdate()
    msg["Message-ID"] = make_msgid()
    extra_mail_headers: list[tuple[str, str]] = cfg.get("MAIL_HEADERS", [])
    for key, value in extra_mail_headers:
        assert key not in msg
        msg[key] = value

    s = smtplib.SMTP(cfg["SMTP_HOST"])
    s.sendmail(mail_from, [mail_to], msg.as_string())
    s.quit()


def error_mail(
    subject: str,
    data: str,
    r: requests.Response,
    user: str | None = None,
    request_url: str | None = None,
) -> None:
    """Error mail."""
    body = f"""
remote URL: {r.url}
status code: {r.status_code}

request data:
{data}

status code: {r.status_code}
content-type: {r.headers["content-type"]}

reply:
{r.text}
"""

    if request_url:
        body = f"site URL: {request_url}\nuser: {user or 'unknown'}\n" + body

    send_mail(subject, body)


def open_changeset_error(
    session_id: int,
    changeset: str,
    r: requests.Response,
    username: str | None = None,
) -> None:
    """Send error mail when failing to open a changeset."""
    body = f"""
user: {username or 'unknown'}
page: {r.url}

message user: https://www.openstreetmap.org/message/new/{username or 'unknown'}

sent:

{changeset}

reply:

{r.text}

"""

    send_mail("error creating changeset", body)


def send_traceback(info, prefix="osm-wikidata"):
    exception_name = sys.exc_info()[0].__name__
    subject = f"{prefix} error: {exception_name}"
    body = info + "\n" + traceback.format_exc()
    send_mail(subject, body)


def datavalue_missing(field: str, entity: wikidata_api.EntityType) -> None:
    """Send an email for a missing datavalue."""
    qid = entity["title"]
    body = f"https://www.wikidata.org/wiki/{qid}\n\n{pprint.pformat(entity)}"

    subject = f"{qid}: datavalue missing in {field}"
    send_mail(subject, body)
