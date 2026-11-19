"""Small, polite HTTP client used by the capture script.

The capture runs on a scheduled GitHub Actions runner. It therefore needs a
working HTTPS client with a stable user agent, a retry policy and SHA-256
hashing of every byte it receives. Nothing in this module interprets a page;
it only moves bytes and records what it moved.
"""

from __future__ import annotations

import hashlib
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

USER_AGENT = (
    "Mozilla/5.0 (compatible; Own6 NFL research capture; "
    "+https://github.com/sassnarep3-star/Own6)"
)

DEFAULT_DELAY_SECONDS = 1.5


@dataclass
class FetchResult:
    """One HTTP response, kept with enough provenance to be re-checked."""

    url: str
    status: int
    content_type: str
    body: bytes
    fetched_at_utc: str
    sha256: str = ""
    error: str = ""
    headers: dict = field(default_factory=dict)
    final_url: str = ""

    @property
    def ok(self) -> bool:
        return self.status == 200 and not self.error

    def text(self, errors: str = "replace") -> str:
        return self.body.decode("utf-8", errors)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(
    url: str,
    *,
    timeout: int = 60,
    retries: int = 3,
    delay: float = DEFAULT_DELAY_SECONDS,
    user_agent: str = USER_AGENT,
    sleep=time.sleep,
) -> FetchResult:
    """GET ``url`` and return the bytes with their hash and read time.

    A failed attempt is retried with a fixed back-off. The last error is kept
    on the result rather than raised, so a partial capture still produces an
    honest log instead of aborting.
    """
    last_error = ""
    status = 0
    content_type = ""
    body = b""
    headers: dict = {}
    for attempt in range(retries):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = int(response.status)
                content_type = response.headers.get("Content-Type", "")
                body = response.read()
                headers = dict(response.headers.items())
                final_url = response.geturl()
            if status == 200:
                sleep(delay)
                return FetchResult(
                    url=url,
                    status=status,
                    content_type=content_type,
                    body=body,
                    fetched_at_utc=utc_now_iso(),
                    sha256=sha256_hex(body),
                    headers=headers,
                    final_url=final_url,
                )
            last_error = f"http_status_{status}"
        except urllib.error.HTTPError as exc:  # pragma: no cover - network dependent
            status = int(exc.code)
            last_error = f"http_error_{exc.code}"
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = f"{type(exc).__name__}: {exc}"
        if attempt + 1 < retries:
            sleep(delay * (attempt + 1))
    return FetchResult(
        url=url,
        status=status,
        content_type=content_type,
        body=body,
        fetched_at_utc=utc_now_iso(),
        sha256=sha256_hex(body) if body else "",
        error=last_error,
        headers=headers,
    )
