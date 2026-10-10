"""Safe public-URL fetching and visible-text extraction for SATARK.

The fetcher fails closed on malformed URLs, private/reserved DNS answers,
unsafe redirects, oversized responses, and non-web content. It is still a
defense-in-depth control: deployments should also enforce outbound network
policy at the infrastructure layer.
"""

import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, HTTPRedirectHandler, build_opener

from config import (
    URL_FETCH_TIMEOUT_SECONDS,
    URL_MAX_BYTES,
    URL_MAX_REDIRECTS,
    URL_MAX_TEXT_CHARS,
    URL_USER_AGENT,
)
from satark_utils import safe_text


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self._skip_tags = []
        self._ignored_tags = {"script", "style", "noscript", "svg"}

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self._skip_tags:
            self._skip_tags.append(tag)
        elif tag in self._ignored_tags:
            self._skip_tags.append(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self._skip_tags and tag == self._skip_tags[-1]:
            self._skip_tags.pop()

    def handle_data(self, data):
        if not self._skip_tags and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return "\\n".join(self.parts)


def _resolved_global_addresses(host, port):
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses:
        return []
    result = []
    for item in addresses:
        try:
            result.append(ipaddress.ip_address(item[4][0]))
        except (ValueError, IndexError):
            return []
    return result


def is_public_url(url):
    """Return True only for HTTP(S) URLs resolving exclusively to global IPs."""
    try:
        parsed = urlparse(safe_text(url))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
            return False
        if parsed.port is not None and not (1 <= parsed.port <= 65535):
            return False
        addresses = _resolved_global_addresses(host, parsed.port or (443 if parsed.scheme == "https" else 80))
        return bool(addresses) and all(ip.is_global for ip in addresses)
    except (socket.gaierror, ValueError, OSError):
        return False


class SafeRedirectHandler(HTTPRedirectHandler):
    """Validate every redirect and enforce a finite redirect budget."""
    def __init__(self, max_redirects=URL_MAX_REDIRECTS):
        super().__init__()
        self.max_redirects = max_redirects
        self.redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirect_count += 1
        if self.redirect_count > self.max_redirects:
            raise ValueError("The URL exceeded SATARK's redirect safety limit.")
        if not is_public_url(newurl):
            raise ValueError("The URL redirects to a private or unsafe network address.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_text(url):
    url = safe_text(url)
    if not is_public_url(url):
        raise ValueError("For safety, only public HTTP/HTTPS URLs can be fetched.")
    request = Request(
        url,
        headers={
            "User-Agent": URL_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain",
            "Accept-Encoding": "identity",
        },
    )
    redirect_handler = SafeRedirectHandler()
    opener = build_opener(redirect_handler)
    with opener.open(request, timeout=URL_FETCH_TIMEOUT_SECONDS) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        declared_length = response.headers.get("Content-Length")
        try:
            if declared_length is not None and int(declared_length) > URL_MAX_BYTES:
                raise ValueError("The remote response is larger than SATARK's safety limit.")
        except ValueError as exc:
            if "larger than" in str(exc):
                raise
        raw = response.read(URL_MAX_BYTES + 1)
        if len(raw) > URL_MAX_BYTES:
            raise ValueError("The remote response is larger than SATARK's safety limit.")
        final_url = response.geturl()
    if not is_public_url(final_url):
        raise ValueError("The final URL is not a public address and was blocked.")
    # Never decode arbitrary binary payloads as text. SATARK's URL workflow is
    # for visible web/text content, not file downloads or content sniffing.
    accepted_types = ("text/html", "application/xhtml+xml", "text/plain", "application/xml", "text/xml")
    media_type = content_type.split(";", 1)[0].strip()
    if media_type not in accepted_types:
        raise ValueError(
            "SATARK only reads public HTML, XML, or plain-text pages. "
            "This URL returned an unsupported content type."
        )
    decoded = raw.decode("utf-8", errors="replace")
    if media_type == "text/plain":
        return decoded[:URL_MAX_TEXT_CHARS]
    parser = VisibleTextParser()
    parser.feed(decoded)
    parser.close()
    text = parser.text() or decoded
    return text[:URL_MAX_TEXT_CHARS]
