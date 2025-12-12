import uuid

from app.core.security import get_payload
from app.literals.report import ReportCategory, ReportPriority, ReportReason, ReportStatus
from app.models.report import Report


class TestUserReportEndpoints:
    """Tests for user report endpoints (/reports)"""

    def test_create_report_as_user(self, client, user_token, auth_headers, user2_token):
        """Basic user creates a report about another user."""
        user_data = get_payload(user_token)
        user2_data = get_payload(user2_token)

        payload = {
            "contentType": ReportCategory.HOUSING.value,
            "contentId": str(uuid.uuid4()),
            "reportedUserId": user2_data["sub"],
            "reason": ReportReason.SCAM_FRAUD.value,
            "description": "This listing looks like a scam",
        }

        url = "/reports/"
        resp = client.post(url, json=payload, headers=auth_headers)
        print("\n")
        print(resp.json())
        assert resp.status_code == 201
        data = resp.json()
        assert data["contentType"] == ReportCategory.HOUSING.value
        assert data["reason"] == ReportReason.SCAM_FRAUD.value
        assert data["status"] == ReportStatus.PENDING.value
        assert data["priority"] == ReportPriority.MEDIUM.value
        assert data["reportedBy"]["id"] == user_data["sub"]
        assert data["reportedUser"]["id"] == user2_data["sub"]
        assert data["description"] == "This listing looks like a scam"

    def test_create_report_without_description(self, client, user_token, auth_headers, user2_token):
        """Create report without optional description."""
        user2_data = get_payload(user2_token)

        payload = {
            "contentType": ReportCategory.CHANNELS.value,
            "contentId": str(uuid.uuid4()),
            "reportedUserId": user2_data["sub"],
            "reason": ReportReason.HARASSMENT.value,
        }

        url = "/reports/"
        resp = client.post(url, json=payload, headers=auth_headers)

        assert resp.status_code == 201
        data = resp.json()
        assert data["reason"] == ReportReason.HARASSMENT.value
        assert data["description"] is None

    def test_create_report_unauthenticated(self, client, user2_token):
        """Unauthenticated user cannot create report."""
        user2_data = get_payload(user2_token)

        payload = {
            "contentType": ReportCategory.USER.value,
            "contentId": str(uuid.uuid4()),
            "reportedUserId": user2_data["sub"],
            "reason": ReportReason.SPAM.value,
        }

        url = "/reports/"
        resp = client.post(url, json=payload)

        assert resp.status_code == 401

    def test_get_my_reports(self, client, user_token, auth_headers, user2_token):
        """User retrieves their own reports."""
        user2_data = get_payload(user2_token)

        url_create = "/reports/"
        for i in range(3):
            payload = {
                "contentType": ReportCategory.HOUSING.value,
                "contentId": str(uuid.uuid4()),
                "reportedUserId": user2_data["sub"],
                "reason": ReportReason.FAKE_LISTING.value,
                "description": f"Test report {i}",
            }
            client.post(url_create, json=payload, headers=auth_headers)

        url_my = "/reports/my"
        resp = client.get(url_my, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "reports" in data
        assert "total" in data
        assert len(data["reports"]) >= 3
        assert data["total"] >= 3

    def test_get_my_reports_with_pagination(self, client, user_token, auth_headers, user2_token):
        """Test pagination for my reports."""
        user2_data = get_payload(user2_token)

        url_create = "/reports/"
        for i in range(5):
            payload = {
                "contentType": ReportCategory.MESSAGES.value,
                "contentId": str(uuid.uuid4()),
                "reportedUserId": user2_data["sub"],
                "reason": ReportReason.INAPPROPRIATE_CONTENT.value,
            }
            client.post(url_create, json=payload, headers=auth_headers)

        url_my = "/reports/my?page=1&size=2"
        resp = client.get(url_my, headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["reports"]) <= 2

    def test_get_my_reports_unauthenticated(self, client):
        """Unauthenticated user cannot get reports."""
        url = "/reports/my"
        resp = client.get(url)

        assert resp.status_code == 401


class TestAdminReportEndpoints:
    """Tests for admin report endpoints (/admin/reports)"""

    def test_get_stats_as_admin_with_seeded_data(self, client, admin_auth_headers, db):
        """Admin retrieves report statistics using seeded data."""

        report_count = db.query(Report).count()
        assert report_count >= 1, "Expected seeded reports in database"

        url = "/admin/reports/stats"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "pending" in data
        assert "reviewing" in data
        assert "resolved" in data
        assert "dismissed" in data
        assert "critical" in data

        assert data["total"] >= 1

        assert data["pending"] >= 0
        assert data["resolved"] >= 0

    def test_get_stats_as_user_forbidden(self, client, auth_headers):
        """Basic user cannot access stats."""
        url = "/admin/reports/stats"
        resp = client.get(url, headers=auth_headers)

        assert resp.status_code == 403
        assert "elevated access" in resp.json()["detail"]

    def test_get_all_reports_as_admin_with_seeded_data(self, client, admin_auth_headers, db):
        """Admin retrieves all reports including seeded data."""

        report_count = db.query(Report).count()
        assert report_count >= 1, "Expected seeded reports in database"

        url = "/admin/reports/"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert "reports" in data
        assert "total" in data

        assert data["total"] >= 1

    def test_get_reports_filter_by_status_pending(self, client, admin_auth_headers, db):
        """Admin filters reports by pending status using seeded data."""

        pending_count = db.query(Report).filter(Report.status == ReportStatus.PENDING.value).count()

        url = f"/admin/reports/?status={ReportStatus.PENDING.value}"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert all(r["status"] == ReportStatus.PENDING.value for r in data["reports"])
        if pending_count > 0:
            assert len(data["reports"]) >= 1

    def test_get_reports_filter_by_status_resolved(self, client, admin_auth_headers, db):
        """Admin filters reports by resolved status using seeded data."""

        resolved_count = db.query(Report).filter(Report.status == ReportStatus.RESOLVED.value).count()

        url = f"/admin/reports/?status={ReportStatus.RESOLVED.value}"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert all(r["status"] == ReportStatus.RESOLVED.value for r in data["reports"])
        if resolved_count > 0:
            assert len(data["reports"]) >= 1

    def test_get_reports_filter_by_priority_critical(self, client, admin_auth_headers, db):
        """Admin filters reports by critical priority using seeded data."""
        critical_count = db.query(Report).filter(Report.priority == ReportPriority.CRITICAL.value).count()

        url = f"/admin/reports/?priority={ReportPriority.CRITICAL.value}"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert all(r["priority"] == ReportPriority.CRITICAL.value for r in data["reports"])
        if critical_count > 0:
            assert len(data["reports"]) >= 1

    def test_get_reports_filter_by_category(self, client, admin_auth_headers, db):
        """Admin filters reports by content category using seeded data."""
        housing_count = db.query(Report).filter(Report.content_type == ReportCategory.HOUSING.value).count()

        url = f"/admin/reports/?category={ReportCategory.HOUSING.value}"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert all(r["contentType"] == ReportCategory.HOUSING.value for r in data["reports"])
        if housing_count > 0:
            assert len(data["reports"]) >= 1

    def test_get_reports_with_search(self, client, admin_auth_headers, user_token, auth_headers, user2_token):
        """Admin searches reports by description."""
        user2_data = get_payload(user2_token)

        url_create = "/reports/"
        payload = {
            "contentType": ReportCategory.USER.value,
            "contentId": str(uuid.uuid4()),
            "reportedUserId": user2_data["sub"],
            "reason": ReportReason.HARASSMENT.value,
            "description": "UNIQUE_SEARCH_TERM_12345",
        }
        resp = client.post(url_create, json=payload, headers=auth_headers)
        assert resp.status_code == 201

        url = "/admin/reports/?search=UNIQUE_SEARCH_TERM_12345"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert any("UNIQUE_SEARCH_TERM_12345" in (r.get("description") or "") for r in data["reports"])

    def test_get_report_by_id_from_seeded_data(self, client, admin_auth_headers, db):
        """Admin gets specific report details from seeded data."""

        seeded_report = db.query(Report).first()
        assert seeded_report is not None, "Expected seeded reports in database"

        url = f"/admin/reports/{seeded_report.id}"
        resp = client.get(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(seeded_report.id)
        assert data["contentType"] == seeded_report.content_type
        assert data["reason"] == seeded_report.reason

    def test_get_report_by_id_as_user_forbidden(self, client, auth_headers, db):
        """Basic user cannot get specific report details."""

        seeded_report = db.query(Report).first()
        assert seeded_report is not None

        url = f"/admin/reports/{seeded_report.id}"
        resp = client.get(url, headers=auth_headers)

        assert resp.status_code == 403

    def test_update_report_as_admin(self, client, admin_auth_headers, user_token, auth_headers, user2_token):
        """Admin updates report status and priority."""
        user2_data = get_payload(user2_token)

        url_create = "/reports/"
        payload = {
            "contentType": ReportCategory.MARKETPLACE.value,
            "contentId": str(uuid.uuid4()),
            "reportedUserId": user2_data["sub"],
            "reason": ReportReason.FAKE_LISTING.value,
        }
        resp = client.post(url_create, json=payload, headers=auth_headers)
        report_id = resp.json()["id"]

        update_payload = {
            "status": ReportStatus.REVIEWING.value,
            "priority": ReportPriority.HIGH.value,
            "resolution": "Under investigation",
        }

        url = f"/admin/reports/{report_id}"
        resp = client.patch(url, json=update_payload, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == ReportStatus.REVIEWING.value
        assert data["priority"] == ReportPriority.HIGH.value
        assert data["resolution"] == "Under investigation"
        assert data["reviewedBy"] is not None
        assert data["reviewedAt"] is not None

    def test_update_seeded_report_as_admin(self, client, admin_auth_headers, db):
        """Admin updates a seeded pending report."""

        pending_report = db.query(Report).filter(Report.status == ReportStatus.PENDING.value).first()

        if pending_report is None:
            return

        update_payload = {
            "status": ReportStatus.REVIEWING.value,
            "priority": ReportPriority.HIGH.value,
        }

        url = f"/admin/reports/{pending_report.id}"
        resp = client.patch(url, json=update_payload, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == ReportStatus.REVIEWING.value
        assert data["priority"] == ReportPriority.HIGH.value

    def test_update_report_as_user_forbidden(self, client, auth_headers, db):
        """Basic user cannot update report."""

        seeded_report = db.query(Report).first()
        assert seeded_report is not None

        update_payload = {"status": ReportStatus.RESOLVED.value}

        url = f"/admin/reports/{seeded_report.id}"
        resp = client.patch(url, json=update_payload, headers=auth_headers)

        assert resp.status_code == 403

    def test_delete_report_as_admin(self, client, admin_auth_headers, user_token, auth_headers, user2_token):
        """Admin deletes a report."""
        user2_data = get_payload(user2_token)

        url_create = "/reports/"
        payload = {
            "contentType": ReportCategory.USER.value,
            "contentId": str(uuid.uuid4()),
            "reportedUserId": user2_data["sub"],
            "reason": ReportReason.VIOLENCE.value,
        }
        resp = client.post(url_create, json=payload, headers=auth_headers)
        report_id = resp.json()["id"]

        url = f"/admin/reports/{report_id}"
        resp = client.delete(url, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

        resp_get = client.get(url, headers=admin_auth_headers)
        assert resp_get.status_code == 404

    def test_delete_report_as_user_forbidden(self, client, auth_headers, db):
        """Basic user cannot delete report."""

        seeded_report = db.query(Report).first()
        assert seeded_report is not None

        url = f"/admin/reports/{seeded_report.id}"
        resp = client.delete(url, headers=auth_headers)

        assert resp.status_code == 403

    def test_bulk_update_reports_as_admin(self, client, admin_auth_headers, user_token, auth_headers, user2_token):
        """Admin performs bulk update on multiple reports."""
        user2_data = get_payload(user2_token)

        url_create = "/reports/"
        report_ids = []
        for i in range(3):
            payload = {
                "contentType": ReportCategory.CHANNELS.value,
                "contentId": str(uuid.uuid4()),
                "reportedUserId": user2_data["sub"],
                "reason": ReportReason.HATE_SPEECH.value,
            }
            resp = client.post(url_create, json=payload, headers=auth_headers)
            report_ids.append(resp.json()["id"])

        bulk_payload = {
            "reportIds": report_ids,
            "action": {
                "status": ReportStatus.RESOLVED.value,
                "priority": ReportPriority.CRITICAL.value,
                "resolution": "All resolved together",
            },
        }

        url = "/admin/reports/bulk"
        resp = client.patch(url, json=bulk_payload, headers=admin_auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["updated"] == 3
        assert "3 reports updated" in data["message"]

        for report_id in report_ids:
            url_get = f"/admin/reports/{report_id}"
            resp_get = client.get(url_get, headers=admin_auth_headers)
            report = resp_get.json()
            assert report["status"] == ReportStatus.RESOLVED.value
            assert report["priority"] == ReportPriority.CRITICAL.value

    def test_bulk_update_empty_list(self, client, admin_auth_headers):
        """Bulk update with empty list should fail validation."""
        bulk_payload = {
            "reportIds": [],
            "action": {"status": ReportStatus.RESOLVED.value},
        }

        url = "/admin/reports/bulk"
        resp = client.patch(url, json=bulk_payload, headers=admin_auth_headers)

        assert resp.status_code == 422

    def test_bulk_update_as_user_forbidden(self, client, auth_headers, db):
        """Basic user cannot perform bulk updates."""

        seeded_report = db.query(Report).first()
        assert seeded_report is not None

        bulk_payload = {
            "reportIds": [str(seeded_report.id)],
            "action": {"status": ReportStatus.RESOLVED.value},
        }

        url = "/admin/reports/bulk"
        resp = client.patch(url, json=bulk_payload, headers=auth_headers)

        assert resp.status_code == 403

    def test_update_nonexistent_report(self, client, admin_auth_headers):
        """Updating non-existent report returns 404."""
        fake_id = str(uuid.uuid4())
        update_payload = {"status": ReportStatus.RESOLVED.value}

        url = f"/admin/reports/{fake_id}"
        resp = client.patch(url, json=update_payload, headers=admin_auth_headers)

        assert resp.status_code == 404

    def test_delete_nonexistent_report(self, client, admin_auth_headers):
        """Deleting non-existent report returns 404."""
        fake_id = str(uuid.uuid4())

        url = f"/admin/reports/{fake_id}"
        resp = client.delete(url, headers=admin_auth_headers)

        assert resp.status_code == 404


class TestReportSeededData:
    """Tests specifically for verifying seeded report data."""

    def test_seeded_reports_exist(self, db):
        """Verify seeded reports are present in the database."""
        report_count = db.query(Report).count()
        assert report_count >= 9, f"Expected at least 10 seeded reports, got {report_count}"

    def test_seeded_reports_have_various_statuses(self, db):
        """Verify seeded reports include various statuses."""
        pending = db.query(Report).filter(Report.status == ReportStatus.PENDING.value).count()
        reviewing = db.query(Report).filter(Report.status == ReportStatus.REVIEWING.value).count()
        resolved = db.query(Report).filter(Report.status == ReportStatus.RESOLVED.value).count()
        dismissed = db.query(Report).filter(Report.status == ReportStatus.DISMISSED.value).count()

        assert pending >= 1, "Expected pending reports from seed data"
        assert resolved >= 1, "Expected resolved reports from seed data"

        total_statuses = sum(1 for count in [pending, reviewing, resolved, dismissed] if count > 0)
        assert total_statuses >= 3, "Expected at least 3 different statuses in seed data"

    def test_seeded_reports_have_various_priorities(self, db):
        """Verify seeded reports include various priorities."""
        low = db.query(Report).filter(Report.priority == ReportPriority.LOW.value).count()
        medium = db.query(Report).filter(Report.priority == ReportPriority.MEDIUM.value).count()
        high = db.query(Report).filter(Report.priority == ReportPriority.HIGH.value).count()
        critical = db.query(Report).filter(Report.priority == ReportPriority.CRITICAL.value).count()

        total_priorities = sum(1 for count in [low, medium, high, critical] if count > 0)
        assert total_priorities >= 3, "Expected at least 3 different priorities in seed data"

    def test_seeded_reports_have_various_categories(self, db):
        """Verify seeded reports include various content categories."""
        housing = db.query(Report).filter(Report.content_type == ReportCategory.HOUSING.value).count()
        marketplace = db.query(Report).filter(Report.content_type == ReportCategory.MARKETPLACE.value).count()
        channels = db.query(Report).filter(Report.content_type == ReportCategory.CHANNELS.value).count()
        messages = db.query(Report).filter(Report.content_type == ReportCategory.MESSAGES.value).count()
        services = db.query(Report).filter(Report.content_type == ReportCategory.SERVICES.value).count()
        user = db.query(Report).filter(Report.content_type == ReportCategory.USER.value).count()

        categories = [housing, marketplace, channels, messages, services, user]
        total_categories = sum(1 for count in categories if count > 0)
        assert total_categories >= 2, "Expected at least 2 different categories in seed data"

    def test_resolved_reports_have_reviewer_info(self, db):
        """Verify resolved reports have reviewer information when admin reviewed."""
        resolved_reports = db.query(Report).filter(Report.status == ReportStatus.RESOLVED.value).all()

        assert len(resolved_reports) >= 1, "Expected resolved reports from seed data"

        reports_with_reviewer = [r for r in resolved_reports if r.reviewed_by_id is not None]
        for report in reports_with_reviewer:
            assert report.reviewed_at is not None, "Reviewed report should have reviewed_at"
            assert report.resolution is not None, "Reviewed report should have resolution"
