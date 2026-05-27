"""Web scraper for extracting text content from web pages by CSS selector."""

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Literal

import requests
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, HTTPError, Timeout

logger = logging.getLogger(__name__)

AuthType = Literal["basic", "bearer", "header", "session"]


@dataclass
class AuthConfig:
    """Authentication configuration for HTTP requests."""

    type: AuthType
    username: str | None = None
    password: str | None = None
    token: str | None = None
    header_name: str | None = None
    header_value: str | None = None
    login_url: str | None = None

    @classmethod
    def from_env(cls) -> "AuthConfig | None":
        """Build an AuthConfig from SCRAPER_* environment variables, or return None."""
        username = os.environ.get("SCRAPER_USERNAME")
        password = os.environ.get("SCRAPER_PASSWORD")
        token = os.environ.get("SCRAPER_TOKEN")
        login_url = os.environ.get("SCRAPER_LOGIN_URL")

        if login_url and username and password:
            return cls(type="session", username=username, password=password, login_url=login_url)
        if token:
            return cls(type="bearer", token=token)
        if username and password:
            return cls(type="basic", username=username, password=password)
        return None


def _build_session(auth: AuthConfig | None) -> requests.Session:
    """Create a requests.Session with authentication pre-configured."""
    session = requests.Session()
    if not auth:
        return session

    if auth.type == "basic":
        session.auth = HTTPBasicAuth(auth.username, auth.password)
    elif auth.type == "bearer":
        session.headers["Authorization"] = f"Bearer {auth.token}"
    elif auth.type == "header":
        session.headers[auth.header_name] = auth.header_value
    elif auth.type == "session":
        session.post(auth.login_url, data={"username": auth.username, "password": auth.password})

    return session


def scrape_titles(
    url: str,
    selectors: list[str] | None = None,
    timeout: int = 10,
    retries: int = 2,
    auth: AuthConfig | None = None,
) -> list[str]:
    """Fetch a webpage and extract text from the first matching CSS selector.

    Tries each selector in order and returns results from the first one that
    matches at least one element. Retries on transient network errors with
    exponential backoff.

    Args:
        url: The URL of the page to scrape.
        selectors: CSS selectors to try in order (default: ["h2"]).
        timeout: Request timeout in seconds.
        retries: Number of retry attempts on transient errors (ConnectionError, Timeout).
        auth: Optional AuthConfig for authenticated requests.

    Returns:
        A list of text content from all matched elements on the page.

    Raises:
        ValueError: If the URL is empty or invalid.
        ConnectionError: If the page cannot be reached after all retries.
        HTTPError: If the server returns an error status code.
        Timeout: If every attempt exceeds the timeout duration.
    """
    if not url or not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL: {url!r}")

    if selectors is None:
        selectors = ["h2"]

    session = _build_session(auth)
    logger.info("Fetching %s", url)

    last_exception: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            break
        except (ConnectionError, Timeout) as exc:
            last_exception = exc
            if attempt < retries:
                wait = 2 ** (attempt - 1)
                logger.warning("Attempt %d/%d failed (%s), retrying in %ds", attempt, retries, type(exc).__name__, wait)
                time.sleep(wait)
            else:
                logger.error("All %d attempts failed for %s", retries, url)
                raise

    soup = BeautifulSoup(response.text, "html.parser")

    for sel in selectors:
        titles = [tag.get_text(strip=True) for tag in soup.select(sel)]
        if titles:
            logger.info("Selector %r matched %d element(s)", sel, len(titles))
            return titles
        logger.debug("Selector %r matched nothing", sel)

    logger.info("No selectors matched any elements on %s", url)
    return []


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape text content from a web page by CSS selector.")
    parser.add_argument("url", help="URL of the page to scrape")
    parser.add_argument(
        "-s", "--selector",
        action="append",
        dest="selectors",
        help="CSS selector to match (can be repeated; tries in order). Default: h2",
    )
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Request timeout in seconds (default: 10)")
    parser.add_argument("-r", "--retries", type=int, default=2, help="Retry attempts on transient errors (default: 2)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    auth_config = AuthConfig.from_env()

    try:
        titles = scrape_titles(
            args.url,
            selectors=args.selectors,
            timeout=args.timeout,
            retries=args.retries,
            auth=auth_config,
        )
        if titles:
            print(f"Found {len(titles)} title(s):")
            for title in titles:
                print(f"  - {title}")
        else:
            print("No elements matched on the page.")
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Timeout:
        print(f"Error: Request to {args.url!r} timed out.", file=sys.stderr)
        sys.exit(1)
    except ConnectionError:
        print(f"Error: Could not connect to {args.url!r}.", file=sys.stderr)
        sys.exit(1)
    except HTTPError as e:
        print(f"Error: Server returned {e.response.status_code} for {args.url!r}.", file=sys.stderr)
        sys.exit(1)
