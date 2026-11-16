import json
import math
from typing import Any

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from alerts.models import Alert
from services.explainer import generate_explanation


SEVERITIES = {severity.value for severity in Alert.Severity}
STRING_FIELDS = ("title", "source", "metric_name")
NUMBER_FIELDS = ("metric_value", "threshold")


def root(request: HttpRequest) -> JsonResponse:
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    return JsonResponse({"status": "AI Intelligence Layer is running"})


def _serialize_alert(alert: Alert) -> dict[str, Any]:
    return {
        "id": alert.id,
        "title": alert.title,
        "severity": alert.severity,
        "source": alert.source,
        "metric_name": alert.metric_name,
        "metric_value": alert.metric_value,
        "threshold": alert.threshold,
        "created_at": alert.created_at.isoformat(),
    }


def _validate_payload(payload: Any) -> tuple[dict[str, Any] | None, dict[str, str]]:
    if not isinstance(payload, dict):
        return None, {"body": "Expected a JSON object"}

    errors: dict[str, str] = {}
    values: dict[str, Any] = {}
    required_fields = (*STRING_FIELDS, "severity", *NUMBER_FIELDS)

    for field in required_fields:
        if field not in payload:
            errors[field] = "This field is required"

    for field in STRING_FIELDS:
        value = payload.get(field)
        if field in payload and not isinstance(value, str):
            errors[field] = "Expected a string"
        else:
            values[field] = value

    severity = payload.get("severity")
    if "severity" in payload:
        if severity not in SEVERITIES:
            errors["severity"] = "Must be critical, warning, or info"
        else:
            values["severity"] = severity

    for field in NUMBER_FIELDS:
        value = payload.get(field)
        if field not in payload:
            continue
        try:
            if isinstance(value, bool):
                raise ValueError
            number = float(value)
            if not math.isfinite(number):
                raise ValueError
            values[field] = number
        except (TypeError, ValueError):
            errors[field] = "Expected a finite number"

    if errors:
        return None, errors
    return values, {}


def _read_json(request: HttpRequest) -> tuple[Any | None, JsonResponse | None]:
    try:
        return json.loads(request.body), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"detail": "Invalid JSON"}, status=422)


@csrf_exempt
def alert_collection(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        alerts = [_serialize_alert(alert) for alert in Alert.objects.all()]
        return JsonResponse(alerts, safe=False)
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    payload, error = _read_json(request)
    if error is not None:
        return error
    values, errors = _validate_payload(payload)
    if errors:
        return JsonResponse(
            {"detail": "Invalid alert payload", "errors": errors},
            status=422,
        )

    alert = Alert.objects.create(**values)
    return JsonResponse(_serialize_alert(alert), status=201)


def alert_detail(request: HttpRequest, alert_id: int) -> JsonResponse:
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    alert = Alert.objects.filter(pk=alert_id).first()
    if alert is None:
        return JsonResponse({"detail": "Alert not found"}, status=404)
    return JsonResponse(_serialize_alert(alert))


@csrf_exempt
def explain_alert(request: HttpRequest, alert_id: int) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)
    alert = Alert.objects.filter(pk=alert_id).first()
    if alert is None:
        return JsonResponse({"detail": "Alert not found"}, status=404)
    return JsonResponse(
        {
            "alert_id": alert.id,
            "explanation": generate_explanation(alert),
            "generated_at": timezone.now().isoformat(),
        }
    )