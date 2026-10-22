import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "mock-api"))

import main

HTTP_METHODS = {"get", "post", "patch", "put", "delete"}


class OpenAPIContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract_path = ROOT / "docs" / "openapi.yaml"

        with contract_path.open(encoding="utf-8-sig") as file:
            cls.contract = yaml.safe_load(file)

        cls.generated = main.app.openapi()

    def test_openapi_version_matches(self):
        self.assertEqual(
            self.contract["openapi"],
            self.generated["openapi"],
        )

    def test_documented_operations_exist(self):
        for path, methods in self.contract["paths"].items():
            for method in methods:
                if method not in HTTP_METHODS:
                    continue

                with self.subTest(path=path, method=method):
                    self.assertIn(path, self.generated["paths"])
                    self.assertIn(
                        method,
                        self.generated["paths"][path],
                    )

    def test_operation_ids_match(self):
        for path, methods in self.contract["paths"].items():
            for method, operation in methods.items():
                if method not in HTTP_METHODS:
                    continue

                actual = self.generated["paths"][path][method]

                with self.subTest(path=path, method=method):
                    self.assertEqual(
                        operation.get("operationId"),
                        actual.get("operationId"),
                    )

    def test_documented_responses_exist_in_generated_schema(self):
        for path, methods in self.contract["paths"].items():
            for method, operation in methods.items():
                if method not in HTTP_METHODS:
                    continue

                actual = self.generated["paths"][path][method]
                documented_codes = set(operation["responses"])
                generated_codes = set(actual["responses"])

                with self.subTest(path=path, method=method):
                    self.assertTrue(
                        documented_codes.issubset(generated_codes),
                        (
                            "Response codes missing from generated schema: "
                            f"{documented_codes - generated_codes}"
                        ),
                    )

    def test_order_id_constraints_match(self):
        documented = (
            self.contract["components"]["parameters"]["OrderId"]["schema"]
        )

        generated_parameters = (
            self.generated["paths"]["/orders/{orderId}"]["get"]["parameters"]
        )

        order_id = next(
            parameter
            for parameter in generated_parameters
            if parameter["name"] == "orderId"
        )

        actual = order_id["schema"]

        for key in ("type", "minLength", "maxLength", "pattern"):
            with self.subTest(constraint=key):
                self.assertEqual(
                    documented.get(key),
                    actual.get(key),
                )

    def test_patch_request_schema_matches(self):
        documented = self.contract["components"]["schemas"]["OrderUpdate"]
        generated = self.generated["components"]["schemas"]["OrderUpdate"]

        self.assertEqual(
            documented["required"],
            generated["required"],
        )
        self.assertEqual(
            documented["additionalProperties"],
            generated["additionalProperties"],
        )
        self.assertEqual(
            documented["properties"]["status"]["enum"],
            generated["properties"]["status"]["enum"],
        )

    def test_security_scheme_matches_runtime_bearer_auth(self):
        documented = self.contract["components"]["securitySchemes"]
        generated = self.generated["components"]["securitySchemes"]

        self.assertEqual(set(documented), set(generated))
        self.assertIn("bearerAuth", documented)
        self.assertEqual(documented["bearerAuth"]["type"], "http")
        self.assertEqual(documented["bearerAuth"]["scheme"], "bearer")
        self.assertEqual(
            documented["bearerAuth"]["type"],
            generated["bearerAuth"]["type"],
        )
        self.assertEqual(
            documented["bearerAuth"]["scheme"],
            generated["bearerAuth"]["scheme"],
        )

    def test_every_operation_requires_authentication(self):
        for path, methods in self.generated["paths"].items():
            for method, operation in methods.items():
                if method not in HTTP_METHODS:
                    continue

                with self.subTest(path=path, method=method):
                    security = operation.get(
                        "security",
                        self.generated.get("security", []),
                    )

                    self.assertTrue(
                        security,
                        "Operation must declare authentication security",
                    )
                    self.assertTrue(
                        any("bearerAuth" in item for item in security),
                        "Operation must require bearerAuth",
                    )

    def test_documented_and_runtime_operation_sets_match_exactly(self):
        def operation_set(schema):
            return {
                (path, method)
                for path, methods in schema["paths"].items()
                for method in methods
                if method in HTTP_METHODS
            }

        self.assertEqual(
            operation_set(self.contract),
            operation_set(self.generated),
            "OpenAPI contract has missing or undocumented runtime operations",
        )

    def test_patch_documents_required_nonce_header(self):
        parameters = self.contract["paths"]["/orders/{orderId}"]["patch"][
            "parameters"
        ]
        nonce = next(
            parameter
            for parameter in parameters
            if parameter.get("name") == "X-Request-Nonce"
        )
        self.assertEqual(nonce["in"], "header")
        self.assertTrue(nonce["required"])
        self.assertEqual(nonce["schema"]["minLength"], 8)
        self.assertEqual(nonce["schema"]["maxLength"], 128)

    def test_admin_and_patch_describe_required_permissions(self):
        admin_description = self.contract["paths"]["/admin/orders"]["get"][
            "description"
        ]
        patch_description = self.contract["paths"]["/orders/{orderId}"]["patch"][
            "description"
        ]

        self.assertIn("orders:read:any", admin_description)
        self.assertIn("orders:manage", patch_description)

    def test_error_response_references_are_valid(self):
        responses = self.contract["components"]["responses"]
        schemas = self.contract["components"]["schemas"]

        for response_name in (
            "InvalidRequest",
            "Unauthorized",
            "Forbidden",
            "NotFound",
        ):
            with self.subTest(response=response_name):
                self.assertIn(response_name, responses)

                schema_ref = responses[response_name]["content"][
                    "application/json"
                ]["schema"]["$ref"]

                self.assertEqual(
                    schema_ref,
                    "#/components/schemas/Error",
                )

        error = schemas["Error"]
        detail = error["properties"]["error"]

        self.assertIn("error", error["required"])
        self.assertIn("code", detail["required"])
        self.assertIn("message", detail["required"])

    def test_tenant_boundary_is_documented_for_order_operations(self):
        operations = (
            self.contract["paths"]["/orders"]["get"],
            self.contract["paths"]["/orders/{orderId}"]["get"],
            self.contract["paths"]["/orders/{orderId}"]["patch"],
            self.contract["paths"]["/admin/orders"]["get"],
        )

        for operation in operations:
            with self.subTest(operation=operation.get("operationId")):
                description = operation["description"].lower()
                self.assertIn("tenant", description)
                self.assertIn("denied", description)

    def test_public_order_schema_does_not_expose_tenant_id(self):
        documented = self.contract["components"]["schemas"]["Order"]
        generated = self.generated["components"]["schemas"]["Order"]

        self.assertNotIn("tenant_id", documented["properties"])
        self.assertNotIn("tenant_id", generated["properties"])
        self.assertIn(
            "tenant identifiers",
            documented["description"].lower(),
        )

    def test_admin_contract_does_not_claim_scoped_tenant_admin_access(self):
        description = self.contract["paths"]["/admin/orders"]["get"][
            "description"
        ].lower()

        self.assertIn("one shared lab tenant", description)
        self.assertIn("does not establish scoped", description)
        self.assertIn("cross-tenant operations", description)

    def test_contract_documents_server_resolved_read_only_sharing(self):
        description = self.contract["paths"]["/orders/{orderId}"]["get"][
            "description"
        ].lower()

        self.assertIn("sharing", description)
        self.assertIn("read-only", description)
        self.assertIn("revoked", description)
        self.assertIn("generic 404", description)

    def test_policy_version_header_is_required_in_contract_and_runtime(self):
        parameter = self.contract["components"]["parameters"]["PolicyVersion"]
        self.assertEqual(parameter["name"], "X-Policy-Version")
        self.assertEqual(parameter["in"], "header")
        self.assertTrue(parameter["required"])
        self.assertEqual(parameter["schema"]["enum"], ["AP-1.0"])
        for path, methods in self.generated["paths"].items():
            for method, operation in methods.items():
                if method not in HTTP_METHODS:
                    continue
                self.assertTrue(any(
                    p.get("name") == "X-Policy-Version" and p.get("required")
                    for p in operation.get("parameters", [])
                ), f"{method.upper()} {path} must require policy version")

    def test_contract_documents_process_local_patch_behavior(self):
        description = self.contract["paths"]["/orders/{orderId}"]["patch"][
            "description"
        ].lower()

        self.assertTrue(
            "process-local" in description
            or "process local" in description
            or "restart" in description,
            "Contract must document that mock API updates are not durable",
        )


if __name__ == "__main__":
    unittest.main()