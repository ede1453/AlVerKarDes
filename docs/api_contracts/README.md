# API Contract Snapshots

This folder stores compact OpenAPI contract snapshots.

Purpose:

```text
Detect accidental breaking API changes before release.
```

The snapshot guard focuses on:

- removed paths
- removed methods
- changed operationId values
- removed response status codes

Allowed non-breaking changes:

- new paths
- new methods
- additional response status codes
