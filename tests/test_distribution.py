import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

path = Path(__file__).resolve().parents[1] / ".agents" / "workflow" / "distribute.py"
spec = importlib.util.spec_from_file_location("distribute", path)
distribution = importlib.util.module_from_spec(spec)
spec.loader.exec_module(distribution)


def member(login, capacity=1, skills=None):
    return {"login": login, "capacity": capacity, "skills": skills or []}


def issue(n, blockers=None, skills=None, estimate=1):
    return {"number": n, "blocked_by": blockers or [], "skills": skills or [], "estimate": estimate}


def plan(members, tickets, data):
    _, people, ordered = distribution.validate({"repository": "team/repo", "members": members}, {"issues": tickets})
    return distribution.make_plan(people, ordered, data)


class DistributionTests(unittest.TestCase):
    def test_one_person_owns_all_and_dependency_stays_blocked(self):
        data = {n: {"state": "open", "assignees": []} for n in (1, 2)}
        result = plan([member("alice")], [issue(2, [1]), issue(1)], data)
        self.assertEqual([r["assignee"] for r in result], ["alice", "alice"])
        self.assertEqual(result[1]["open_blockers"], [1])
        self.assertFalse(result[1]["ready"])

    def test_many_people_and_weighted_capacity(self):
        data = {n: {"state": "open", "assignees": []} for n in range(1, 7)}
        result = plan([member("alice", 2), member("bob")], [issue(n) for n in data], data)
        self.assertEqual([r["assignee"] for r in result].count("alice"), 4)
        self.assertEqual([r["assignee"] for r in result].count("bob"), 2)
        members = [member("user" + str(n)) for n in range(100)]
        result = plan(members, [issue(1)], {1: data[1]})
        self.assertEqual(result[0]["action"], "planned")

    def test_skills_match_and_missing_skill_does_not_guess(self):
        data = {1: {"state": "open", "assignees": []}, 2: {"state": "open", "assignees": []}}
        result = plan([member("alice", skills=["frontend"]), member("bob", skills=["backend"])], [issue(1, skills=["backend"]), issue(2, skills=["security"])], data)
        self.assertEqual(result[0]["assignee"], "bob")
        self.assertEqual(result[1]["action"], "unassigned_no_matching_skills")

    def test_existing_assignment_is_preserved_and_counted(self):
        data = {1: {"state": "open", "assignees": ["alice"]}, 2: {"state": "open", "assignees": []}}
        result = plan([member("alice"), member("bob")], [issue(1), issue(2)], data)
        self.assertEqual(result[0]["action"], "skipped_assigned")
        self.assertEqual(result[1]["assignee"], "bob")

    def test_external_closed_blocker_does_not_block(self):
        data = {1: {"state": "open", "assignees": []}, 99: {"state": "closed", "assignees": []}}
        result = plan([member("alice")], [issue(1, [99])], data)
        self.assertTrue(result[0]["ready"])

    def test_cycle_and_empty_roster_fail(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            distribution.validate({"repository": "team/repo", "members": [member("alice")]}, {"issues": [issue(1, [2]), issue(2, [1])]})
        with self.assertRaisesRegex(ValueError, "at least one"):
            distribution.validate({"repository": "team/repo", "members": []}, {"issues": [issue(1)]})

    def test_apply_rechecks_and_does_not_replace_new_owner(self):
        rows = [{"issue": 1, "action": "planned", "assignee": "alice"}]
        with patch.object(distribution, "fetch_issue", return_value={"state": "open", "assignees": ["bob"]}), patch.object(distribution, "run_gh") as gh:
            distribution.execute("team/repo", rows)
        self.assertEqual(rows[0]["action"], "skipped_changed")
        gh.assert_not_called()

    def test_apply_verifies_and_reports_failure(self):
        rows = [{"issue": 1, "action": "planned", "assignee": "alice"}]
        states = [{"state": "open", "assignees": []}, {"state": "open", "assignees": []}]
        with patch.object(distribution, "fetch_issue", side_effect=states), patch.object(distribution, "run_gh"):
            failed = distribution.execute("team/repo", rows)
        self.assertTrue(failed)
        self.assertEqual(rows[0]["action"], "failed")

    def test_apply_writes_only_new_assignment_and_verifies(self):
        rows = [{"issue": 1, "action": "planned", "assignee": "alice"}]
        states = [{"state": "open", "assignees": []}, {"state": "open", "assignees": ["alice"]}]
        with patch.object(distribution, "fetch_issue", side_effect=states), patch.object(distribution, "run_gh") as gh:
            failed = distribution.execute("team/repo", rows)
        self.assertFalse(failed)
        self.assertEqual(rows[0]["action"], "applied")
        gh.assert_called_once_with("issue", "edit", "1", "--repo", "team/repo", "--add-assignee", "alice")


if __name__ == "__main__":
    unittest.main()
