import time
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

import requests
from bs4 import BeautifulSoup

import config
from utils.helpers import clean_text

_BASE = "https://career.hkust.edu.hk/web/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en,zh;q=0.9",
}


def _build_session() -> requests.Session:
    session = requests.Session()
    session.cookies.set("PHPSESSID", config.SESSION_COOKIE)
    return session


def _build_url(filters: dict, page_num: int) -> str:
    """Build a filter-aware paginated URL.

    filters keys match the form param names: 'keywords', 'BN[]', 'JN[]',
    'EMT[]', 'WL[]', 'awards[]', 'EM[]', 'L[]', 'TEC', 'AJOB', 'NCHI'.
    Multi-select values should be lists of strings.
    """
    params: list[tuple[str, str]] = []
    params.append(("keywords", filters.get("keywords", "")))

    for key in ("BN[]", "JN[]", "EMT[]", "WL[]", "awards[]", "EM[]", "L[]"):
        for val in filters.get(key, []):
            params.append((key, val))

    for flag in ("TEC", "AJOB", "NCHI"):
        if filters.get(flag):
            params.append((flag, "1"))

    if page_num > 1:
        params.append(("page", str(page_num)))

    return f"{config.HKUST_JOB_BOARD_URL}?{urlencode(params)}"


def _safe_get(session: requests.Session, url: str):
    for attempt in range(3):
        try:
            r = session.get(url, headers=_HEADERS, timeout=config.REQUEST_TIMEOUT)
            if r.status_code == 200:
                return r
            print(f"  Warning: HTTP {r.status_code} for {url}")
        except requests.RequestException as e:
            print(f"  Request failed (attempt {attempt + 1}): {e}")
            time.sleep(1.5)
    print(f"  ERROR: failed to fetch {url} after 3 attempts")
    return None


def _parse_list_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr.job-item")
    out = []

    for row in rows:
        large_view_tds = row.select("td.detail-text.large-view")
        if not large_view_tds:
            continue

        first_td = large_view_tds[0]
        job_post_link = first_td.select_one("a.job-post")
        if not job_post_link:
            continue

        detail_url = urljoin(_BASE, job_post_link.get("href", ""))

        company = ""
        company_font2 = first_td.select("table tr td font.font2")
        if company_font2:
            company = clean_text(company_font2[0].get_text(" ", strip=True))

        title = ""
        job_nature = ""
        if len(large_view_tds) >= 2:
            title_td = large_view_tds[1]
            title_link = title_td.select_one("a.job-post")
            if title_link:
                fonts = title_link.select("font.font2")
                if len(fonts) >= 1:
                    title = clean_text(fonts[0].get_text(" ", strip=True))
                if len(fonts) >= 2:
                    job_nature = clean_text(fonts[1].get_text(" ", strip=True))

        posting_date = ""
        deadline = ""
        if len(large_view_tds) >= 4:
            posting_date = clean_text(large_view_tds[2].get_text(" ", strip=True))
            deadline = clean_text(large_view_tds[3].get_text(" ", strip=True))

        job_id = ""
        if detail_url:
            q = parse_qs(urlparse(detail_url).query)
            job_id = (q.get("jp") or [""])[0]

        out.append({
            "company": company,
            "job_title": title,
            "job_nature": job_nature,
            "posting_date": posting_date,
            "deadline": deadline,
            "detail_url": detail_url,
            "job_id": job_id,
        })
    return out


def _parse_detail_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    scope = soup.select_one(".content-container .career-content") or soup

    parts = []
    for selector in [
        ".career-content .detail-text",
        "table.second-detail tbody tr td",
        ".content-container p",
    ]:
        for el in scope.select(selector):
            text = clean_text(el.get_text(" ", strip=True))
            if text:
                parts.append(text)

    details = " ".join(parts) if parts else clean_text(scope.get_text(" ", strip=True))

    email = ""
    website = ""
    for link in soup.select("a.red_link"):
        href = link.get("href", "")
        if href.startswith("mailto:") and not email:
            email = href.split(":", 1)[-1].split("?", 1)[0].strip()
        elif href.startswith("https://") and not website:
            website = href.strip()

    return {"details": details, "email": email, "website": website}


def scrape_jobs(filters: dict, pages: list[int], progress_cb=None) -> list[dict]:
    """Scrape the given page numbers with active filters, return job dicts.

    progress_cb: optional callable(event: dict) called from the scraping thread.
    """
    session = _build_session()
    all_jobs = []
    seen_urls: set[str] = set()

    for page_index, page_num in enumerate(pages, 1):
        url = _build_url(filters, page_num)
        print(f"  [{page_index}/{len(pages)}] page {page_num}...")
        if progress_cb:
            progress_cb({
                "type": "progress",
                "page": page_num,
                "page_index": page_index,
                "total_pages": len(pages),
                "message": f"Scraping page {page_num}/{len(pages)}...",
            })

        r = _safe_get(session, url)
        if not r:
            print(f"    Skipping page {page_num} (fetch failed).")
            if progress_cb:
                progress_cb({"type": "warning", "message": f"Page {page_num} failed, skipping."})
            continue

        items = _parse_list_page(r.text)
        if not items:
            print(f"    No listings found — possibly past the last page.")
            if progress_cb:
                progress_cb({"type": "info", "message": "No more listings — stopping early."})
            break

        for item in items:
            detail_url = item.get("detail_url", "")
            if not detail_url or detail_url in seen_urls:
                continue
            seen_urls.add(detail_url)

            time.sleep(config.SLEEP_BETWEEN_REQUESTS)
            dr = _safe_get(session, detail_url)
            if not dr:
                continue

            detail = _parse_detail_page(dr.text)
            all_jobs.append({**item, **detail})
            if progress_cb:
                progress_cb({
                    "type": "job_found",
                    "count": len(all_jobs),
                    "company": item.get("company", ""),
                    "job_title": item.get("job_title", ""),
                })

    return all_jobs
