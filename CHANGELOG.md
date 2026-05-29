# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/lettr/lettr-python/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/lettr/lettr-python/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/lettr/lettr-python/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/lettr/lettr-python/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/lettr/lettr-python/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/lettr/lettr-python/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/lettr/lettr-python/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/lettr/lettr-python/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/lettr/lettr-python/releases/tag/v0.1.0
