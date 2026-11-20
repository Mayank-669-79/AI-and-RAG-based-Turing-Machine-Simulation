# API contract

The canonical request/response examples and shared JSON contracts are in the
root [README](../README.md), Sections 5 and 6.

Required endpoints:
- `GET /api/health`
- `POST /api/machine/generate`
- `POST /api/machine/run`

Member 6 owns the implementation of machine endpoints. Do not change shared
field names without agreement from all module owners.
