"""Executable RN-* acceptance cases. Every input is synthetic lab data."""

import json
import random
import unittest
from pathlib import Path

import yaml

from analytics.normalization import ContractError, RouteNormalizer

CONTRACT = Path(__file__).resolve().parents[1] / "docs/openapi.yaml"
KEY = bytes(range(32))  # Public deterministic unit-test bytes, never a runtime key.


def normalizer(content=None, key=KEY, version="test-v1"):
    return RouteNormalizer(content or CONTRACT.read_bytes(), key, version)


class RouteAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.n = normalizer()

    def test_template_method_and_unknown_cases(self):
        cases = [
            ("RN-T01", "GET", "/orders", "/orders", "documented"),
            ("RN-T02", "GET", "/orders/order-1001", "/orders/{orderId}", "documented"),
            ("RN-T03", "PATCH", "/orders/A9-Z", "/orders/{orderId}", "documented"),
            ("RN-T04", "GET", "/admin/orders", "/admin/orders", "documented"),
            ("RN-T05", "get", "/orders", "/orders", "documented"),
            (
                "RN-T06",
                "DELETE",
                "/orders/order-1001",
                "/orders/{orderId}",
                "method_not_documented",
            ),
            ("RN-T07", "HEAD", "/orders", "/orders", "method_not_documented"),
            ("RN-T08", "GE T", "/orders", None, "invalid"),
            ("RN-T09", "A" * 17, "/orders", None, "invalid"),
            ("RN-T10", "GET", "/Orders", "/__unknown__", "path_not_documented"),
            ("RN-T11", "GET", "/orders/", "/__unknown__", "path_not_documented"),
            (
                "RN-Q01",
                "GET",
                "/orders?owner=user-a&token=synthetic-secret",
                "/orders",
                "documented",
            ),
            (
                "RN-Q02",
                "GET",
                "/orders/order-1001?expand=owner",
                "/orders/{orderId}",
                "documented",
            ),
            (
                "RN-Q04",
                "POST",
                "/internal/health?access_token=synthetic-secret",
                "/__unknown__",
                "path_not_documented",
            ),
            ("RN-U01", "GET", "/shadow/orders", "/__unknown__", "path_not_documented"),
            (
                "RN-U02",
                "GET",
                "/orders/123/details",
                "/__unknown__",
                "path_not_documented",
            ),
            (
                "RN-U03",
                "GET",
                "/users/550e8400-e29b-41d4-a716-446655440000",
                "/__unknown__",
                "path_not_documented",
            ),
            (
                "RN-U04",
                "POST",
                "/unknown/synthetic-person@example.invalid",
                "/__unknown__",
                "path_not_documented",
            ),
        ]
        reasons = {
            "documented": "DOCUMENTED_OPERATION",
            "invalid": "INVALID_METHOD",
            "method_not_documented": "METHOD_NOT_IN_CONTRACT",
            "path_not_documented": "PATH_NOT_IN_CONTRACT",
        }
        for case, method, path, route, classification in cases:
            with self.subTest(case=case):
                result = self.n.normalize(method, path)
                self.assertEqual(
                    (result.route, result.classification), (route, classification)
                )
                self.assertEqual(result.reason_code, reasons[classification])
                if classification != "invalid":
                    self.assertEqual(result.method, method.upper())
                if classification == "path_not_documented":
                    self.assertEqual(len(result.unknown_route_token), 64)
                    self.assertNotIn(path, json.dumps(result.to_dict()))

    def test_query_equivalence_RN_Q03_P02(self):
        """RN-Q03, RN-P02: query data never changes the route key or token."""
        for path in ("/orders", "/shadow/order-1001"):
            self.assertEqual(
                self.n.normalize("GET", path + "?x=1"),
                self.n.normalize("GET", path + "?x=2"),
            )

    def test_encoding_cases(self):
        cases = [
            ("RN-E01", "/%6Frders", "DOCUMENTED_OPERATION"),
            ("RN-E02", "/orders/order%2D1001", "DOCUMENTED_OPERATION"),
            ("RN-E03", "/orders/%ZZ", "INVALID_PATH_ENCODING"),
            ("RN-E04", "/orders/%C3%28", "INVALID_PATH_ENCODING"),
            ("RN-E05", "/orders%2Forder-1001", "INVALID_PATH_ENCODING"),
            ("RN-E06", "/orders%5Corder-1001", "INVALID_PATH_ENCODING"),
            ("RN-E07", "/orders/%256F%2572%2564%2565%2572", "INVALID_PATH_ENCODING"),
            ("RN-E08", "/orders/%00", "INVALID_PATH_ENCODING"),
        ]
        for case, target, reason in cases:
            with self.subTest(case=case):
                self.assertEqual(self.n.normalize("GET", target).reason_code, reason)

    def test_traversal_cases(self):
        for case, target in [
            ("RN-X01", "/orders/../admin/orders"),
            ("RN-X02", "/orders/%2e%2e/admin/orders"),
            ("RN-X03", "/orders/./order-1001"),
            ("RN-X04", "//orders"),
            ("RN-X05", "/orders\\order-1001"),
            ("RN-X06", "/orders#synthetic-fragment"),
        ]:
            with self.subTest(case=case):
                self.assertEqual(
                    self.n.normalize("GET", target).reason_code, "AMBIGUOUS_PATH_SYNTAX"
                )

    def test_bounds_cases_with_exact_byte_counts(self):
        boundary = "/" + "/".join(["a" * 127] * 16)
        self.assertEqual(len(boundary.encode()), 2048)
        cases = [
            ("RN-B01", "/orders/" + "a" * 64, "DOCUMENTED_OPERATION"),
            ("RN-B02", "/orders/" + "a" * 65, "INVALID_PARAMETER"),
            ("RN-B03", "/orders/order_1001", "INVALID_PARAMETER"),
            ("RN-B04", "/orders/caf%C3%A9", "INVALID_PARAMETER"),
            ("RN-B05", "", "INVALID_PATH_BOUNDS"),
            ("RN-B06", boundary, "PATH_NOT_IN_CONTRACT"),
            ("RN-B07", boundary + "a", "INVALID_PATH_BOUNDS"),
            ("RN-B08", "/" + "/".join(["a"] * 32), "PATH_NOT_IN_CONTRACT"),
            ("RN-B09", "/" + "/".join(["a"] * 33), "INVALID_PATH_BOUNDS"),
            ("RN-B10", "/unknown/" + "a" * 128, "PATH_NOT_IN_CONTRACT"),
            ("RN-B11", "/unknown/" + "a" * 129, "INVALID_PATH_BOUNDS"),
            ("RN-Q05", "/orders?" + "a" * 4089, "INVALID_PATH_BOUNDS"),
        ]
        self.assertEqual(len(cases[-1][1].encode()), 4097)
        for case, target, reason in cases:
            with self.subTest(case=case):
                self.assertEqual(self.n.normalize("GET", target).reason_code, reason)

    def test_hmac_determinism_and_rotation_RN_P01_P03_P04_P08(self):
        """RN-P01, RN-P03, RN-P04, RN-P08: deterministic, keyed and versioned."""
        a = self.n.normalize("GET", "/private/synthetic-one")
        self.assertEqual(a, self.n.normalize("GET", "/private/synthetic-one"))
        self.assertNotEqual(
            a.unknown_route_token,
            self.n.normalize("GET", "/private/synthetic-two").unknown_route_token,
        )
        rotated = normalizer(key=bytes(reversed(range(32))), version="test-v2")
        b = rotated.normalize("GET", "/private/synthetic-one")
        self.assertNotEqual(a.unknown_route_token, b.unknown_route_token)
        self.assertEqual(b.unknown_route_key_version, "test-v2")
        self.assertEqual(a, self.n.normalize("GET", "/private/%73ynthetic-one"))

    def test_indistinguishable_templates_RN_P07(self):
        """RN-P07: ambiguous templates fail compilation rather than selecting one."""
        data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8-sig"))
        data["paths"]["/orders/{name}"] = {
            "parameters": [
                {
                    "name": "name",
                    "in": "path",
                    "required": True,
                    "schema": data["components"]["parameters"]["OrderId"]["schema"],
                }
            ],
            "get": {},
        }
        with self.assertRaises(ContractError):
            normalizer(yaml.safe_dump(data).encode())

    def test_static_precedence_independent_of_method(self):
        data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8-sig"))
        data["paths"]["/orders/special"] = {"get": {}}
        n = normalizer(yaml.safe_dump(data).encode())
        result = n.normalize("PATCH", "/orders/special")
        self.assertEqual(
            (result.route, result.reason_code),
            ("/orders/special", "METHOD_NOT_IN_CONTRACT"),
        )

    def test_compile_rejects_unsupported_pattern_missing_version_and_duplicate_keys(
        self,
    ):
        for mutate in ("pattern", "version", "type"):
            data = yaml.safe_load(CONTRACT.read_text(encoding="utf-8-sig"))
            if mutate == "version":
                del data["info"]["version"]
            else:
                data["components"]["parameters"]["OrderId"]["schema"][mutate] = (
                    "unsupported"
                )
            with self.subTest(case=mutate), self.assertRaises(ContractError):
                normalizer(yaml.safe_dump(data).encode())
        with self.assertRaises(ContractError):
            normalizer(CONTRACT.read_bytes() + b"\npaths: {}\n")

    def test_fuzz_malformed_inputs_deterministic_bounded_and_no_echo(self):
        rng = random.Random(104)  # Reproducible fuzz corpus, not cryptography.
        for _ in range(1000):
            path = "/synthetic/" + "".join(
                rng.choices("%0123456789abcdef./\\?AZ", k=rng.randrange(160))
            )
            one = self.n.normalize("GET", path)
            self.assertEqual(one, self.n.normalize("GET", path))
            self.assertLess(len(json.dumps(one.to_dict())), 512)
            self.assertNotIn("synthetic", json.dumps(one.to_dict()))
        for path in (None, 42, "\ud800", "/%ff", "/%252e%252e", "/%0d%0a"):
            self.assertEqual(self.n.normalize("GET", path).classification, "invalid")

    def test_unsupported_methods_not_inferred_and_updated_openapi_support_route(self):
        self.assertEqual(
            self.n.normalize("OPTIONS", "/orders").reason_code, "METHOD_NOT_IN_CONTRACT"
        )
        self.assertEqual(
            self.n.normalize("GET", "/support/orders").classification, "documented"
        )

    def test_contract_version_is_line_ending_independent(self):
        """Windows and Unix checkouts must produce the same contract fingerprint."""
        content = CONTRACT.read_bytes()
        windows_content = content.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        bare_cr_content = content.replace(b"\r\n", b"\n").replace(b"\n", b"\r")
        expected = normalizer(content).contract_version
        self.assertEqual(normalizer(windows_content).contract_version, expected)
        self.assertEqual(normalizer(bare_cr_content).contract_version, expected)

    def test_runtime_key_and_contract_version_required(self):
        with self.assertRaises(ValueError):
            normalizer(key=b"short")
        self.assertTrue(self.n.contract_version.startswith("sha256:"))
