# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.7.0] - 2026-09-22

Lettr now owns the schedule for scheduled emails. It used to hand them straight to SparkPost, so the "scheduled transmission" was the provider's object and the provider's id was the only id there was. SparkPost retired per-transmission GET and DELETE, which would have taken read and cancel down with it, so Lettr keeps the email itself and only hands it over when it is due. That moves the id, adds a second one, and gives cancel something to return - so this release is **not** purely additive.

### Changed

- **`emails.schedule()` returns `ScheduledEmail`**, not `SendEmailResponse`. The API now answers a create with the whole record rather than `{request_id, accepted, rejected}`, so there is no reason to make a caller fetch what it was already told. `result.request_id` and `result.accepted` still read the same; anything annotated `SendEmailResponse` needs its type updated.
- **`emails.cancel_scheduled()` returns the cancelled `ScheduledEmail`** instead of `None`. It is how you confirm the cancel landed - `state` is `"cancelled"` and `accepted` has dropped to 0 - without a second round trip. Code that ignores the return value is unaffected.
- **`get_scheduled()` and `cancel_scheduled()` take `request_id`, renamed from `transmission_id`.** Positional callers are unaffected. The rename is the point: `transmission_id` now names a *different* field on the same object, and passing one where a `request_id` belongs is a 404, so the old parameter name would have sent callers to the wrong value.
- **`ScheduledEmail.transmission_id` is now `str | None`.** It is the *provider's* id, and the provider has not seen the email until it is due, so it is `None` for the whole life of a scheduled email and fills in only once it is sent.

### Added

- **`ScheduledEmail.request_id`** - Lettr's own id, `sch_`-prefixed, and the one that addresses the email in `get_scheduled()` and `cancel_scheduled()`.

  The two ids are not interchangeable and neither is redundant: `request_id` addresses the email, while `transmission_id` is the value that appears on **webhook events**, so it is the one to correlate incoming webhooks against. An integration that reacts to delivery has to keep both and join them.
- **`ScheduledEmail.accepted`, `.rejected`, `.tag` and `.failure_reason`**, mirroring what the API returns. `failure_reason` is set only in the `"failed"` state.
- **`emails.list_scheduled(status=..., per_page=..., page=...)`** returning a `ScheduledEmailPage` - the emails plus the usual `total` / `per_page` / `current_page` / `last_page`. Previously the only handle on a scheduled email was an id you had stored yourself, and losing it meant losing the email. `status` takes any of the five states, `per_page` is 1-100 (default 25), `page` is 1-based.
- **`ScheduledEmailState`** - `"scheduled" | "sending" | "sent" | "cancelled" | "failed"`, the type of the `status` filter. Only `"scheduled"` is still cancellable; `"sending"` means the handover has already started.

  `ScheduledEmail.state` itself stays a plain `str`, deliberately. A legacy read (below) derives its state from delivery events and can answer `"delivered"` or `"bounced"`, neither of which is one of Lettr's five - narrowing the field to the Literal would turn a correct `== "delivered"` check into a type error.
- **`schedule(scheduled_at=...)` accepts a `datetime`** as well as an ISO 8601 string, rendered with `.isoformat()`, matching `campaigns.schedule()`. Include a timezone offset; naive values are read as UTC.

### Fixed

- **Reading a pre-rework scheduled email no longer raises `KeyError`.** An old SparkPost transmission id passed to `get_scheduled()` is still answered, but out of delivery events and in the older nine-key shape: no `request_id`, and none of `accepted`, `rejected`, `tag` or `failure_reason`. The parser demanded those keys, so every such read crashed. They are all optional now, and `request_id` falls back to `transmission_id` so it always holds the id that addresses the email you asked about, whichever shape came back.

### Notes

- **The scheduling window is 5 minutes to 30 days**, now documented on `schedule()`. The API enforces it; `schedule()` still does no local validation of any kind, so a value outside the window raises `ValidationError` from the response rather than before the request goes out.

## [1.6.0] - 2026-09-10

Brings this client level with lettr-php: template modules, the folders endpoint, preparation status, and idempotent sends. Everything is additive - code written against 1.5.1 keeps working and sends identical requests.

### Added

