1
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs
import os
import requests
from bs4 import BeautifulSoup
import pandas as pd

SESSION_COOKIES = {"PHPSESSID": "e15c19f39862f5ff8423ca1196c683e79ecf9e41869c0f89c20e5602b62b3159"}

BASE_LIST_URL = "https://career.hkust.edu.hk/web/job.php"
BASE = "https://career.hkust.edu.hk/web/"

def get_page_number():
    """Get page number(s) from user input - supports single page (e.g., 3) or range (e.g., 1-50)"""
    while True:
        try:
            page_input = input("Enter page number(s) to scrape - Single (e.g., 3) or Range (e.g., 1-50): ").strip()
            
            if '-' in page_input:
                # Handle range input
                start_str, end_str = page_input.split('-', 1)
                start_page = int(start_str.strip())
                end_page = int(end_str.strip())
                
                if start_page < 1:
                    print("Start page must be at least 1.")
                elif start_page > end_page:
                    print("Start page must be <= end page")
                elif end_page - start_page > 100:
                    print("⚠️  Warning: Large range detected. This will take a long time.")
                    confirm = input(f"Scrape {end_page - start_page + 1} pages ({start_page}-{end_page})? (y/n): ").strip().lower()
                    if confirm != 'y':
                        print("Operation cancelled.")
                        continue
                    pages = list(range(start_page, end_page + 1))
                    print(f"✅ Will scrape {len(pages)} pages: {start_page} to {end_page}")
                    return pages
                else:
                    pages = list(range(start_page, end_page + 1))
                    print(f"✅ Will scrape {len(pages)} pages: {pages}")
                    return pages
            else:
                # Handle single page input
                page_num = int(page_input)
                if page_num >= 1:
                    print(f"✅ Will scrape page: {page_num}")
                    return [page_num]  # Return as list for consistency
                else:
                    print("Page number must be at least 1.")
        except ValueError:
            print("Invalid format. Use single number (3) or range (1-5)")

def build_url(page_num):
    """Build the URL for the specified page"""
    if page_num == 1:
        return BASE_LIST_URL
    else:
        return f"{BASE_LIST_URL}?page={page_num}&"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en,zh;q=0.9",
}

REQUEST_TIMEOUT = 25
SLEEP_BETWEEN_REQUESTS = 1.0  


def clean_text(s: str) -> str:
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).replace("\xa0", " ").strip()


def load_existing_jobs(filename="hkust_job.csv"):
    """Load existing jobs from CSV file and return a set of (company, job_title) tuples for fast lookup."""
    if not os.path.exists(filename):
        return set(), pd.DataFrame()
    
    try:
        df = pd.read_csv(filename, encoding="utf-8-sig")
        # Create a set of (company, job_title) tuples for O(1) lookup
        existing_jobs = set()
        for _, row in df.iterrows():
            key = (str(row.get('company', '')).strip(), str(row.get('job_title', '')).strip())
            existing_jobs.add(key)
        return existing_jobs, df
    except Exception as e:
        print(f"Warning: Could not load existing CSV file: {e}")
        return set(), pd.DataFrame()


def is_duplicate(company, job_title, existing_jobs):
    """Check if a job is already in the existing jobs set."""
    key = (str(company).strip(), str(job_title).strip())
    return key in existing_jobs


def safe_get(session: requests.Session, url: str):
    for attempt in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            
            if r.status_code == 200:
                return r
            else:
                print(f"  Warning: Got status code {r.status_code} for {url}")
                
        except requests.RequestException as e:
            print(f"  Request failed (attempt {attempt + 1}): {e}")
            time.sleep(1.5)
    
    print(f"  ERROR: Failed to fetch {url} after 3 attempts")
    return None


