# APIsenX — Day 3 Test Note

**Task:** Mock API Implementation  
**Branch:** `member5/mock-api`  
**Date:** 2026-10-12

## Implemented

- Created `mock-api/main.py` using FastAPI.
- Implemented `GET /orders`.
- Implemented `GET /orders/{orderId}`.
- Implemented `PATCH /orders/{orderId}`.
- Implemented `GET /admin/orders`.
- Reused the existing authorization module and JSON fixtures.
- Added local demo bearer-token authentication.
- Added structured error responses and authorization audit logs.
- Added automated API tests in `tests/test_mock_api.py`.

## Verification

- Existing authorization tests: 10 passed.
- Mock API tests: 10 passed.
- Total: 20 passed, 0 failed.
- Customer can access only their own orders.
- Cross-user order access is denied with HTTP 403.
- Missing and invalid credentials are rejected with HTTP 401.
- Customer access to administrative operations is denied.
- Invalid order-update fields are rejected.

## Limitations

- Demo bearer tokens are for local testing only.
- Order updates are not persisted to the JSON fixtures.
- Sharing grants and production-grade JWT validation are not implemented.

## Result

The local mock API starts successfully on port 8000. All 20 automated tests passed in the recorded test run.

Next: review the implementation, verify the OpenAPI contract against the running API, and commit the Day 3 deliverables.
