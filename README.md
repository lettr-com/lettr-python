# Lettr for Python SDK

The official Python SDK for the [Lettr Email API](https://lettr.com). Send transactional emails with tracking, attachments, templates, and personalization.

## Installation

```bash
pip install lettr
```

## Quick Start

```python
import lettr

client = lettr.Lettr("lttr_your_api_key")

client.emails.send(
    from_email="you@example.com",
    to=["user@example.com"],
    subject="Hello from Lettr!",
    html="<h1>Welcome!</h1>",
)
```

## Usage

### Health & Authentication

```python
# Check API health (no authentication required)
health = client.health()
print(health.status)  # "ok"

# Validate your API key
auth = client.auth_check()
print(f"Team: {auth.team_name} (ID: {auth.team_id})")
```

### Sending Emails

```python
import lettr

client = lettr.Lettr("lttr_your_api_key")

# Simple email
response = client.emails.send(
    from_email="sender@example.com",
    to=["recipient@example.com"],
    subject="Hello!",
    html="<h1>Hello</h1><p>Welcome to our service!</p>",
    text="Hello\n\nWelcome to our service!",
)

print(response.request_id)  # "12345678901234567890"
print(response.accepted)    # 1
```

#### With Options

```python
response = client.emails.send(
    from_email="sender@example.com",
    from_name="Acme Inc",
    to=["recipient@example.com"],
    cc=["manager@example.com"],
    bcc=["archive@example.com"],
    reply_to="support@example.com",
    subject="Your Order Confirmation",
    html="<h1>Order Confirmed</h1>",
    text="Order Confirmed",
    tag="order-confirmation",
    headers={"X-Order-Id": "12345"},
    options=lettr.EmailOptions(
        click_tracking=True,
        open_tracking=True,
        transactional=True,
    ),
    metadata={"order_id": "12345"},
)
```

#### With Attachments

```python
import base64

with open("invoice.pdf", "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

response = client.emails.send(
    from_email="billing@example.com",
    to=["customer@example.com"],
    subject="Your Invoice",
    html="<p>Please find your invoice attached.</p>",
    attachments=[
        lettr.Attachment(
            name="invoice.pdf",
            type="application/pdf",
            data=pdf_data,
        )
    ],
)
```

#### Using Templates

```python
response = client.emails.send(
    from_email="hello@example.com",
    to=["user@example.com"],
    template_slug="welcome-email",
    substitution_data={
        "first_name": "John",
        "company": "Acme Inc",
    },
)
```

### Scheduling Emails

```python
# Schedule an email for future delivery
response = client.emails.schedule(
    from_email="sender@example.com",
    to=["recipient@example.com"],
    subject="Scheduled Message",
    html="<p>This was scheduled!</p>",
    scheduled_at="2025-12-01T10:00:00Z",
)
print(f"Scheduled: {response.request_id}")

# Get scheduled email details
detail = client.emails.get_scheduled(response.request_id)
print(f"{detail.subject} ({detail.state}) -> {detail.recipients}")

# Cancel a scheduled email
client.emails.cancel_scheduled("transmission_id")
```

### Listing & Retrieving Emails

```python
# List sent emails
email_list = client.emails.list(per_page=10)
for email in email_list.results:
    print(f"{email.subject} -> {email.rcpt_to}")

# Paginate with cursor
next_page = client.emails.list(cursor=email_list.next_cursor)

# Filter by recipient
filtered = client.emails.list(recipients="user@example.com")

# Filter by date range
filtered = client.emails.list(from_date="2026-01-01", to_date="2026-01-31")

# Get email details (all events for a transmission)
detail = client.emails.get("request_id_here")
print(f"{detail.subject} -> {detail.recipients} ({detail.state})")
for event in detail.events:
    print(f"{event.type}: {event.timestamp}")
```

### Email Events

```python
# List email events with filtering
events = client.emails.list_events(
    events=["delivery", "bounce"],
    recipients=["user@example.com"],
    from_date="2025-01-01",
    to_date="2025-12-31",
    per_page=50,
)

for event in events.results:
    print(f"{event.type}: {event.rcpt_to} at {event.timestamp}")
    if event.geo_ip:
        print(f"  Location: {event.geo_ip.city}, {event.geo_ip.country}")
    if event.user_agent_parsed:
        print(f"  Client: {event.user_agent_parsed.agent_family}")
```

### Domains

```python
# List all domains
domains = client.domains.list()
for domain in domains:
    print(f"{domain.domain} - {domain.status_label}")

# Add a new sending domain
domain = client.domains.create("example.com")
print(domain.dkim)  # DKIM config for DNS setup

# Get domain details (includes DMARC, SPF, DNS provider info)
domain = client.domains.get("example.com")
print(f"DMARC: {domain.dmarc_status}, SPF: {domain.spf_status}")

# Verify DNS records
verification = client.domains.verify("example.com")
print(f"DKIM: {verification.dkim_status}")
print(f"CNAME: {verification.cname_status}")
print(f"DMARC: {verification.dmarc_status}")
print(f"SPF: {verification.spf_status}")

# Delete a domain
client.domains.delete("example.com")
```

### Templates

```python
# List templates
template_list = client.templates.list(per_page=10)
for template in template_list.templates:
    print(f"{template.name} ({template.slug})")

# Create a template
template = client.templates.create(
    name="Welcome Email",
    html="<h1>Hello {{NAME}}!</h1><p>Welcome aboard.</p>",
)

# Get a template
template = client.templates.get("welcome-email")
print(template.html)

# Get template HTML
html = client.templates.get_html(project_id=1, slug="welcome-email")

# Update a template (creates a new version)
template = client.templates.update(
    "welcome-email",
    html="<h1>Hi {{NAME}}!</h1><p>Updated content.</p>",
)

# Get merge tags
merge_tags = client.templates.get_merge_tags("welcome-email")
for tag in merge_tags.merge_tags:
    print(f"{tag.key} (required: {tag.required})")

# Delete a template
client.templates.delete("welcome-email")
```

### Webhooks

```python
# List webhooks
webhooks = client.webhooks.list()
for webhook in webhooks:
    print(f"{webhook.name}: {webhook.url} (enabled: {webhook.enabled})")

# Create a webhook
webhook = client.webhooks.create(
    name="My Webhook",
    url="https://example.com/webhook",
    auth_type="none",
    events_mode="selected",
    events=["message.delivery", "message.bounce", "message.spam_complaint"],
)

# Create with authentication
webhook = client.webhooks.create(
    name="Secure Webhook",
    url="https://example.com/webhook",
    auth_type="basic",
    events_mode="all",
    auth_username="user",
    auth_password="secret",
)

# Update a webhook
webhook = client.webhooks.update(
    "webhook-abc123",
    name="Renamed Webhook",
    active=False,
)

# Get webhook details
webhook = client.webhooks.get("webhook-abc123")

# Delete a webhook
client.webhooks.delete("webhook-abc123")
```

### Projects

```python
# List projects
project_list = client.projects.list()
for project in project_list.projects:
    print(f"{project.emoji} {project.name}")
```

## Error Handling

The SDK raises typed exceptions for all API errors:

```python
import lettr

client = lettr.Lettr("lttr_your_api_key")

try:
    client.emails.send(
        from_email="sender@example.com",
        to=["recipient@example.com"],
        subject="Hello",
        html="<p>Hello!</p>",
    )
except lettr.ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Field errors: {e.errors}")
except lettr.AuthenticationError:
    print("Invalid API key")
except lettr.ForbiddenError:
    print("Access forbidden")
except lettr.NotFoundError as e:
    print(f"Not found: {e.message}")
except lettr.RateLimitError as e:
    print(f"Rate limited: {e.message} (code: {e.error_code})")
except lettr.BadRequestError as e:
    print(f"Bad request: {e.message} (code: {e.error_code})")
except lettr.ServerError as e:
    print(f"Server error: {e.message}")
except lettr.LettrError as e:
    print(f"Unexpected error: {e.message}")
```

### Exception Hierarchy

| Exception | HTTP Status | Description |
|---|---|---|
| `LettrError` | -- | Base exception for all errors |
| `AuthenticationError` | 401 | Missing or invalid API key |
| `ForbiddenError` | 403 | Access forbidden |
| `ValidationError` | 422 | Request validation failed |
| `NotFoundError` | 404 | Resource not found |
| `ConflictError` | 409 | Resource already exists |
| `BadRequestError` | 400 | Invalid domain or request |
| `RateLimitError` | 429 | Quota or rate limit exceeded |
| `ServerError` | 500, 502 | Server-side error |

## Context Manager

Use the client as a context manager to automatically close connections:

```python
with lettr.Lettr("lttr_your_api_key") as client:
    client.emails.send(
        from_email="sender@example.com",
        to=["recipient@example.com"],
        subject="Hello!",
        html="<p>Hello!</p>",
    )
# Connection pool is automatically closed
```

## Requirements

- Python 3.8+
- [httpx](https://www.python-httpx.org/) (installed automatically)

## License

MIT
