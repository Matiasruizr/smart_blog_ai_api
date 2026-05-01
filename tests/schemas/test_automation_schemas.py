from datetime import datetime, timezone

from app.schemas.automation import GenerateRequest, SchedulerStatusResponse, TrendingTopicResponse


def test_generate_request_defaults():
    req = GenerateRequest(
        subject="Why MCP is changing AI integrations",
        brief="Cover the protocol, real use cases, and adoption curve.",
    )
    assert req.tags == []
    assert req.auto_publish is False


def test_trending_topic_response_from_attributes():
    class FakeTopic:
        id = "topic123"
        subject = "Top repos this week"
        brief = "Summary of trending repos."
        tags = ["open-source"]
        source = "github"
        status = "pending"
        created_at = datetime.now(timezone.utc)

    response = TrendingTopicResponse.model_validate(FakeTopic())
    assert response.id == "topic123"
    assert response.source == "github"
    assert response.status == "pending"


def test_scheduler_status_response_defaults():
    status = SchedulerStatusResponse(enabled=True, interval_hours=48)
    assert status.next_run_at is None
    assert status.last_run_at is None
