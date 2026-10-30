#!/usr/bin/env python3
"""Assign a published GitHub issue batch to configured human team members."""
import argparse
import heapq
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


def positive(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} must be a positive finite number")
    return float(value)


def number(value, label):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive issue number")
    return value


def strings(value, label):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v.strip() for v in value):
        raise ValueError(f"{label} must be a list of non-empty strings")
    return sorted(set(v.strip().casefold() for v in value))


def validate(team, tickets):
    if not isinstance(team, dict) or not isinstance(tickets, dict):
        raise ValueError("team and tickets must be JSON objects")
    repo = team.get("repository")
    if not isinstance(repo, str) or not REPOSITORY.fullmatch(repo) or repo.casefold() == "owner/repository":
        raise ValueError("team.repository must be the actual OWNER/REPOSITORY")
    members = team.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("team.members must contain at least one real participant")
    normalized = []
    seen = set()
    for m in members:
        if not isinstance(m, dict):
            raise ValueError("each member must be an object")
        login = m.get("login")
        if not isinstance(login, str) or not LOGIN.fullmatch(login) or login.casefold() == "replace-with-real-github-login":
            raise ValueError(f"invalid or placeholder GitHub login: {login!r}")
        if login.casefold() in seen:
            raise ValueError(f"duplicate team member: {login}")
        seen.add(login.casefold())
        normalized.append({"login": login, "capacity": positive(m.get("capacity", 1), f"capacity of {login}"), "skills": strings(m.get("skills", []), f"skills of {login}")})
    issues = tickets.get("issues")
    if not isinstance(issues, list) or not issues:
        raise ValueError("tickets.issues must be a non-empty list")
    entries = {}
    for item in issues:
        if not isinstance(item, dict):
            raise ValueError("each issue must be an object")
        n = number(item.get("number"), "issue number")
        if n in entries:
            raise ValueError(f"duplicate issue #{n}")
        blocked = item.get("blocked_by", [])
        if not isinstance(blocked, list):
            raise ValueError(f"blocked_by of #{n} must be a list")
        blocked = sorted(set(number(b, f"blocker of #{n}") for b in blocked))
        entries[n] = {"number": n, "blocked_by": blocked, "skills": strings(item.get("skills", []), f"skills of #{n}"), "estimate": positive(item.get("estimate", 1), f"estimate of #{n}")}
    indegree = {n: 0 for n in entries}
    edges = {n: [] for n in entries}
    for n, item in entries.items():
        for blocker in item["blocked_by"]:
            if blocker in entries:
                indegree[n] += 1
                edges[blocker].append(n)
    ready = [n for n in entries if indegree[n] == 0]
    heapq.heapify(ready)
    ordered = []
    while ready:
        n = heapq.heappop(ready)
        ordered.append(entries[n])
        for child in edges[n]:
            indegree[child] -= 1
            if indegree[child] == 0:
                heapq.heappush(ready, child)
    if len(ordered) != len(entries):
        raise ValueError("dependency cycle in ticket batch")
    return repo, normalized, ordered


def run_gh(*args):
    try:
        result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(f"cannot execute gh: {exc}") from exc
    if result.returncode:
        raise RuntimeError(f"gh failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout


def fetch_issue(repo, n):
    data = json.loads(run_gh("api", f"repos/{repo}/issues/{n}"))
    if "pull_request" in data:
        raise ValueError(f"#{n} is a pull request, not an issue")
    return {"state": data["state"].lower(), "assignees": [a["login"] for a in data.get("assignees", [])]}


def make_plan(members, tickets, issues):
    load = {m["login"].casefold(): 0.0 for m in members}
    for ticket in tickets:
        issue = issues[ticket["number"]]
        if issue["state"] == "open":
            for login in issue["assignees"]:
                if login.casefold() in load:
                    load[login.casefold()] += ticket["estimate"]
    result = []
    for ticket in tickets:
        n = ticket["number"]
        issue = issues[n]
        blocked = [b for b in ticket["blocked_by"] if issues[b]["state"] != "closed"]
        row = {"issue": n, "open_blockers": blocked, "ready": not blocked}
        if issue["state"] != "open":
            row.update(action="skipped_closed", assignees=issue["assignees"])
        elif issue["assignees"]:
            row.update(action="skipped_assigned", assignees=issue["assignees"])
        else:
            eligible = [m for m in members if set(ticket["skills"]).issubset(m["skills"])]
            if not eligible:
                row.update(action="unassigned_no_matching_skills", required_skills=ticket["skills"])
            else:
                chosen = min(eligible, key=lambda m: (load[m["login"].casefold()] / m["capacity"], m["login"].casefold()))
                row.update(action="planned", assignee=chosen["login"])
                load[chosen["login"].casefold()] += ticket["estimate"]
        result.append(row)
    return result


def execute(repo, plan):
    failed = False
    for row in plan:
        if row["action"] != "planned":
            continue
        try:
            current = fetch_issue(repo, row["issue"])
            if current["state"] != "open" or current["assignees"]:
                row.update(action="skipped_changed", current=current)
                continue
            run_gh("issue", "edit", str(row["issue"]), "--repo", repo, "--add-assignee", row["assignee"])
            verified = fetch_issue(repo, row["issue"])
            if row["assignee"].casefold() not in [x.casefold() for x in verified["assignees"]]:
                raise RuntimeError("assignment could not be verified")
            if len(verified["assignees"]) != 1:
                row.update(action="conflict_after_write", current=verified)
                failed = True
            else:
                row.update(action="applied")
        except (ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
            row.update(action="failed", error=str(exc))
            failed = True
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", required=True, type=Path)
    parser.add_argument("--tickets", required=True, type=Path)
    parser.add_argument("--apply", action="store_true", help="write issue assignments to GitHub")
    parser.add_argument("--snapshot", type=Path, help="offline JSON fixture; cannot be used with --apply")
    args = parser.parse_args()
    if args.apply and args.snapshot:
        parser.error("--snapshot cannot be combined with --apply")
    try:
        team = json.loads(args.team.read_text(encoding="utf-8-sig"))
        tickets = json.loads(args.tickets.read_text(encoding="utf-8-sig"))
        repo, members, ordered = validate(team, tickets)
        ids = {t["number"] for t in ordered} | {b for t in ordered for b in t["blocked_by"]}
        if args.snapshot:
            snapshot = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
            issues = {n: snapshot["issues"][str(n)] for n in ids}
        else:
            for member in members:
                run_gh("api", f"repos/{repo}/assignees/{member['login']}")
            issues = {n: fetch_issue(repo, n) for n in sorted(ids)}
        for n, issue in issues.items():
            if not isinstance(issue, dict) or issue.get("state") not in ("open", "closed"):
                raise ValueError(f"invalid state for issue #{n}")
            assignees = issue.get("assignees")
            if not isinstance(assignees, list) or any(not isinstance(a, str) or not LOGIN.fullmatch(a) for a in assignees):
                raise ValueError(f"invalid assignees for issue #{n}")
        plan = make_plan(members, ordered, issues)
        failed = execute(repo, plan) if args.apply else False
        unresolved = any(row["action"] in ("unassigned_no_matching_skills", "skipped_changed", "conflict_after_write", "failed") for row in plan)
        print(json.dumps({"repository": repo, "mode": "apply" if args.apply else "preview", "results": plan}, ensure_ascii=False, indent=2))
        return 1 if failed or unresolved else 0
    except (ValueError, RuntimeError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"Distribution stopped: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