- **`client.folders.list()`** - the folders templates are filed into, each with its `purpose` and `templates_count`. This is what `templates.create(folder_id=...)` was missing: nothing else returned a folder id, so a caller either omitted it and accepted whichever folder the API picked, or hardcoded an integer read out of an app URL. Read-only by design - deleting a folder moves or deletes the templates inside it, so that stays in the app.
- **Template `purpose`** (`"transactional" | "campaign"`) on create and on every template response, plus a `purpose` filter on `list()`. Only campaign templates can be picked by the campaign builder; only transactional ones can be sent as single emails.
- **`preparation_status`** (`"pending" | "ready" | "failed"`) on every template response. Creating or updating a template defers image migration and HTML rendering to a background job; this says whether the content you sent is the content that will go out.

  It is **not** the same question as "can I send this": after an *update* the previous render stays in place, so a `"pending"` template is still sendable - it is serving the old content.

  A response without the key reads as `"ready"`, not `"pending"` - it comes from an API deployment that predates the field, where every template with HTML was simply usable, and `"pending"` would look like a stalled queue.
- **`templates.list(folder_id=...)`** - one `per_page=100` call reconciles a whole bulk import instead of a detail call per template, each dragging the full HTML payload against the same rate limit. A folder outside the resolved project raises `NotFoundError` rather than returning an empty list, so a typo cannot be misread as "nothing is there yet".
- **`emails.send(..., idempotency_key=...)`** - reuse the key when you retry and the API returns the original result instead of delivering a second email. `SendEmailResponse` gained `replayed`, true when that happened.

  **You choose the key; the SDK never generates one.** It only works if both attempts use the same value, and the SDK does not retry - one `send()` is one HTTP request - so the retry is yours, and only you know two calls are the same logical send. A key generated inside `send()` would differ on every attempt and protect nothing.

  A malformed key raises `ValidationError` **before any request goes out**. `is_valid_idempotency_key()` is exported for callers deriving keys from their own ids.
- **`IdempotencyInProgressError`** and **`IdempotencyConflictError`**, both subclasses of `ConflictError`, because one is safe to retry and the other is not. The first carries `retry_after` and must be retried with the *same* key; the second means that key was used with a different payload and will fail identically forever.

### Notes

- Keys are scoped per team **and** API key, so the same string through a different API key is a different key. The provider retains one for 24 hours.
- `ApiClient` gained `request_with_headers()` / `post_with_headers()` for the one place a response header carries meaning. `request()` and `post()` are unchanged.
- `raise_for_status()` takes an optional third `headers` argument. Existing two-argument calls behave exactly as before.

## [1.5.1] - 2026-08-15

### Fixed
- Corrected the segment condition documentation on `SegmentConditionGroup`: conditions **within a group** are joined by `OR`, and **groups** are joined by `AND` — i.e. `(A OR B) AND (C OR D)`. The previous docstring stated the inverse. No behaviour change — the API has always evaluated segments this way, and no code paths were touched. Worth a read if you built a segment against the old description, since it may target a wider or narrower audience than you intended.

## [1.5.0] - 2026-08-14

Covers the reworked bulk contact import (TPL-2105) and the duplicate-create fix.
Everything here is additive — code written against 1.4.0 keeps working and sends
the exact same payloads.

### Added
- **Per-contact bulk create.** `client.audience.contacts.bulk_create()` accepts a
  second request shape where each contact carries its own properties, lists and
  topic subscriptions, alongside the original flat `emails` list:

  ```python
  client.audience.contacts.bulk_create(
      contacts=[
          BulkContactRow(email="cara@example.com", properties={"plan": "pro"}),
          BulkContactRow(
              email="dan@example.com",
              topics=[TopicSubscription.opt_out("01h-promos")],
          ),
      ],
      list_ids=["01h-everyone"],
  )
  ```

  `emails` is now optional, so exactly one of `emails`/`contacts` must be given —
  an empty call raises `ValueError` instead of being sent to the API.
- New request types `BulkContactRow` (`email`, `properties`, `list_ids`,
  `topics`) and `TopicSubscription` (`id` + state, with the
  `TopicSubscription.opt_in()` / `.opt_out()` constructors), plus the
  `TopicSubscriptionState` literal (`"opt_in"` / `"opt_out"`).

  `TopicSubscriptionState` is what a request should *do* with a topic, and is
  deliberately separate from a topic's `default_subscription`, which describes
  how the topic behaves for a contact that says nothing. An `opt_out` on a topic
  whose default is opt-out suppresses the auto-subscription in the same request
  instead of needing a second call.
