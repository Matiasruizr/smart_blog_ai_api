import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import Settings
from app.models.post import BlogPost
from app.models.topic import TrendingTopic


def _send_via_smtp(to: str, subject: str, html_body: str, settings: Settings) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.email_from, to, msg.as_string())


def _send_via_sendgrid(to: str, subject: str, html_body: str, settings: Settings) -> None:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(
        from_email=settings.email_from,
        to_emails=to,
        subject=subject,
        html_content=html_body,
    )
    SendGridAPIClient(settings.sendgrid_api_key).send(message)


def _send_via_resend(to: str, subject: str, html_body: str, settings: Settings) -> None:
    import resend

    resend.api_key = settings.resend_api_key
    resend.Emails.send({
        "from": settings.email_from,
        "to": to,
        "subject": subject,
        "html": html_body,
    })


def _dispatch(to: str, subject: str, html_body: str, settings: Settings) -> None:
    if settings.email_provider == "sendgrid":
        _send_via_sendgrid(to, subject, html_body, settings)
    elif settings.email_provider == "resend":
        _send_via_resend(to, subject, html_body, settings)
    else:
        _send_via_smtp(to, subject, html_body, settings)


def _topic_card(topic: TrendingTopic, settings: Settings) -> str:
    approve_url = f"{settings.api_url}/api/v1/automation/approve/{topic.id}"
    source_badge = (
        "🔶 Hacker News" if topic.source == "hackernews" else "🐙 GitHub Trending"
    )
    return f"""
    <div style="border:1px solid #e2e8f0;border-radius:8px;padding:20px;margin-bottom:16px;font-family:sans-serif;">
      <p style="margin:0 0 4px;font-size:12px;color:#64748b;">{source_badge}</p>
      <h3 style="margin:0 0 8px;font-size:18px;color:#1e293b;">{topic.subject}</h3>
      <p style="margin:0 0 16px;color:#475569;line-height:1.6;">{topic.brief}</p>
      <a href="{approve_url}"
         style="display:inline-block;background:#7c3aed;color:#fff;padding:10px 20px;
                border-radius:6px;text-decoration:none;font-weight:600;font-size:14px;">
        ✅ Approve &amp; Generate Post
      </a>
    </div>"""


def send_topic_suggestions(topics: list[TrendingTopic], settings: Settings) -> None:
    cards = "".join(_topic_card(t, settings) for t in topics)
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:24px;background:#f8fafc;font-family:sans-serif;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:32px;">
    <h1 style="font-size:24px;color:#1e293b;margin-bottom:8px;">Your blog topics for this cycle</h1>
    <p style="color:#64748b;margin-bottom:24px;">
      Click <strong>Approve &amp; Generate Post</strong> on the topic you'd like to publish next.
      Claude will generate a full draft automatically.
    </p>
    {cards}
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="font-size:12px;color:#94a3b8;">Smart Blog AI · Automated content pipeline</p>
  </div>
</body>
</html>"""

    _dispatch(
        to=settings.email_to_owner,
        subject="📝 Your blog topic suggestions are ready",
        html_body=html,
        settings=settings,
    )


def send_post_published(post: BlogPost, settings: Settings) -> None:
    post_url = f"{settings.blog_url}/blog/{post.slug}"
    cover_html = (
        f'<img src="{post.cover_image_url}" alt="Cover" '
        f'style="width:100%;border-radius:8px;margin-bottom:20px;">'
        if post.cover_image_url
        else ""
    )
    html = f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:24px;background:#f8fafc;font-family:sans-serif;">
  <div style="max-width:600px;margin:0 auto;background:#fff;border-radius:12px;padding:32px;">
    <p style="font-size:12px;color:#64748b;margin-bottom:16px;">New post published</p>
    {cover_html}
    <h1 style="font-size:24px;color:#1e293b;margin-bottom:12px;">{post.title}</h1>
    <p style="color:#475569;line-height:1.6;margin-bottom:24px;">{post.excerpt}</p>
    <a href="{post_url}"
       style="display:inline-block;background:#7c3aed;color:#fff;padding:12px 24px;
              border-radius:6px;text-decoration:none;font-weight:600;">
      Read Post →
    </a>
    <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
    <p style="font-size:12px;color:#94a3b8;">Smart Blog AI · Automated content pipeline</p>
  </div>
</body>
</html>"""

    _dispatch(
        to=settings.email_to_owner,
        subject=f"🚀 New post published: {post.title}",
        html_body=html,
        settings=settings,
    )
