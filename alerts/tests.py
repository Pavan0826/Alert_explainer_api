import json

from django.test import TestCase

from alerts.models import Alert


class AlertApiTests(TestCase):
    def test_root_returns_status(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "AI Intelligence Layer is running"})

    def test_create_list_and_get_alert(self) -> None:
        payload = {
            "title": "CPU high",
            "severity": "critical",
            "source": "worker-1",
            "metric_name": "CPU utilization",
            "metric_value": 95,
            "threshold": 80,
        }
        created = self.client.post(
            "/alerts/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        alert = created.json()
        self.assertEqual(alert["severity"], "critical")
        self.assertIn("created_at", alert)
        self.assertEqual(self.client.get("/alerts/").json(), [alert])
        self.assertEqual(self.client.get(f"/alerts/{alert['id']}").json(), alert)

    def test_invalid_severity_is_rejected(self) -> None:
        response = self.client.post(
            "/alerts/",
            data=json.dumps(
                {
                    "title": "Bad severity",
                    "severity": "urgent",
                    "source": "worker-1",
                    "metric_name": "CPU utilization",
                    "metric_value": 95,
                    "threshold": 80,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 422)

    def test_explanation_and_missing_alert_responses(self) -> None:
        alert = Alert.objects.create(
            title="CPU high",
            severity=Alert.Severity.CRITICAL,
            source="worker-1",
            metric_name="CPU utilization",
            metric_value=95,
            threshold=80,
        )
        response = self.client.post(f"/alerts/{alert.id}/explain")
        self.assertEqual(response.status_code, 200)
        self.assertIn("metric exceeded its threshold", response.json()["explanation"])
        self.assertEqual(response.json()["alert_id"], alert.id)
        self.assertIn("generated_at", response.json())
        self.assertEqual(self.client.get("/alerts/999").status_code, 404)
        missing_explanation = self.client.post("/alerts/999/explain")
        self.assertEqual(missing_explanation.status_code, 404)
        self.assertEqual(missing_explanation.json()["detail"], "Alert not found")