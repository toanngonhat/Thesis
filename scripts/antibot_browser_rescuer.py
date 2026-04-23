#!/usr/bin/env python3
"""
Anti-Bot Browser Downloader:
Uses real Chrome browser (Playwright) to bypass:
- Cloudflare protection
- User-agent detection  
- JavaScript-based bot detection
- Rate limiting via user-like behavior
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Tuple
import re
import time
from urllib.parse import urlparse
import requests

from playwright.async_api import async_playwright

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
PAPERS_FILE = DATA_DIR / "papers_100.json"
PDF_DIR = DATA_DIR / "papers_pdf"
DOWNLOAD_DIR = PDF_DIR / "temp_downloads"
PDF_DIR.mkdir(parents=True, exist_ok=True)
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_TIMEOUT = 25  # seconds
MAX_PAPERS_PER_RUN = 100
MAX_CANDIDATES_PER_PAPER = 5
MAX_BROWSER_ATTEMPTS_PER_PAPER = 2

SKIP_BROWSER_HOSTS = {
    "doi.org",
    "dl.acm.org",
    "www.science.org",
    "onlinelibrary.wiley.com",
}

BROWSER_ALLOWLIST = {
    "arxiv.org",
    "export.arxiv.org",
    "hal.science",
    "research.chalmers.se",
    "www.usenix.org",
}

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
}


def rank_candidate_url(url: str) -> tuple[int, str]:
    """Lower rank is better (faster/more likely OA first)."""
    u = (url or "").lower()
    host = urlparse(u).netloc
    if "arxiv.org/pdf/" in u:
        return (0, u)
    if u.endswith(".pdf"):
        return (1, u)
    if any(x in host for x in ["hal.science", "zenodo.org", "eprint.iacr.org", "usenix.org"]):
        return (2, u)
    if "doi.org" in host:
        return (5, u)
    return (3, u)


def failed_paper_priority(paper: dict) -> tuple[int, int]:
    """Lower score first: likely-open papers should be processed earlier."""
    oa = (paper.get("openAccessPdf") or "").lower()
    src = (paper.get("url") or "").lower()
    if "arxiv.org/pdf/" in oa or "arxiv.org/pdf/" in src:
        return (0, int(paper.get("index") or 10**9))
    if oa.endswith(".pdf"):
        return (1, int(paper.get("index") or 10**9))
    if any(h in oa or h in src for h in ["hal.science", "usenix.org", "zenodo.org", "eprint.iacr.org"]):
        return (2, int(paper.get("index") or 10**9))
    if "doi.org" in src:
        return (4, int(paper.get("index") or 10**9))
    return (3, int(paper.get("index") or 10**9))


def get_safe_filename(title: str, max_len: int = 100) -> str:
    """Create safe filename from title."""
    name = re.sub(r"[^a-zA-Z0-9._ -]", "", title).replace(" ", "_")[:max_len]
    return name or "paper"


def build_standard_filename(index: int, year: int, title: str) -> str:
    return f"{index:03d}_{year}_{get_safe_filename(title, max_len=120)}.pdf"


def resolve_candidate_urls(paper: dict) -> list[str]:
    urls = []
    oa = (paper.get("openAccessPdf") or "").strip()
    src = (paper.get("url") or "").strip()
    if oa:
        urls.append(oa)
    if src and src not in urls:
        urls.append(src)
    return urls


def normalize_doi(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if "doi.org/" in s:
        return s.split("doi.org/", 1)[1].strip(" /")
    if s.startswith("10."):
        return s
    return ""


def resolve_doi_redirect(url: str) -> str:
    """Resolve DOI URL to final redirect target (best-effort)."""
    try:
        r = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=20,
            allow_redirects=True,
        )
        if r.url and r.url != url:
            return r.url
    except Exception:
        pass
    return ""


def openalex_candidates(paper: dict) -> list[str]:
    """Get OA candidates from OpenAlex by DOI/title (best-effort)."""
    out: list[str] = []
    title = (paper.get("title") or "").strip()
    doi = normalize_doi((paper.get("url") or ""))

    try:
        if doi:
            r = requests.get(
                f"https://api.openalex.org/works/https://doi.org/{doi}",
                headers=REQUEST_HEADERS,
                timeout=25,
            )
            if r.ok:
                w = r.json()
                b = (w.get("best_oa_location") or {})
                p = (w.get("primary_location") or {})
                for u in [b.get("pdf_url"), b.get("landing_page_url"), p.get("pdf_url"), p.get("landing_page_url")]:
                    if u and u not in out:
                        out.append(u)
                for loc in (w.get("locations") or []):
                    for u in [loc.get("pdf_url"), loc.get("landing_page_url")]:
                        if u and u not in out:
                            out.append(u)
                return out
    except Exception:
        pass

    if not title:
        return out

    try:
        r = requests.get(
            "https://api.openalex.org/works",
            params={"search": title, "per-page": 5},
            headers=REQUEST_HEADERS,
            timeout=25,
        )
        if not r.ok:
            return out
        for w in (r.json().get("results") or []):
            b = (w.get("best_oa_location") or {})
            p = (w.get("primary_location") or {})
            for u in [b.get("pdf_url"), b.get("landing_page_url"), p.get("pdf_url"), p.get("landing_page_url")]:
                if u and u not in out:
                    out.append(u)
            for loc in (w.get("locations") or []):
                for u in [loc.get("pdf_url"), loc.get("landing_page_url")]:
                    if u and u not in out:
                        out.append(u)
            if out:
                break
    except Exception:
        pass
    return out


def validate_pdf(file_path: Path) -> bool:
    """Check if file is a valid PDF."""
    if not file_path.exists():
        return False
    try:
        size = file_path.stat().st_size
        if size < 2048:
            return False
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except:
        return False


def download_via_curl(url: str, output_path: Path) -> Tuple[bool, str]:
    """Try a direct curl download for obvious PDF URLs."""
    cmd = [
        "curl",
        "-sS",
        "-L",
        "--max-time",
        str(DOWNLOAD_TIMEOUT),
        "-A",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "-o",
        str(output_path),
        url,
    ]
    subprocess.run(cmd, capture_output=True, text=True)

    if validate_pdf(output_path):
        size_kb = output_path.stat().st_size / 1024
        return True, f"Direct curl: {size_kb:.1f}KB"

    if output_path.exists():
        output_path.unlink()
    return False, "Direct curl failed"


async def download_with_browser(url: str, output_path: Path, paper_id: int) -> Tuple[bool, str]:
    """
    Download PDF using real Chrome browser via Playwright.
    Bypasses Cloudflare + sends real browser requests.
    """
    try:
        print(f"    🌐 Starting browser...", file=sys.stderr)
        
        async with async_playwright() as p:
            # Launch Chrome with stealth settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
            )
            
            page = await context.new_page()
            
            # Setup download handler
            async def on_download(download):
                # Save downloaded file
                await download.save_as(str(output_path))
                print(f"    💾 Download captured via browser", file=sys.stderr)
            
            page.on("download", on_download)
            
            last_pdf_url = None
            referer_url = url

            def on_response(resp):
                nonlocal last_pdf_url
                ctype = (resp.headers.get("content-type") or "").lower()
                if "application/pdf" in ctype or ".pdf" in resp.url.lower():
                    last_pdf_url = resp.url

            page.on("response", on_response)

            try:
                print(f"    📄 Loading {url[:60]}...", file=sys.stderr)
                
                # Navigate with longer timeout and wait for network idle
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=DOWNLOAD_TIMEOUT * 1000,
                )
                
                print(f"    ✓ Page loaded", file=sys.stderr)
                referer_url = page.url
                
                # Wait a bit for scripts to run
                await asyncio.sleep(2)
                
                # Check if page has PDF viewer or download links
                # Method 1: Check if current page returned PDF
                content_type = await page.evaluate(
                    """
                    () => {
                        const items = performance.getEntriesByType('resource');
                        const pdfReq = items.find(r => r.name.includes('.pdf'));
                        return pdfReq ? 'pdf' : 'html';
                    }
                    """
                )
                
                if content_type == "pdf":
                    print(f"    ✓ Page is PDF (via resource check)", file=sys.stderr)
                    # Try to save page as PDF
                    try:
                        await page.pdf(path=str(output_path))
                        print(f"    💾 Saved as PDF via page.pdf()", file=sys.stderr)
                        await asyncio.sleep(1)
                    except:
                        pass
                
                # Method 2: Look for PDF download link/button
                print(f"    🔍 Looking for download links...", file=sys.stderr)
                pdf_links = await page.evaluate(
                    """
                    () => {
                        const links = [];
                        document.querySelectorAll('a[href*=".pdf"], button[onclick*="pdf"], a[href*="/pdf"]').forEach(a => {
                            let href = a.href || a.getAttribute('data-url') || a.getAttribute('ontap');
                            if (href) links.push(href);
                        });
                        return links;
                    }
                    """
                )
                
                if pdf_links:
                    print(f"    ✓ Found {len(pdf_links)} PDF links", file=sys.stderr)
                    for link in pdf_links[:1]:  # Try first link
                        print(f"      Clicking: {link[:50]}...", file=sys.stderr)
                        try:
                            await page.goto(link, wait_until="networkidle", timeout=DOWNLOAD_TIMEOUT * 1000)
                            await asyncio.sleep(1)
                        except:
                            pass
                
                # Method 3: Save page as PDF (for HTML pages that should be PDF)
                await asyncio.sleep(1)
                
                # Check if file was downloaded from browser
                if output_path.exists():
                    if validate_pdf(output_path):
                        size_kb = output_path.stat().st_size / 1024
                        await context.close()
                        await browser.close()
                        return True, f"Browser download: {size_kb:.1f}KB"
                    else:
                        output_path.unlink()
                
                # Fallback: use curl with browser's cookies and detected PDF URL
                print(f"    📥 Fallback: curl with browser context...", file=sys.stderr)
                cookie_header = ""
                cookies = await context.cookies()
                if cookies:
                    cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

                target_url = last_pdf_url or url
                cmd = [
                    "curl",
                    "-sS",
                    "-L",
                    "--max-time",
                    str(DOWNLOAD_TIMEOUT),
                    "-A",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "-H",
                    f"Referer: {referer_url}",
                    "-o",
                    str(output_path),
                ]
                if cookie_header:
                    cmd.extend(["-H", f"Cookie: {cookie_header}"])
                cmd.append(target_url)
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                await context.close()
                await browser.close()
                
                if validate_pdf(output_path):
                    size_kb = output_path.stat().st_size / 1024
                    return True, f"Fallback curl: {size_kb:.1f}KB"
                
                return False, "Could not retrieve valid PDF"
            except Exception as e:
                try:
                    await context.close()
                    await browser.close()
                except Exception:
                    pass
                return False, f"Browser flow error: {str(e)[:30]}"
    
    except asyncio.TimeoutError:
        return False, "Browser timeout"
    except Exception as e:
        return False, str(e)[:40]


async def rescue_paper_via_browser(paper: dict, index: int) -> Tuple[bool, str, str]:
    """Rescue single paper using browser automation."""
    title = paper.get("title", f"Paper_{index}")
    year = int(paper.get("year") or 0)
    filename = build_standard_filename(index, year, title)
    output_path = PDF_DIR / filename
    
    # Skip if already exists
    if validate_pdf(output_path):
        return True, "Already exists", filename
    
    candidate_urls = resolve_candidate_urls(paper)

    # Augment candidates from DOI redirects and OpenAlex OA metadata.
    augmented: list[str] = []
    for u in candidate_urls:
        if u and u not in augmented:
            augmented.append(u)
        if "doi.org/" in (u or ""):
            ru = resolve_doi_redirect(u)
            if ru and ru not in augmented:
                augmented.append(ru)
    for u in openalex_candidates(paper):
        if u and u not in augmented:
            augmented.append(u)
    candidate_urls = sorted(augmented, key=rank_candidate_url)[:MAX_CANDIDATES_PER_PAPER]

    if not candidate_urls:
        return False, "No URL provided", ""

    print(f"\n📄 Paper {index}: {title[:55]}", file=sys.stderr)
    print(f"   Candidate URLs: {len(candidate_urls)}", file=sys.stderr)

    browser_attempts = 0
    for url in candidate_urls:
        host = urlparse(url).netloc
        print(f"   Trying host: {host}", file=sys.stderr)

        # Direct curl first is cheap and often succeeds for OA endpoints.
        lowered = url.lower()
        ok, msg = download_via_curl(url, output_path)
        if ok:
            print(f"   ✅ {msg}", file=sys.stderr)
            return True, msg, filename

        # Skip expensive browser path for known resolver/paywall hosts.
        if host in SKIP_BROWSER_HOSTS:
            continue

        # Only open browser for a small allowlist of hosts where JS flow may help.
        if host not in BROWSER_ALLOWLIST:
            continue

        if browser_attempts >= MAX_BROWSER_ATTEMPTS_PER_PAPER:
            continue

        success, msg = await download_with_browser(url, output_path, index)
        browser_attempts += 1
        if success:
            print(f"   ✅ {msg}", file=sys.stderr)
            return True, msg, filename
    
    print(f"   ❌ Could not retrieve valid PDF", file=sys.stderr)
    return False, "Could not retrieve valid PDF", ""


async def main():
    """Process failed papers using browser automation."""
    with open(PAPERS_FILE) as f:
        papers = json.load(f)
    
    failed_papers = [
        p for p in papers
        if p.get("pdf_download_status", "").startswith("failed")
    ]
    failed_papers.sort(key=failed_paper_priority)
    
    if not failed_papers:
        print("✅ No failed papers", file=sys.stderr)
        return
    
    print(f"\n{'='*70}", file=sys.stderr)
    print(f"🌐 ANTI-BOT BROWSER RESCUE (Playwright + Chrome)", file=sys.stderr)
    print(f"{'='*70}", file=sys.stderr)
    print(f"Scanning {len(failed_papers)} failed papers", file=sys.stderr)
    print(f"Limit: {MAX_PAPERS_PER_RUN} papers per run (browser is slower)\n", file=sys.stderr)
    
    recovered = 0
    processed = 0
    
    # Process first N failed papers
    for paper in failed_papers[:MAX_PAPERS_PER_RUN]:
        idx = paper["index"]
        success, msg, filename = await rescue_paper_via_browser(paper, idx)
        processed += 1
        
        if success:
            recovered += 1
            paper["pdf_download_status"] = "downloaded"
            paper["pdf_file"] = f"data/papers_pdf/{filename}"

        # Persist progress after each paper to avoid losing recoveries on interruption.
        with open(PAPERS_FILE, "w") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        
        # Rate limiting between papers
        if processed < min(MAX_PAPERS_PER_RUN, len(failed_papers)):
            print(f"\n   ⏰ Waiting 3s before next paper...", file=sys.stderr)
            await asyncio.sleep(3)
    
    # Summary
    total_downloaded = sum(1 for p in papers if p.get("pdf_download_status") == "downloaded")
    total_failed = sum(1 for p in papers if p.get("pdf_download_status", "").startswith("failed"))
    
    print(f"\n{'='*70}", file=sys.stderr)
    print(f"📊 ANTI-BOT BROWSER RESCUE SUMMARY:", file=sys.stderr)
    print(f"{'='*70}", file=sys.stderr)
    print(f"   ✅ This batch: +{recovered}/{processed} recovered", file=sys.stderr)
    print(f"   ✅ Total downloaded: {total_downloaded}/100", file=sys.stderr)
    print(f"   ❌ Still failed: {total_failed}/100", file=sys.stderr)
    print(f"   📈 Progress: {total_downloaded}%", file=sys.stderr)
    print(f"{'='*70}\n", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
