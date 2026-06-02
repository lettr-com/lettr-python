# Lettr for Python SDK

The official Python SDK for the [Lettr Email API](https://lettr.com). A clean, typed client for emails, templates, domains, webhooks, audience, and campaigns — methods raise typed exceptions on failure.

## Installation

```bash
pip install lettr
```

## Quick Start

```python
import lettr

client = lettr.Lettr("lttr_your_api_key")

response = client.emails.send(
    from_email="you@example.com",
    to=["user@example.com"],
    subject="Hello from Lettr!",
    html="<h1>Welcome!</h1>",
)

print(response.request_id)
```

Use the client as a context manager to close the connection pool automatically:

```python
with lettr.Lettr("lttr_your_api_key") as client:
    client.emails.send(from_email="you@example.com", to=["user@example.com"],
                       subject="Hello!", html="<p>Hello!</p>")
```

## Error Handling

The SDK raises typed exceptions — all subclasses of `lettr.LettrError`:

```python
try:
    client.emails.send(from_email="you@example.com", to=["user@example.com"],
                       subject="Hello", html="<p>Hello!</p>")
except lettr.ValidationError as e:
    print(e.message, e.errors)
except lettr.LettrError as e:
    print(e.message)
```

See [Error Handling](https://docs.lettr.com/quickstart/python/advanced#error-handling) for the full exception hierarchy.

## Documentation

Full guides for every resource, with complete request/response details, live in the docs:

📚 **[docs.lettr.com/quickstart/python](https://docs.lettr.com/quickstart/python/quickstart)**

| Topic | Guide |
|-|-|
| Install, client setup, sending | [Quickstart](https://docs.lettr.com/quickstart/python/quickstart) |
| Async, Django, error handling, type hints | [Advanced](https://docs.lettr.com/quickstart/python/advanced) |
| Manage Lettr templates & merge tags | [Templates](https://docs.lettr.com/quickstart/python/templates) |
| Add, verify, and manage sending domains | [Domains](https://docs.lettr.com/quickstart/python/domains) |
| Webhook endpoints for delivery & engagement events | [Webhooks](https://docs.lettr.com/quickstart/python/webhooks) |
| Lists, contacts, topics, properties, segments | [Audience](https://docs.lettr.com/quickstart/python/audience) |
| List, send, and schedule campaigns | [Campaigns](https://docs.lettr.com/quickstart/python/campaigns) |
| Flask & FastAPI integration | [Flask](https://docs.lettr.com/quickstart/python/send-with-flask) · [FastAPI](https://docs.lettr.com/quickstart/python/send-with-fastapi) |
| Endpoint reference (params & schemas) | [API Reference](https://docs.lettr.com/api-reference/introduction) |

## Requirements

- Python 3.8+
- [httpx](https://www.python-httpx.org/) (installed automatically)

## License

MIT