- **Batch-wide `list_ids` and `topics`,** plus `update_existing`, on
  `bulk_create()`. Batch-wide lists and topics are unioned into every row; a
  row-level property key or `opt_out` wins over the batch-wide value.
  `update_existing=True` merges properties (submitted keys overwrite, absent keys
  are preserved) and allows dropping a subscription. It is only sent when `True`,
  so legacy payloads stay byte-identical.
- **Bulk create now reports what happened per row.** `BulkContactImportResult`
  gains `updated`, `error_count`, `errors` (`BulkContactError` — `index`,
  `email`, `error_code`, `error`) and `contacts` (`BulkContactRef` — `id`,
  `email`, `created`), plus the `has_errors` and `contact_ids` properties and
  `id_for(email)`. `created` and `already_existed` keep their exact meaning, and
  the new fields default when the API omits them, so the result also parses a
  pre-TPL-2105 response.

  A bulk create can **partially succeed**: rows that fail validation are skipped
  and returned in `errors` while the rest of the batch commits, and the call
  still returns HTTP 201. Check `result.has_errors` — a call that does not raise
  does not mean every row landed.

  Note that `already_existed` and `updated` overlap by design. They answer
  different questions ("was the address already in the audience?" vs "did this
  request change the contact?"), so they do not sum to the row count: a contact
  that already existed and got attached to a list is counted in both.
- `BulkContactErrorCode` literal (`missing_email`, `invalid_email`,
  `invalid_property_value`, `unknown_property_key`, `unknown_list`,
  `unknown_topic`, `invalid_topic_subscription`). `BulkContactError.error_code`
  is typed as a union with `str`, so a code added server-side still parses.
- **Bulk topic subscribe/unsubscribe** — two methods on
  `client.audience.contacts`, mirroring the existing
  `bulk_attach_lists()` / `bulk_detach_lists()` pair:
  - `bulk_subscribe_topics(contact_ids=..., topic_ids=...)` —
    `POST /audience/contacts/topics/bulk`, returns `BulkTopicsSubscribeResult`
    (`subscribed`, `already_subscribed`, `total_pairs`).
  - `bulk_unsubscribe_topics(contact_ids=..., topic_ids=...)` —
    `DELETE /audience/contacts/topics/bulk` with a request body, returns
    `BulkTopicsUnsubscribeResult` (`unsubscribed`, `total_pairs`). Pairs that do
    not exist are ignored.

  Both process every `contact_ids` × `topic_ids` combination (up to 1000 × 50).
  Feed them `result.contact_ids` from a bulk create — no id lookup needed.
- `ContactAlreadyExistsError` — raised by `client.audience.contacts.create()`
  when the email is already in the team's audience. It carries the colliding
  `.email`. This is a client-correctable condition, **not** an outage: do not
  retry it; update the existing contact with `update()`, or use
  `bulk_create(update_existing=True)`.

### Changed
- Creating a contact whose email already exists now raises
  `ContactAlreadyExistsError` (HTTP 409, `resource_already_exists`). The API
  previously let this escape as HTTP 500 with the misleading `send_error` code,
  which arrived as a `ServerError`. **If your retry policy retries 5xx, duplicate
  creates are no longer retried** — which was pointless anyway. Any error mapping
  or docs of yours that name `send_error` for this endpoint should be corrected.
  `ContactAlreadyExistsError` subclasses `ConflictError`, so existing
  `except ConflictError` / `except LettrError` handlers catch it unchanged, and a
  409 with any other error code stays a plain `ConflictError`.

## [1.4.0] - 2026-05-28

### Added
- `CampaignDetail` type — a `Campaign` subclass that adds the rendered
  `html_content` field. Returned by `client.campaigns.get(id)`.

### Changed
- `client.campaigns.get(id)` is now typed as returning `CampaignDetail`
  (previously `Campaign`). `CampaignDetail` inherits from `Campaign`, so
  existing callers that read summary fields keep working unchanged.

### Removed
- `Campaign.html_content` — moved to `CampaignDetail`. The field was only
  ever populated by `get()`; on `list()` / `send()` / `schedule()` /
  `unschedule()` it was always `None`, so reading it on those return
  values was a dead branch the type system silently encouraged. Move
  any `html_content` access to a `get()` result.

## [1.3.0] - 2026-05-27

### Added
- Campaigns API — wraps the `/campaigns` endpoints under `client.campaigns`:
  - `list` — paginated, with an optional `status` filter
  - `get` — single campaign including rendered `html_content`
  - `list_events` — cursor-paginated engagement events, with
    `event_type` / `email` / `start_date` / `end_date` / `limit` filters
  - `send` — send a campaign now
  - `schedule` — schedule a campaign (`scheduled_at`, ISO 8601, future)
  - `unschedule` — cancel a scheduled send
  `send` / `schedule` / `unschedule` return the updated `Campaign`, or `None`
  in the rare case the API omits it (e.g. the campaign was concurrently
  deleted).

## [1.2.0] - 2026-05-26

### Added
- Audience API — wraps all `/audience/*` endpoints under
  `client.audience.<sub>`:
  - `client.audience.lists` — list, get, create, update, delete, bulk_delete
  - `client.audience.contacts` — list (with `search`/`status`/`list_id`/
    `segment_id` filters), get, create (with optional `double_opt_in`),
    update, delete, bulk_create, plus membership ops `add_to_list` /
    `remove_from_list` / `subscribe_to_topic` / `unsubscribe_from_topic`
    (keyword-only to prevent `contact_id` / `list_id` transposition) and
    `bulk_attach_lists` / `bulk_detach_lists`
  - `client.audience.topics` — list, get, create, update, delete
  - `client.audience.properties` — list, get, create, update, delete
  - `client.audience.segments` — list (with `list_id` filter), get, create,
    update, delete
- `UNSET` sentinel exported from `lettr` — pass to `topics.update`,
  `properties.update`, or `segments.update` to leave a field unchanged;
  pass `None` to explicitly clear a nullable field (`description`,
  `fallback_value`, `list_id`).
- `ApiClient.patch()` method and `json` body support on `ApiClient.delete()`
  to back the new audience endpoints (PATCH for updates, DELETE with a
  body for bulk endpoints).

### Notes
- `audience/confirm/{token}` is intentionally not wrapped (intended for
  end-user confirmation flow, not SDK usage).

## [1.1.0] - 2026-04-22

### Changed
- Webhook event types are now namespaced (e.g. `message.delivery`,
  `engagement.click`, `unsubscribe.list_unsubscribe`). The SDK continues to
  pass `events` strings through unchanged, so callers just need to switch to
  the new names. Docs and tests updated accordingly.
- `webhooks.update()` now sends the webhook URL as `url` instead of `target`
  to match the updated API.

### Deprecated
- `webhooks.update(..., target=...)` — use `url=` instead. `target` still
  works (mapped to `url` in the request body) but emits a
  `DeprecationWarning`. Passing both raises `TypeError`.

## [1.0.0] - 2026-04-20

### Changed
- Marked the SDK as stable (1.0.0). No code-behavior changes since 0.3.0;
  this release commits to the current public API under semantic versioning.
  Breaking changes will require a 2.0.0.

## [0.3.0] - 2026-04-20

### Changed
- Synced with the latest OpenAPI spec: `ListEmailsResponse` and
  `ListProjectsResponse` no longer carry a top-level `success` flag;
  `ErrorCode` gained `retrieval_error`, `insufficient_scope`, and
  `schedule_cancellation_failed`; the webhook event-type typo
  `engagament.*` was corrected to `engagement.*`. No SDK behavior
  change — `error_code` values and webhook `events` strings continue
  to accept any value, so callers don't need to update their code.

### Fixed
- `emails.list()`, `emails.get()`, and `emails.list_events()` were reading
  responses at the wrong nesting level and silently returned empty results
  when the API actually had data. Now correctly read from
  `data.events.data` (list endpoints) and `data.events` (detail endpoint),
  matching the OpenAPI spec.
- `emails.schedule()` crashed with `KeyError: 'transmission_id'` because
  it parsed the wrong response shape. Per the spec, the endpoint returns
  the same envelope as `POST /emails` (`request_id`, `accepted`,
  `rejected`), not a full transmission detail.
- `emails.get_scheduled()` was using the wrong `ScheduledEmail` shape
  (missing required `recipients`/`events`; `events` was typed as
  `list[str]` instead of `list[EmailEvent]`).
- `Lettr.auth_check()` crashed with `KeyError: 'team_name'` — the spec
  returns `team_id` + `timestamp`, not `team_name`.
- `Lettr.health()` now also surfaces the `timestamp` field returned by
  the API.
- `domains.create()` (and any future endpoint returning a DKIM object)
  no longer crashes when the API returns unknown DKIM fields. All nested
  dataclass parsers (`DkimInfo`, `DmarcValidationResult`,
  `SpfValidationResult`, `GeoIp`, `UserAgentParsed`) now silently ignore
  unknown keys instead of raising `TypeError`.
- Added `signing_domain` field to `DkimInfo` (was missing from the SDK
  but present in the spec).

### Changed (breaking)
- `EmailDetail` dataclass reshaped to match the spec. Was
  `{ results: list[EmailEvent], total_count: int }`; now has
  `transmission_id`, `state`, `from_email`, `subject`, `recipients`,
  `num_recipients`, `events`, plus optional `scheduled_at` and `from_name`.
  Code that did `detail.results` should use `detail.events`.
- `EmailList` and `EmailEventList` gained `date_from` / `date_to` fields
  exposing the query window returned by the API.
- `ScheduledEmail` dataclass reshaped to match the spec (same shape as
  `EmailDetail`): required fields are now `transmission_id`, `state`,
  `from_email`, `subject`, `recipients`, `num_recipients`, `events`;
  removed the spurious `created_at`; `events` is now
  `list[EmailEvent]` (was `list[str]`).
- `emails.schedule()` now returns `SendEmailResponse` (not
  `ScheduledEmail`). Use `emails.get_scheduled(request_id)` to retrieve
  the full transmission detail afterwards.
- `AuthCheck` dataclass: `team_name` removed, `timestamp` added (matches
  the spec).
- `HealthCheck` dataclass: added required `timestamp` field.

## [0.2.0]

### Added
- `client.health()` — check API health (no auth required)
- `client.auth_check()` — validate API key and get team info
- `client.emails.list_events()` — list email events with filtering
- `client.emails.schedule()` — schedule email for future delivery
- `client.emails.get_scheduled()` / `cancel_scheduled()` — manage scheduled emails
- `client.webhooks.create()` / `update()` / `delete()` — full webhook CRUD
- `client.templates.get_html()` — retrieve rendered template HTML
- `tag` and `headers` parameters to `emails.send()`
- `from_date` / `to_date` query params to `emails.get()`
- `ForbiddenError` (403) and `RateLimitError` (429) exceptions
- New types: `HealthCheck`, `AuthCheck`, `GeoIp`, `UserAgentParsed`,
  `EmailEventList`, `ScheduledEmail`, `DmarcValidationResult`,
  `SpfValidationResult`
- `dmarc_status`, `spf_status`, `is_primary_domain`, `dns_provider` fields
  on `Domain`; `dmarc` / `spf` validation objects on `DomainVerification`
- `perform_substitutions` option on `EmailOptions`
- Additional event fields (`campaign_id`, `template_id`, geo/user-agent, etc.)
  on `EmailEvent`
- Comprehensive test suite (72 tests)

### Changed
- `emails.send()` — `subject` is now optional (required only when not using
  a template)
- `ScheduledEmail.id` → `transmission_id` to match spec
- Bumped minimum SDK version to 0.2.0

### Removed
- `campaign_id` kwarg from `emails.send()` and `emails.schedule()` — not
  part of the spec's send request schema

## [0.1.0]

### Added
- Initial release
- `Lettr` client with resource-based API (`emails`, `domains`, `templates`,
  `webhooks`, `projects`)
- Bearer token authentication, context manager support
- Typed exception hierarchy (`LettrError`, `AuthenticationError`,
  `ValidationError`, `NotFoundError`, `ConflictError`, `BadRequestError`,
  `ServerError`)

[Unreleased]: https://github.com/lettr/lettr-python/compare/v1.7.0...HEAD
[1.7.0]: https://github.com/lettr/lettr-python/compare/v1.6.0...v1.7.0
[1.6.0]: https://github.com/lettr/lettr-python/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/lettr/lettr-python/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/lettr/lettr-python/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/lettr/lettr-python/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/lettr/lettr-python/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/lettr/lettr-python/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/lettr/lettr-python/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/lettr/lettr-python/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/lettr/lettr-python/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/lettr/lettr-python/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lettr/lettr-python/releases/tag/v0.1.0