def parse_list_page(html: str):
    soup = BeautifulSoup(html, "lxml")
    rows = soup.select("tr.job-item")
    out = []

    for row in rows:
        large_view_tds = row.select("td.detail-text.large-view")
        if not large_view_tds:
            continue
            
        first_large_view = large_view_tds[0]
        job_post_link = first_large_view.select_one("a.job-post")
        if not job_post_link:
            continue
            
        detail_url = urljoin(BASE, job_post_link.get("href")) if job_post_link.has_attr("href") else ""

        company = ""
        company_font2 = first_large_view.select("table tr td font.font2")
        if company_font2:
            # The first font2 element contains the company name
            company = clean_text(company_font2[0].get_text(" ", strip=True))
        
        title = ""
        job_nature = ""
        
        # Look for the second large-view td which contains job title and job nature
        if len(large_view_tds) >= 2:
            # The second large-view td contains job title and job nature
            job_title_td = large_view_tds[1]
            job_title_link = job_title_td.select_one("a.job-post")
            if job_title_link:
                font2_elements = job_title_link.select("font.font2")
                if len(font2_elements) >= 1:
                    title = clean_text(font2_elements[0].get_text(" ", strip=True))
                if len(font2_elements) >= 2:
                    job_nature = clean_text(font2_elements[1].get_text(" ", strip=True))
        
        # Extract posting date and deadline from the large-view columns
        posting_date = ""
        deadline = ""
        if len(large_view_tds) >= 4:
            posting_date = clean_text(large_view_tds[2].get_text(" ", strip=True))
            deadline = clean_text(large_view_tds[3].get_text(" ", strip=True))

        # 尝试解析 job id
        jp = ""
        if detail_url:
            q = parse_qs(urlparse(detail_url).query)
            jp = (q.get("jp") or [""])[0]

        out.append(
            {
                "company": company,
                "job_title": title,
                "job_nature": job_nature,
                "posting_date": posting_date,
                "application_deadline": deadline,
                "detail_url": detail_url,
                "job_id": jp,
            }
        )
    return out


def parse_detail_page(html: str):

    soup = BeautifulSoup(html, "lxml")

    scope = soup.select_one(".content-container .career-content") or soup
    
    job_description = ""
    
    description_selectors = [
        ".career-content .detail-text",  # Main job description area
        "table.second-detail tbody tr td",  # Structured job details
        ".content-container p",  # Paragraph content
        ".job-description",  # If there's a specific job description class
    ]
    
    all_text_parts = []
    
    for selector in description_selectors:
        elements = scope.select(selector)
        for elem in elements:
            text = clean_text(elem.get_text(" ", strip=True))
            if text: 
                all_text_parts.append(text)
    
    if all_text_parts:
        combined_text = " ".join(all_text_parts)
    else:
        combined_text = clean_text(scope.get_text(" ", strip=True))
    
    job_description = combined_text

    email = ""
    website = ""
    
    red_links = soup.select('a.red_link')
    
    for link in red_links:
        if not link.has_attr("href"):
            continue
            
        href = link["href"]
        
        if href.startswith("mailto:"):
            if not email:  
                email = href.split(":", 1)[-1].split("?", 1)[0].strip()
        
        elif href.startswith("https://"):
            if not website:  
                website = href.strip()

    return {
        "detail_text_all": job_description,
        "apply_email": email,
        "website": website,
    }


