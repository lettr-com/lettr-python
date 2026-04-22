# Webhook API changes: namespaced events + `target` → `url` on update

## Context

The Lettr API has changed on the webhook endpoints in two ways:

1. **Event types are now namespaced**, e.g. `message.delivery`, `engagement.click`, `unsubscribe.list_unsubscribe`. Both `POST /webhooks` and `PUT /webhooks/{id}` expect namespaced strings in the `events` field, and `event_types` comes back namespaced in responses.
2. **`PUT /webhooks/{id}` now takes `url` instead of `target`** for changing the webhook endpoint URL. `POST` already uses `url`; this aligns `PUT` with it.

The SDK currently:
- Passes the caller's `events` list straight through as strings, so no validation code needs changing — only docs/tests that still show the old bare names (`delivery`, `bounce`, `spam_complaint`).
- Sends `payload["target"]` from a `target=` kwarg on `webhooks.update()` (`src/lettr/resources/webhooks.py:132,170`), which will break against the new API.

Per user direction: `target` must remain accepted and be marked deprecated (emit `DeprecationWarning`, still map to `url` on the wire). No major version bump.

## Changes

### 1. `src/lettr/resources/webhooks.py` — `update()` method

- Add `url: str | None = None` kwarg alongside the existing `target: str | None = None` (keep `target` for backward compat).
- At the top of the method body, if `target is not None` emit `warnings.warn("The `target` parameter is deprecated; use `url` instead.", DeprecationWarning, stacklevel=2)`. If both are passed, raise `TypeError` (ambiguous).
- Resolve `effective_url = url if url is not None else target`; write `payload["url"] = effective_url` when set. Remove the `payload["target"] = ...` line.
- Update the docstring: document `url` as the new parameter, note `target` is deprecated alias, and in the `events` arg doc mention the namespaced format with one example (e.g. `"message.delivery"`).
- Add `import warnings` at the top.

### 2. `src/lettr/resources/webhooks.py` — `create()` docstring only

- Update the `events` arg docstring to mention namespaced format, matching the same example style. No code change; the field passthrough already works.

### 3. `src/lettr/resources/webhooks.py` — class-level `Usage` docstring

- Leave the example at line 31 alone (it uses `events_mode="all"`, no events list).

### 4. `tests/test_webhooks.py`

- `WEBHOOK_DATA["event_types"]` (line 25): change to `["message.delivery", "message.bounce"]`.
- `TestList.test_list_webhooks` (line 40): update assertion to the namespaced list.
- `TestCreate.test_create_webhook` (lines 62, 72): use namespaced events in input and assertion.
- `TestUpdate.test_update_partial` (lines 126, 128): use namespaced events; assert `payload == {"events": ["message.delivery"]}`.
- Add `TestUpdate.test_update_with_url`: call `webhooks.update("wh_123", url="https://new.example.com/hook")`, assert `payload == {"url": "https://new.example.com/hook"}`.
- Add `TestUpdate.test_update_target_deprecated`: use `pytest.warns(DeprecationWarning)`, call `webhooks.update("wh_123", target="https://legacy.example.com/hook")`, assert the payload still sends `{"url": "https://legacy.example.com/hook"}` (deprecated kwarg, modern wire format).
- Add `TestUpdate.test_update_url_and_target_conflict`: passing both raises `TypeError`.

### 5. `README.md` — Webhooks section

- Line 263: change `events=["delivery", "bounce", "spam_complaint"]` to `events=["message.delivery", "message.bounce", "message.spam_complaint"]`.

### 6. `CHANGELOG.md` — `[Unreleased]`

Add a short entry under `[Unreleased]`:
- **Changed:** Webhook event types are now namespaced (e.g. `message.delivery`, `engagement.click`). Docs/tests updated; the SDK continues to pass `events` strings through unchanged, so callers just need to use the new names.
- **Deprecated:** `webhooks.update(..., target=...)` — use `url=` instead. `target` still works (mapped to `url` in the request body) but emits `DeprecationWarning`.

## Files touched

- `src/lettr/resources/webhooks.py`
- `tests/test_webhooks.py`
- `README.md`
- `CHANGELOG.md`

## Files intentionally NOT touched

- `src/lettr/_types.py` — `Webhook.event_types: list[str] | None` already accepts namespaced strings; no schema change.
- `_parse_webhook()` at `src/lettr/resources/webhooks.py:12` — reads `event_types` passthrough; already correct for the new format.

## Verification

1. `uv run --extra dev pytest tests/test_webhooks.py -v` — all existing tests pass with namespaced data; new `url` / `target`-deprecation / conflict tests pass.
2. `uv run --extra dev pytest` — full suite stays green (no other file depends on webhook event naming).
3. `uv run --extra dev python -c "import warnings; warnings.simplefilter('error', DeprecationWarning); from unittest.mock import MagicMock; from lettr.resources.webhooks import Webhooks; w = Webhooks(MagicMock()); w._client.put.return_value = {'data': {'id':'x','name':'n','url':'u','enabled':True,'auth_type':'none','has_auth_credentials':False}}; w.update('x', target='https://t')"` — should raise `DeprecationWarning` (proves the warning fires).
4. Manually spot-check the README snippet renders the new event names.
