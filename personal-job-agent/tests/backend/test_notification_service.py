"""Unit tests for backend.services.notification_service"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from backend.services.notification_service import NotificationService


USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def svc(mock_db):
    return NotificationService(mock_db)


def _make_notif(is_read=False):
    n = MagicMock()
    n.id = uuid.uuid4()
    n.user_id = USER_ID
    n.notification_type = "job_match"
    n.title = "New high-match job"
    n.body = ""
    n.is_read = is_read
    n.priority = "normal"
    n.action_url = ""
    n.metadata_ = {}
    n.created_at = None
    n.updated_at = None
    return n


class TestMarkRead:
    @pytest.mark.asyncio
    async def test_marks_notification_read(self, svc, mock_db):
        notif = _make_notif(is_read=False)
        mock_db.get = AsyncMock(return_value=notif)

        await svc.mark_read(notif.id)

        assert notif.is_read is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_op_when_not_found(self, svc, mock_db):
        mock_db.get = AsyncMock(return_value=None)

        await svc.mark_read(uuid.uuid4())

        mock_db.commit.assert_not_called()


class TestMarkAllRead:
    @pytest.mark.asyncio
    async def test_calls_commit(self, svc, mock_db):
        result_mock = MagicMock()
        result_mock.rowcount = 5
        mock_db.execute = AsyncMock(return_value=result_mock)

        count = await svc.mark_all_read(USER_ID)

        assert count == 5
        mock_db.commit.assert_called_once()


class TestDeleteRead:
    @pytest.mark.asyncio
    async def test_returns_rowcount(self, svc, mock_db):
        result_mock = MagicMock()
        result_mock.rowcount = 3
        mock_db.execute = AsyncMock(return_value=result_mock)

        count = await svc.delete_read(USER_ID)

        assert count == 3
        mock_db.commit.assert_called_once()


class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_and_commits(self, svc, mock_db):
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await svc.create(
            user_id=USER_ID,
            notification_type="job_match",
            title="High match found",
            body="95% match for Senior Python Engineer",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
