---
description: Sync FastAPI routes and Pydantic schemas to openapi/openapi.yaml and check whether docs/contracts/ needs updating
---

## Your task

Check whether `openapi/openapi.yaml` is in sync with the current code. If there are differences, update it automatically and prompt the user to sync `docs/contracts/` if needed.

## Step 1: Check for differences

Run the following command to compare the spec generated from the current code against `openapi.yaml`:

```
cd apps/api && python ../../scripts/export_openapi.py --check
```

- No output, exit code 0 → already in sync. Inform the user: "openapi.yaml is up to date, no changes needed." Stop here.
- Diff output, exit code 1 → proceed to Step 2.

## Step 2: Show a plain-language diff summary

Read the diff output and explain to the user:
- Which endpoints or fields were added
- Which endpoints or fields were removed
- Which types or descriptions were changed

## Step 3: Update openapi.yaml

Run the following command to write the latest spec to the file:

```
cd apps/api && python ../../scripts/export_openapi.py
```

Confirm that `openapi/openapi.yaml` has been updated.

## Step 4: Check whether docs/contracts/ needs syncing

Read all files under `docs/contracts/` and compare against the changes from Step 2:
- If the changes affect endpoint structure or request/response fields → tell the user which contracts file needs updating and what should be added
- If the changes are description-only → inform the user that contracts do not need updating

## Step 5: Output a summary

Use the following format:

```
openapi-sync complete

Changes:
  Added:    ...
  Modified: ...
  Removed:  ...

openapi/openapi.yaml  ✓ updated
docs/contracts/       [manual update needed: xxx.md] or [no update needed]
```
