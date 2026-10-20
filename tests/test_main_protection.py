import json
import subprocess
import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

from scripts.manage_main_protection import (
    CHECK,
    PROTECTION_PATH,
    REPO_PATH,
    REPOSITORY,
    SETTINGS,
    ApiError,
    ProtectionError,
    configure,
    gh_request,
    protection_gaps,
)


class MainProtectionTests(unittest.TestCase):
    def setUp(self):
        self.settings = json.loads(SETTINGS.read_text())

    def test_approved_payload_has_all_required_controls(self):
        self.assertEqual(protection_gaps(self.settings), [])

    def test_each_weakened_control_is_detected(self):
        for field in ("enforce_admins", "required_conversation_resolution"):
            changed = deepcopy(self.settings)
            changed[field] = False
            with self.subTest(field=field):
                self.assertTrue(protection_gaps(changed))
        for field in ("allow_force_pushes", "allow_deletions"):
            changed = deepcopy(self.settings)
            changed[field] = True
            with self.subTest(field=field):
                self.assertTrue(protection_gaps(changed))
        for field, value in (
            ("required_approving_review_count", 1),
            ("dismiss_stale_reviews", False),
            ("require_code_owner_reviews", False),
            ("require_last_push_approval", False),
            ("bypass_pull_request_allowances", {"users": ["synthetic-user"]}),
        ):
            changed = deepcopy(self.settings)
            changed["required_pull_request_reviews"][field] = value
            with self.subTest(field=field):
                self.assertTrue(protection_gaps(changed))

    def test_wrong_app_or_non_strict_check_is_rejected(self):
        changed = deepcopy(self.settings)
        changed["required_status_checks"]["checks"] = [dict(CHECK, app_id=1)]
        self.assertTrue(protection_gaps(changed))
        changed = deepcopy(self.settings)
        changed["required_status_checks"]["strict"] = False
        self.assertTrue(protection_gaps(changed))

    def test_default_check_never_writes(self):
        request = Mock(side_effect=ApiError(404))
        self.assertFalse(configure(request=request)["verified"])
        request.assert_called_once_with("GET", PROTECTION_PATH)

    def test_forbidden_apply_never_writes(self):
        request = Mock(side_effect=ApiError(403))
        with self.assertRaises(ApiError):
            configure(apply=True, request=request)
        request.assert_called_once_with("GET", PROTECTION_PATH)

    def test_existing_stronger_protection_is_preserved(self):
        observed = deepcopy(self.settings)
        observed["required_pull_request_reviews"]["required_approving_review_count"] = 3
        request = Mock(return_value=observed)
        result = configure(apply=True, request=request)
        self.assertTrue(result["verified"])
        self.assertFalse(result["changed"])
        request.assert_called_once_with("GET", PROTECTION_PATH)

    def test_existing_incomplete_protection_is_not_overwritten(self):
        request = Mock(return_value={})
        with self.assertRaisesRegex(ProtectionError, "not overwritten"):
            configure(apply=True, request=request)
        request.assert_called_once_with("GET", PROTECTION_PATH)

    def test_wrong_repository_or_nonadmin_cannot_apply(self):
        for repo in (
            {"full_name": "other/repository", "permissions": {"admin": True}},
            {"full_name": REPOSITORY, "permissions": {"admin": False}},
        ):
            request = Mock(side_effect=[ApiError(404), repo])
            with self.subTest(repo=repo), self.assertRaises(ProtectionError):
                configure(apply=True, request=request)
            self.assertEqual(
                [c.args[0] for c in request.call_args_list], ["GET", "GET"]
            )

    def test_create_targets_only_main_and_requires_readback(self):
        repo = {"full_name": REPOSITORY, "permissions": {"admin": True}}
        request = Mock(
            side_effect=[ApiError(404), repo, {}, self.settings, {"protected": True}]
        )
        result = configure(apply=True, request=request)
        self.assertTrue(result["verified"])
        self.assertTrue(result["changed"])
        self.assertEqual(request.call_args_list[1].args, ("GET", REPO_PATH))
        self.assertEqual(
            request.call_args_list[2].args, ("PUT", PROTECTION_PATH, self.settings)
        )

    def test_successful_put_does_not_hide_failed_verification(self):
        repo = {"full_name": REPOSITORY, "permissions": {"admin": True}}
        request = Mock(side_effect=[ApiError(404), repo, {}, {}, {"protected": False}])
        with self.assertRaisesRegex(ProtectionError, "verification failed"):
            configure(apply=True, request=request)

    def test_lost_readback_after_put_does_not_claim_nothing_changed(self):
        repo = {"full_name": REPOSITORY, "permissions": {"admin": True}}
        request = Mock(side_effect=[ApiError(404), repo, {}, ApiError(403)])
        with self.assertRaisesRegex(ProtectionError, "submitted but readback failed"):
            configure(apply=True, request=request)

    @patch("scripts.manage_main_protection.subprocess.run")
    def test_cli_sends_payload_on_stdin_without_credential_arguments(self, run):
        run.return_value = subprocess.CompletedProcess(
            [], 0, 'HTTP/2.0 200 OK\ncontent-type: application/json\n\n{"ok":true}', ""
        )
        self.assertEqual(
            gh_request("PUT", PROTECTION_PATH, self.settings), {"ok": True}
        )
        self.assertEqual(run.call_args.kwargs["input"], json.dumps(self.settings))
        self.assertIn("--input", run.call_args.args[0])
        self.assertNotIn("Authorization", str(run.call_args))


if __name__ == "__main__":
    unittest.main()
