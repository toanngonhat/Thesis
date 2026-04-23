#!/usr/bin/env python3
"""Collect 100 papers related to refactoring-stable proof repair.

Data source: OpenAlex Works API.
Output:
- data/papers_100.json
- data/papers_100_summary.csv
- data/papers_100_summary.md
- data/papers_pdf/ (open-access PDFs when available)
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

API_URL = "https://api.openalex.org/works"

QUERIES = [
    "proof repair verification",
    "program verification refactoring",
    "proof maintenance software evolution",
    "solver brittleness verification conditions",
    "incremental verification",
    "regression verification",
    "proof script adaptation",
    "SMT trigger quantifier",
    "invariant inference verification",
    "formal methods maintenance",
    "formal verification software engineering",
    "proof engineering coq",
    "lean theorem proving software",
    "verification condition generation",
    "contract-based verification",
    "software security verification",
    "symbolic execution security",
    "program analysis security and privacy",
    "machine learning security",
    "ai for software engineering",
]

KEYWORDS = [
    "proof",
    "repair",
    "verification",
    "refactor",
    "refactoring",
    "invariant",
    "lemma",
    "solver",
    "smt",
    "regression",
    "maintenance",
    "evolution",
    "coq",
    "lean",
    "dafny",
    "verus",
    "viper",
    "specification",
]

TOP_VENUE_PATTERNS = {
    "SE": [
        "icse",
        "international conference on software engineering",
        "fse",
        "foundations of software engineering",
        "esec",
        "joint meeting on foundations of software engineering",
        "ase",
        "automated software engineering",
        "issta",
        "international symposium on software testing and analysis",
        "tse",
        "ieee transactions on software engineering",
        "tosem",
        "acm transactions on software engineering and methodology",
        "emse",
        "empirical software engineering",
    ],
    "PL": [
        "pldi",
        "programming language design and implementation",
        "popl",
        "principles of programming languages",
        "oopsla",
        "object-oriented programming systems languages and applications",
        "icfp",
        "international conference on functional programming",
        "ecoop",
        "european conference on object-oriented programming",
        "cav",
        "computer aided verification",
        "vmcai",
        "verification model checking and abstract interpretation",
        "proceedings of the acm on programming languages",
        "lmcs",
        "logical methods in computer science",
        "jfp",
        "journal of functional programming",
        "toplas",
        "acm transactions on programming languages and systems",
    ],
    "AI": [
        "neurips",
        "nips",
        "neural information processing systems",
        "icml",
        "international conference on machine learning",
        "iclr",
        "international conference on learning representations",
        "aaai",
        "aaai conference on artificial intelligence",
        "ijcai",
        "international joint conference on artificial intelligence",
        "journal of machine learning research",
        "jmlr",
        "artificial intelligence",
        "ieee transactions on pattern analysis and machine intelligence",
        "tpami",
    ],
    "Security": [
        "usenix security",
        "usenix security symposium",
        "ieee symposium on security and privacy",
        "oakland",
        "acm conference on computer and communications security",
        "ccs",
        "network and distributed system security symposium",
        "ndss",
        "computer security foundations symposium",
        "csf",
        "ieee transactions on dependable and secure computing",
        "tdsc",
        "transactions on privacy and security",
        "tops",
        "acm transactions on privacy and security",
    ],
}

TARGET_COUNT = 100
MIN_PER_DOMAIN = 10
PER_PAGE = 50
PAGES_PER_QUERY = 6
REQUEST_DELAY_SEC = 0.45
PDF_TIMEOUT_SEC = 15
DOWNLOAD_PDFS = True


def fetch_json(url: str) -> Dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "thesis-paper-collector/1.0 (mailto:student@example.com)",
            "Accept": "application/json",
        },
    )
    retries = 3
    delay = 0.9
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(delay)
                delay *= 1.8
                continue
            raise
        except Exception as e:
            last_err = e
            time.sleep(delay)
            delay *= 1.5

    if last_err:
        raise last_err
    raise RuntimeError("Failed to fetch JSON")


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def venue_key(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", normalize_text(s).lower())


def infer_domain_from_venue(venue: str) -> str:
    vk = venue_key(venue)
    for domain, patterns in TOP_VENUE_PATTERNS.items():
        for p in patterns:
            if f" {p} " in f" {vk} " or p in vk:
                return domain
    return "Other"


def is_top_venue(venue: str) -> bool:
    return infer_domain_from_venue(venue) != "Other"


def decode_abstract(inv_idx: Dict) -> str:
    if not isinstance(inv_idx, dict) or not inv_idx:
        return ""
    max_pos = -1
    for positions in inv_idx.values():
        if positions:
            max_pos = max(max_pos, max(positions))
    if max_pos < 0:
        return ""
    words = [""] * (max_pos + 1)
    for word, positions in inv_idx.items():
        for p in positions:
            if 0 <= p < len(words):
                words[p] = word
    return normalize_text(" ".join(w for w in words if w))


def relevance_score(paper: Dict) -> float:
    title = normalize_text(paper.get("title", "")).lower()
    abstract = normalize_text(paper.get("abstract", "")).lower()
    text = f"{title} {abstract}"

    kw_hits = sum(1 for kw in KEYWORDS if kw in text)
    title_hits = sum(1 for kw in KEYWORDS if kw in title)

    citations = int(paper.get("citations") or 0)
    year = int(paper.get("year") or 0)
    recency = max(0, year - 2014) * 0.12

    venue_bonus = 3.0 if is_top_venue(paper.get("venue", "")) else 0.0
    return kw_hits * 1.6 + title_hits * 1.9 + min(citations, 3000) * 0.0015 + recency + venue_bonus


def infer_summary(abstract: str) -> str:
    text = normalize_text(abstract)
    if not text:
        return "No abstract available from metadata."
    parts = re.split(r"(?<=[.!?])\s+", text)
    summary = " ".join(parts[:2]).strip()
    if len(summary) > 360:
        summary = summary[:357].rstrip() + "..."
    return summary


def infer_strengths(paper: Dict) -> str:
    strengths: List[str] = []
    text = f"{paper.get('title','')} {paper.get('abstract','')}".lower()
    citations = int(paper.get("citations") or 0)

    if citations >= 200:
        strengths.append("High citation impact")
    elif citations >= 50:
        strengths.append("Moderate community uptake")

    if any(k in text for k in ["evaluation", "benchmark", "empirical"]):
        strengths.append("Includes empirical evaluation")
    if any(k in text for k in ["sound", "correct", "proof"]):
        strengths.append("Strong formal reasoning focus")
    if any(k in text for k in ["tool", "prototype", "implementation"]):
        strengths.append("Contains implemented tooling")

    if not strengths:
        strengths.append("Directly relevant conceptual contribution")

    return "; ".join(strengths[:3])


def infer_weaknesses(paper: Dict) -> str:
    weaknesses: List[str] = []
    abstract = normalize_text(paper.get("abstract", "")).lower()
    year = int(paper.get("year") or 0)
    citations = int(paper.get("citations") or 0)

    if not abstract:
        weaknesses.append("Limited metadata (missing abstract)")
    if not any(k in abstract for k in ["evaluation", "benchmark", "case study"]):
        weaknesses.append("Evaluation scope unclear from abstract")
    if not any(k in abstract for k in ["artifact", "open source", "repository"]):
        weaknesses.append("Artifact availability not explicit")
    if citations < 10 and year <= 2022:
        weaknesses.append("Lower observed research uptake")
    if year and year < 2015:
        weaknesses.append("May not reflect latest verifier/toolchain behavior")

    if not weaknesses:
        weaknesses.append("Potential domain/tool specificity")

    return "; ".join(weaknesses[:3])


def safe_filename(name: str, max_len: int = 140) -> str:
    base = re.sub(r"[^a-zA-Z0-9._ -]", "", name).strip().replace(" ", "_")
    base = re.sub(r"_+", "_", base)
    if not base:
        base = "paper"
    return base[:max_len]


def try_download_pdf(url: str, target_path: Path) -> Tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "thesis-paper-collector/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=PDF_TIMEOUT_SEC) as resp:
            content_type = resp.headers.get("Content-Type", "")
            data = resp.read()
        if b"%PDF" not in data[:1024] and "pdf" not in content_type.lower():
            return False, "URL did not return PDF content"
        target_path.write_bytes(data)
        return True, "downloaded"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


def fetch_openalex_query(query: str) -> List[Dict]:
    rows: List[Dict] = []
    for page in range(1, PAGES_PER_QUERY + 1):
        params = {
            "search": query,
            "per-page": str(PER_PAGE),
            "page": str(page),
            "filter": "from_publication_date:2000-01-01,type:!book,type:!dataset",
            "sort": "cited_by_count:desc",
        }
        url = f"{API_URL}?{urllib.parse.urlencode(params)}"
        try:
            payload = fetch_json(url)
            rows.extend(payload.get("results", []))
        except Exception as e:
            print(f"warn: query='{query}' page={page} failed: {e}")
            break
        time.sleep(REQUEST_DELAY_SEC)
    return rows


def map_openalex_work(work: Dict) -> Dict:
    title = normalize_text(work.get("display_name", ""))
    year = work.get("publication_year")
    citations = int(work.get("cited_by_count") or 0)

    abstract = decode_abstract(work.get("abstract_inverted_index") or {})

    authorships = work.get("authorships") or []
    author_names = []
    for a in authorships[:6]:
        author = a.get("author") or {}
        name = normalize_text(author.get("display_name", ""))
        if name:
            author_names.append(name)
    authors = ", ".join(author_names)
    if len(authorships) > 6:
        authors += ", et al."

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    venue = normalize_text(source.get("display_name", ""))

    doi = normalize_text(work.get("doi", ""))
    url = doi if doi else normalize_text(work.get("id", ""))

    best_oa = work.get("best_oa_location") or {}
    pdf_url = normalize_text(best_oa.get("pdf_url", ""))
    landing_url = normalize_text(best_oa.get("landing_page_url", ""))
    if not url and landing_url:
        url = landing_url

    paper_id = normalize_text(work.get("id", ""))

    return {
        "paperId": paper_id,
        "title": title,
        "authors": authors,
        "year": year or "",
        "venue": venue,
        "citations": citations,
        "url": url,
        "openAccessPdf": pdf_url,
        "abstract": abstract,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    pdf_dir = data_dir / "papers_pdf"
    data_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    collected: Dict[str, Dict] = {}

    for q in QUERIES:
        items = fetch_openalex_query(q)
        for work in items:
            mapped = map_openalex_work(work)
            pid = mapped["paperId"]
            if pid and pid not in collected and mapped["title"]:
                collected[pid] = mapped
        print(f"query='{q}' -> {len(items)} raw works, unique total={len(collected)}")

    top_only = [p for p in collected.values() if is_top_venue(p.get("venue", ""))]
    ranked = sorted(top_only, key=relevance_score, reverse=True)

    by_domain: Dict[str, List[Dict]] = {"SE": [], "PL": [], "AI": [], "Security": []}
    for p in ranked:
        d = infer_domain_from_venue(p.get("venue", ""))
        if d in by_domain:
            by_domain[d].append(p)

    selected: List[Dict] = []
    selected_ids = set()

    # Ensure each requested domain appears with a minimum count when possible.
    for domain in ["SE", "PL", "AI", "Security"]:
        take = min(MIN_PER_DOMAIN, len(by_domain[domain]))
        for p in by_domain[domain][:take]:
            pid = p.get("paperId")
            if pid and pid not in selected_ids:
                selected.append(p)
                selected_ids.add(pid)

    for p in ranked:
        if len(selected) >= TARGET_COUNT:
            break
        pid = p.get("paperId")
        if pid and pid not in selected_ids:
            selected.append(p)
            selected_ids.add(pid)

    if len(selected) < TARGET_COUNT:
        raise RuntimeError(
            f"Only found {len(selected)} papers from configured top venues. "
            "Expand TOP_VENUE_PATTERNS or broaden query set."
        )

    enriched: List[Dict] = []
    for idx, p in enumerate(selected, start=1):
        summary = infer_summary(p.get("abstract", ""))
        strengths = infer_strengths(p)
        weaknesses = infer_weaknesses(p)

        row = {
            "index": idx,
            "paperId": p.get("paperId", ""),
            "title": p.get("title", ""),
            "authors": p.get("authors", ""),
            "year": p.get("year", ""),
            "venue": p.get("venue", ""),
            "citations": p.get("citations", 0),
            "url": p.get("url", ""),
            "openAccessPdf": p.get("openAccessPdf", ""),
            "summary": summary,
            "strong_points": strengths,
            "weaknesses": weaknesses,
            "pdf_download_status": "not_attempted",
            "pdf_file": "",
            "domain": infer_domain_from_venue(p.get("venue", "")),
        }

        pdf_url = row["openAccessPdf"]
        if DOWNLOAD_PDFS and pdf_url:
            year_str = str(row["year"]) if row["year"] else "na"
            fname = f"{idx:03d}_{year_str}_{safe_filename(row['title'])}.pdf"
            out_path = pdf_dir / fname
            ok, status = try_download_pdf(pdf_url, out_path)
            if ok:
                row["pdf_download_status"] = "downloaded"
                row["pdf_file"] = str(out_path.relative_to(root))
            else:
                row["pdf_download_status"] = f"failed: {status}"

        enriched.append(row)

    with (data_dir / "papers_100.json").open("w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    csv_fields = [
        "index",
        "domain",
        "title",
        "authors",
        "year",
        "venue",
        "citations",
        "url",
        "openAccessPdf",
        "summary",
        "strong_points",
        "weaknesses",
        "pdf_download_status",
        "pdf_file",
        "paperId",
    ]
    with (data_dir / "papers_100_summary.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(enriched)

    with (data_dir / "papers_100_summary.md").open("w", encoding="utf-8") as f:
        f.write("# 100 Related Papers for Refactoring-Stable Proof Repair\n\n")
        f.write(
            "Generated from OpenAlex metadata. Strengths/weaknesses are inferred from metadata and abstracts and should be validated during full-paper reading.\n\n"
        )
        for row in enriched:
            f.write(f"## {row['index']}. {row['title']} ({row['year']})\n")
            f.write(f"- Domain: {row['domain']}\n")
            f.write(f"- Authors: {row['authors'] or 'N/A'}\n")
            f.write(f"- Venue: {row['venue'] or 'N/A'}\n")
            f.write(f"- Citations: {row['citations']}\n")
            f.write(f"- URL: {row['url'] or 'N/A'}\n")
            f.write(f"- Open-access PDF: {row['openAccessPdf'] or 'N/A'}\n")
            f.write(f"- PDF download: {row['pdf_download_status']}\n")
            if row["pdf_file"]:
                f.write(f"- Local PDF file: {row['pdf_file']}\n")
            f.write(f"- Summary: {row['summary']}\n")
            f.write(f"- Strong points: {row['strong_points']}\n")
            f.write(f"- Weaknesses: {row['weaknesses']}\n\n")

    downloaded = sum(1 for r in enriched if r["pdf_download_status"] == "downloaded")
    domain_stats: Dict[str, int] = {}
    for r in enriched:
        domain_stats[r["domain"]] = domain_stats.get(r["domain"], 0) + 1

    print(f"Selected papers: {len(enriched)}")
    print(f"Downloaded open-access PDFs: {downloaded}")
    print(f"Domain distribution: {domain_stats}")
    print("Outputs:")
    print("- data/papers_100_summary.md")
    print("- data/papers_100_summary.csv")
    print("- data/papers_100.json")


if __name__ == "__main__":
    main()