def scrape():
    pages_to_scrape = get_page_number()
    
    session = requests.Session()
    session.cookies.update(SESSION_COOKIES)
    
    # Load existing jobs for duplicate checking
    existing_jobs, existing_df = load_existing_jobs()
    initial_row_count = len(existing_df)
    
    print(f"Loaded {len(existing_jobs)} existing jobs for duplicate checking")
    print(f"Starting to scrape {len(pages_to_scrape)} page(s)...")
    
    all_new_rows = []
    total_duplicates_skipped = 0
    
    for page_index, page_num in enumerate(pages_to_scrape, 1):
        list_url = build_url(page_num)
        print(f"\n[{page_index}/{len(pages_to_scrape)}] Scraping page {page_num}: {list_url}")

        print(f"Fetching page {page_num}...")
        r = safe_get(session, list_url)
        if not r:
            print(f"Failed to fetch page {page_num}. Continuing with next page...")
            continue

        list_items = parse_list_page(r.text)
        print(f"Found {len(list_items)} rows on page {page_num}.")
        
        if len(list_items) == 0:
            print(f"WARNING: No job items found on page {page_num}!")
            continue

        seen = set()
        page_new_rows = []
        page_duplicates_skipped = 0
        print(f"Processing {len(list_items)} jobs from page {page_num}...")
        
        for i, item in enumerate(list_items, 1):
            url = item.get("detail_url")
            if not url or url in seen:
                continue
            seen.add(url)

            company = item.get("company", "")
            job_title = item.get("job_title", "")
            
            if is_duplicate(company, job_title, existing_jobs):
                print(f"  [{i}/{len(list_items)}] DUPLICATE: {job_title} at {company} - skipped")
                page_duplicates_skipped += 1
                continue

            time.sleep(SLEEP_BETWEEN_REQUESTS)
            print(f"  [{i}/{len(list_items)}] Fetching detail: {url}")
            dr = safe_get(session, url)
            if not dr:
                print("    -> failed, skip.")
                continue

            detail = parse_detail_page(dr.text)

            row = {
                **item,
                **detail,
            }
            page_new_rows.append(row)
            
            existing_jobs.add((company, job_title))
            
            print(f"    -> NEW: {job_title} at {company}")
        
        all_new_rows.extend(page_new_rows)
        total_duplicates_skipped += page_duplicates_skipped
        
        print(f"Page {page_num} complete: {len(page_new_rows)} new jobs added, {page_duplicates_skipped} duplicates skipped")

    # Combine existing data with new rows from all pages
    if all_new_rows:
        new_df = pd.DataFrame(all_new_rows)
        
        # Rename columns for new data
        new_df_renamed = new_df.rename(columns={
            'apply_email': 'email',
            'detail_text_all': 'details',
            'application_deadline': 'deadline'
        })
        
        # Add default FALSE values for applied and letter columns
        new_df_renamed['applied'] = False
        new_df_renamed['letter'] = False
        
        # Set "NO EMAIL" for rows with no email address
        no_email_mask = (new_df_renamed['email'].isna() | 
                        (new_df_renamed['email'] == '') | 
                        (new_df_renamed['email'].astype(str).str.strip() == ''))
        new_df_renamed.loc[no_email_mask, 'applied'] = 'NO EMAIL'
        
        new_df_final = new_df_renamed[['company', 'job_title', 'job_nature', 'email', 'website',
                                      'details', 'deadline', 'posting_date', 
                                      'applied', 'letter']].copy()
    
        if not existing_df.empty:
            # Ensure existing dataframe has the applied and letter columns
            if 'applied' not in existing_df.columns:
                existing_df['applied'] = False
            if 'letter' not in existing_df.columns:
                existing_df['letter'] = False
            
            final_df = pd.concat([existing_df, new_df_final], ignore_index=True)
        else:
            final_df = new_df_final
    else:
        final_df = existing_df
        # Ensure final dataframe has the applied and letter columns even if no new rows
        if not final_df.empty:
            if 'applied' not in final_df.columns:
                final_df['applied'] = False
            if 'letter' not in final_df.columns:
                final_df['letter'] = False
    
    final_df.to_csv("hkust_job.csv", index=False, encoding="utf-8-sig")
    
    # Generate summary output
    total_pages_scraped = len(pages_to_scrape)
    new_jobs_added = len(all_new_rows)
    final_row_count = len(final_df)
    
    print(f"\n📊 SCRAPING COMPLETE:")
    print(f"   • Pages scraped: {pages_to_scrape}")
    print(f"   • Total duplicates skipped: {total_duplicates_skipped}")
    print(f"   • New jobs added: {new_jobs_added}")
    if new_jobs_added > 0:
        start_row = initial_row_count + 2  # +2 for header and 1-based indexing
        end_row = final_row_count + 1      # +1 for header
        print(f"   • Appended to rows: {start_row}-{end_row}")
    print(f"   • Total jobs in CSV: {final_row_count}")
    
    return final_df


if __name__ == "__main__":
    scrape()
