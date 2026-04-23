#!/usr/bin/env python3
"""
Collect 100 papers for thesis: Refactoring-Stable Proof Repair
Topics: proof repair, verification, refactoring, code evolution, formal methods, SMT solving
Venues: Top-tier SE (ICSE, FSE), PL (PLDI, OOPSLA, CAV), AI conferences
"""
import json
import urllib.request
import urllib.error
import time
import urllib.parse
from pathlib import Path
from collections import Counter

API_BASE = "https://api.openalex.org/works"
REQUEST_DELAY = 0.5
TIMEOUT = 10

# Search queries aligned with thesis topics
QUERIES = [
    "proof repair verification",
    "refactoring software evolution",  
    "code refactoring maintenance",
    "formal verification program",
    "SMT solver satisfiability",
    "automated program repair",
    "invariant generation assertion",
    "theorem proving proof assistant",
    "verification condition synthesis",
    "abstract interpretation static analysis",
    "symbolic execution test generation",
    "counterexample guided synthesis",
    "specification mining temporal logic",
    "model checking bounded model checking",
    "type systems dependent types verification",
    "constraint solving satisfiability modulo",
    "proof automation lemma discovery",
    "program synthesis machine learning",
    "regression testing continuous verification",
    "code transformation semantics preservation",
]

# Top-tier venues by domain
GOOD_VENUES = {
    # Software Engineering
    "ICSE", "FSE", "ASE", "ISSTA", "ICSME", "TOSEM", "TSE", "EMSE",
    "IEEE Transactions on Software Engineering",
    "ACM Transactions on Software Engineering and Methodology",
    
    # Programming Languages & Verification
    "PLDI", "POPL", "OOPSLA", "ICFP", "ECOOP", "CAV", "VMCAI", "SAC",
    "ACM Transactions on Programming Languages and Systems",
    "Logical Methods in Computer Science",
    "Journal of Functional Programming",
    "Proceedings of the ACM on Programming Languages",
    
    # AI & Machine Learning
    "NeurIPS", "ICML", "ICLR", "AAAI", "IJCAI", "AISTATS",
    "Journal of Machine Learning Research",
}

BAD_KEYWORDS = {
    "medical", "clinical", "disease", "cancer", "drug", "nursing",
    "biology", "agriculture", "dentistry", "cardiology", "psychology",
    "sports", "education", "social", "music", "art", "design",
}

def fetch_openalex_query(query, pages=6):
    """Fetch papers from OpenAlex for single query with retry logic."""
    papers = []
    for page in range(1, pages + 1):
        url = f"{API_BASE}?search={urllib.parse.quote(query)}&per_page=50&page={page}&sort=-publication_date"
        
        # Retry with exponential backoff
        for attempt in range(3):
            try:
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                        "Accept": "application/json"
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                
                for work in data.get("results", []):
                    # Skip if no full text
                    venue = work.get("primary_location", {}).get("source", {}).get("display_name", "")
                    if not venue:
                        continue
                    
                    # Check venue quality
                    venue_lower = venue.lower()
                    if not any(v.lower() in venue_lower for v in GOOD_VENUES):
                        continue
                    
                    # Skip blacklisted domains
                    title_lower = work.get("title", "").lower()
                    if any(bad in title_lower or bad in venue_lower for bad in BAD_KEYWORDS):
                        continue
                    
                    # Must have DOI
                    doi = work.get("doi", "")
                    if not doi:
                        continue
                    
                    paper = {
                        "paperId": work.get("id", "").split("/")[-1],
                        "title": work.get("title", ""),
                        "authors": [a.get("author", {}).get("display_name", "")
                                   for a in work.get("authorships", [])[:5]],
                        "year": work.get("publication_year", 0),
                        "venue": venue,
                        "citations": work.get("cited_by_count", 0),
                        "url": doi,
                        "openAccessPdf": work.get("best_oa_location", {}).get("pdf_url", ""),
                    }
                    papers.append(paper)
                
                time.sleep(REQUEST_DELAY)
                break  # Success, break retry loop
            
            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    time.sleep(wait)
                else:
                    pass  # Final attempt failed, continue to next page
    
    return papers

def infer_domain(venue):
    """Infer domain from venue name."""
    v = venue.lower()
    if any(x in v for x in ["icse", "fse", "ase", "issta", "tosem", "tse", "emse"]):
        return "SE"
    elif any(x in v for x in ["pldi", "popl", "oopsla", "icfp", "cav", "vmcai", "ecoop"]):
        return "PL"
    elif any(x in v for x in ["neurips", "icml", "iclr", "aaai", "ijcai", "aistats"]):
        return "AI"
    else:
        return "Other"

def main():
    print("🔍 Collecting papers from OpenAlex...")
    print(f"   Queries: {len(QUERIES)}, Pages per query: 6, Max results: 50/page\n")
    
    all_papers = {}
    
    for i, query in enumerate(QUERIES, 1):
        print(f"  [{i:2d}/{len(QUERIES)}] {query:40s} ", end="", flush=True)
        papers = fetch_openalex_query(query)
        
        # Deduplicate by paperId
        for p in papers:
            if p["paperId"] not in all_papers:
                all_papers[p["paperId"]] = p
        
        print(f"→ {len(papers):3d} results, {len(all_papers):4d} total")
    
    print(f"\n✓ Collected {len(all_papers)} unique papers")
    
    # Sort by relevance score
    ranked = sorted(
        all_papers.values(),
        key=lambda x: (x["citations"], -x["year"]),
        reverse=True
    )
    
    # Select 100 with domain balance
    selected = []
    domain_limits = {"SE": 35, "PL": 35, "AI": 25, "Other": 5}
    domain_counts = Counter()
    
    for paper in ranked:
        domain = infer_domain(paper["venue"])
        if domain_counts[domain] < domain_limits.get(domain, 0):
            selected.append(paper)
            domain_counts[domain] += 1
        
        if len(selected) >= 100:
            break
    
    # If not enough, add remainder
    if len(selected) < 100:
        for paper in ranked:
            if paper not in selected:
                selected.append(paper)
            if len(selected) >= 100:
                break
    
    # Add index and domain
    for i, p in enumerate(selected[:100], 1):
        p["index"] = i
        p["domain"] = infer_domain(p["venue"])
        p["summary"] = ""  # Will add summaries later
        p["strong_points"] = ""
        p["weaknesses"] = ""
        p["pdf_download_status"] = "pending"
        p["pdf_file"] = ""
    
    # Save JSON
    root = Path("/Users/ngonhattoan/PycharmProjects/Thesis")
    json_path = root / "data" / "papers_100.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(selected[:100], ensure_ascii=False, indent=2))
    
    # Domain stats
    domain_dist = Counter(p["domain"] for p in selected[:100])
    print(f"\n📊 Domain distribution:")
    for domain, count in sorted(domain_dist.items(), key=lambda x: -x[1]):
        print(f"   {domain:8s}: {count:3d} papers")
    
    print(f"\n✓ Saved {len(selected[:100])} papers to: {json_path}")
    print(f"   Ready for: PDF download, summary generation, and metadata enrichment")

if __name__ == "__main__":
    main()
