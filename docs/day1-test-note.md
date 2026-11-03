\# API-Sentinel — Day 1 Test Note



\*\*Role:\*\* Member 5 — Mock API and OpenAPI Engineer  

\*\*Phase:\*\* Foundation  

\*\*Branch:\*\* `member5/mock-api`



\## Objective



Define mock users, roles, orders, and authorization cases.



\## Files



\- `mock\_data/users.json`

\- `mock\_data/orders.json`

\- `mock\_data/authorization\_cases.json`

\- `src/authorization.py`

\- `tests/test\_authorization.py`



\## Authorization rules



\- Active customers can read their own orders.

\- Customers cannot read another customer's orders.

\- Administrators can read and manage orders.

\- Unknown users, inactive users, unknown roles, missing orders, and unsupported actions are denied.



\## Security tests



Normal access, BOLA, BFLA, unknown identity, inactive identity, missing order, and unknown action.



\## Test results



JSON validation: PASS (3 files)
Authorization demo: PASS
Unit tests: PASS (10 tests)
Environment: Windows PowerShell, Python 3.13


\## Limitations



This is a local mock authorization model. HTTP endpoints, database migrations, authentication, and secure tokens are assigned to later project days.



\## Git evidence



Record the actual commit ID and push status after publishing the work.



