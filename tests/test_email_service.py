from unittest.mock import MagicMock, patch

from app.config import Settings

SMTP_SETTINGS = Settings(
    secret_key="test-secret-at-least-32-chars-long-yes",
    mongodb_uri="mongodb://localhost:27017",
    mongodb_db_name="test_db",
    email_provider="smtp",
    smtp_host="smtp.example.com",
    smtp_port=587,
    smtp_user="user",
    smtp_password="pass",
    email_from="noreply@example.com",
    email_to_owner="owner@example.com",
    api_url="http://localhost:8000",
    blog_url="http://localhost:3000",
)


def test_send_topic_suggestions_calls_smtp():
    from app.models.topic import TrendingTopic
    from app.services.email_service import send_topic_suggestions

    topic = MagicMock(spec=TrendingTopic)
    topic.id = "topic123"
    topic.subject = "Why Rust is fast"
    topic.brief = "Explore performance benefits."
    topic.source = "hackernews"

    with patch("app.services.email_service.smtplib.SMTP") as MockSMTP:
        server = MockSMTP.return_value.__enter__.return_value
        send_topic_suggestions([topic], SMTP_SETTINGS)

    MockSMTP.assert_called_once_with("smtp.example.com", 587)
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "pass")
    assert server.sendmail.called


def test_send_post_published_calls_smtp():
    from app.models.post import BlogPost
    from app.services.email_service import send_post_published

    post = MagicMock(spec=BlogPost)
    post.title = "My new post"
    post.slug = "my-new-post"
    post.excerpt = "Short summary."
    post.cover_image_url = None

    with patch("app.services.email_service.smtplib.SMTP") as MockSMTP:
        server = MockSMTP.return_value.__enter__.return_value
        send_post_published(post, SMTP_SETTINGS)

    assert server.sendmail.called


def test_send_topic_suggestions_approval_link_in_email():
    from app.models.topic import TrendingTopic
    from app.services.email_service import _topic_card

    topic = MagicMock(spec=TrendingTopic)
    topic.id = "abc123"
    topic.subject = "Test Subject"
    topic.brief = "Test brief."
    topic.source = "github"

    card = _topic_card(topic, SMTP_SETTINGS)
    assert "http://localhost:8000/api/v1/automation/approve/abc123" in card
    assert "Approve" in card
