"""Browser + scraper nodes. Only fetches URLs the workflow author or
end-user supplies. No crawling, no unauthenticated scanning.
Uses httpx + a light HTML-to-text pass (BeautifulSoup if present).
"""
import re, httpx

def _strip_html(html):
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text("\n", strip=True)
    except ImportError:
        text = re.sub(r"<script.*?</script>", "", html, flags=re.S)
        text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        return re.sub(r"\s+", " ", text).strip()

def scrape_url(url, timeout=30):
    if not url.startswith(("http://", "https://")):
        raise ValueError("scrape_url requires an http(s) URL supplied by the user")
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": "AI-Operations-Center/0.1"}) as c:
        r = c.get(url)
        r.raise_for_status()
        return {"url": str(r.url), "status": r.status_code, "text": _strip_html(r.text)[:20000],
                "title": re.search(r"<title>(.*?)</title>", r.text, re.S).group(1).strip() if re.search(r"<title>(.*?)</title>", r.text, re.S) else ""}

def redirect_chain(url, timeout=30):
    chain = []
    with httpx.Client(timeout=timeout, follow_redirects=False, headers={"User-Agent": "AI-Operations-Center/0.1"}) as c:
        cur = url
        for _ in range(10):
            r = c.get(cur)
            chain.append({"url": cur, "status": r.status_code})
            if r.status_code in (301, 302, 303, 307, 308) and "location" in r.headers:
                cur = r.headers["location"]; continue
            break
    return {"chain": chain}
