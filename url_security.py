"""Safe public-URL fetching and visible-text extraction for SATARK."""
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse
from urllib.request import Request, HTTPRedirectHandler, build_opener

from satark_utils import safe_text

class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())

    def text(self):
        return "\n".join(self.parts)


def is_public_url(url):
    """Allow only HTTP(S) URLs whose resolved addresses are all globally routable.

    Fail closed on DNS errors and malformed URLs. This is a defense-in-depth
    check; deployments should additionally enforce outbound network policy.
    """
    try:
        parsed = urlparse(safe_text(url))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username is not None or parsed.password is not None:
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
            return False
        # Avoid ambiguous/non-standard ports and schemes in this fetcher.
        if parsed.port is not None and not (1 <= parsed.port <= 65535):
            return False
        addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80),
                                       type=socket.SOCK_STREAM)
        if not addresses:
            return False
        for item in addresses:
            ip = ipaddress.ip_address(item[4][0])
            if not ip.is_global:
                return False
        return True
    except (socket.gaierror, ValueError, OSError):
        return False


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_public_url(newurl):
            raise ValueError("The URL redirects to a private or unsafe network address.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url_text(url):
    url = safe_text(url)
    if not is_public_url(url):
        raise ValueError("For safety, only public HTTP/HTTPS URLs can be fetched.")
    request = Request(url, headers={"User-Agent":"SATARK-Security-Analyzer/2.0", "Accept":"text/html,application/xhtml+xml,text/plain"})
    opener = build_opener(SafeRedirectHandler())
    with opener.open(request, timeout=12) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        raw = response.read(1_500_000)
        final_url = response.geturl()
    if not is_public_url(final_url):
        raise ValueError("The final URL is not a public address and was blocked.")
    if "text" not in content_type and "html" not in content_type and "xml" not in content_type:
        return raw.decode("utf-8", errors="ignore")[:12000]
    parser = VisibleTextParser()
    parser.feed(raw.decode("utf-8", errors="ignore"))
    text = parser.text() or raw.decode("utf-8", errors="ignore")
    return text[:30000]
