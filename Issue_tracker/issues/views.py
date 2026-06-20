import json
import os

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from issues.models import CriticalIssue, Issue, LowPriorityIssue, Reporter

REPORTERS_FILE = os.path.join(settings.BASE_DIR, "reporters.json")
ISSUES_FILE = os.path.join(settings.BASE_DIR, "issues.json")


def _read_json(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)


def _write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)


@csrf_exempt
def reporters(request):
    if request.method == "POST":
        return create_reporter(request)
    elif request.method == "GET":
        return get_reporters(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def create_reporter(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    try:
        reporter = Reporter(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            team=data["team"],
        )
        reporter.validate()
    except KeyError as e:
        return JsonResponse({"error": f"Missing field: {e.args[0]}"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    all_reporters = _read_json(REPORTERS_FILE)
    if any(r["id"] == reporter.id for r in all_reporters):
        return JsonResponse(
            {"error": f"Reporter with id {reporter.id} already exists"}, status=400
        )

    all_reporters.append(reporter.to_dict())
    _write_json(REPORTERS_FILE, all_reporters)

    return JsonResponse(reporter.to_dict(), status=201)


def get_reporters(request):
    reporter_id = request.GET.get("id")
    all_reporters = _read_json(REPORTERS_FILE)

    if reporter_id is not None:
        try:
            reporter_id = int(reporter_id)
        except ValueError:
            return JsonResponse({"error": "id must be an integer"}, status=400)
        for r in all_reporters:
            if r["id"] == reporter_id:
                return JsonResponse(r, status=200)
        return JsonResponse({"error": "Reporter not found"}, status=404)

    return JsonResponse(all_reporters, safe=False, status=200)


@csrf_exempt
def issues(request):
    if request.method == "POST":
        return create_issue(request)
    elif request.method == "GET":
        return get_issues(request)
    return JsonResponse({"error": "Method not allowed"}, status=405)


def create_issue(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    try:
        priority = data["priority"]

        if priority == "critical":
            issue = CriticalIssue(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=priority,
                reporter_id=data["reporter_id"],
            )
        elif priority == "low":
            issue = LowPriorityIssue(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=priority,
                reporter_id=data["reporter_id"],
            )
        else:
            issue = Issue(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                status=data["status"],
                priority=priority,
                reporter_id=data["reporter_id"],
            )

        issue.validate()

    except KeyError as e:
        return JsonResponse({"error": f"Missing field: {e.args[0]}"}, status=400)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    all_issues = _read_json(ISSUES_FILE)
    if any(i["id"] == issue.id for i in all_issues):
        return JsonResponse(
            {"error": f"Issue with id {issue.id} already exists"}, status=400
        )

    all_issues.append(issue.to_dict())
    _write_json(ISSUES_FILE, all_issues)

    response_data = issue.to_dict()
    response_data["message"] = issue.describe()
    return JsonResponse(response_data, status=201)


def get_issues(request):
    issue_id = request.GET.get("id")
    status_filter = request.GET.get("status")
    all_issues = _read_json(ISSUES_FILE)

    if issue_id is not None:
        try:
            issue_id = int(issue_id)
        except ValueError:
            return JsonResponse({"error": "id must be an integer"}, status=400)
        for i in all_issues:
            if i["id"] == issue_id:
                return JsonResponse(i, status=200)
        return JsonResponse({"error": "Issue not found"}, status=404)

    if status_filter is not None:
        filtered = [i for i in all_issues if i["status"] == status_filter]
        return JsonResponse(filtered, safe=False, status=200)

    return JsonResponse(all_issues, safe=False, status=200)
