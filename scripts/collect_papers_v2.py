#!/usr/bin/env python3
"""
Collect 100 papers for thesis: Refactoring-Stable Proof Repair
Topics: proof repair, verification, refactoring, code evolution, formal methods, SMT solving
"""
import json
import urllib.request
import urllib.error
import time
import urllib.parse
from pathlib import Path
from collections import Counter

API_BASE = "https://api.openalex.org/works"

# Search queries aligned with thesis topics
QUERIES = [
    "proof repair",
    "refactoring software",
    "formal verification",
    "SMT solver",
    "program repair", 
    "invariant generation",
    "theorem proving",
    "symbolic execution",
    "type systems verification",
    "model checking",
    "automated reasoning",
    "constraint solving",
    "proof synthesis",
    "code evolution",
    "static analysis",
    "program synthesis",
    "specification mining",
    "test generation",
    "verification condition",
    "abstract interpretation",
]

# Top-tier venues by domain (for filtering later)
TOP_VENUES = {
    # SE
    "ICSE", "FSE", "ASE", "ISSTA", "TOSEM", "TSE", "EMSE",
    # PL
    "PLDI", "POPL", "OOPSLA", "ICFP", "ECOOP", "CAV", "VMCAI",
    # AI
    "NeurIPS", "ICML", "ICLR", "AAAI", "IJCAI",
}

BAD_KEYWORDS = {
    "medical", "clinical", "disease", "cancer", "drug", "nursing",
    "biology", "agriculture", "psychology", "sports",
}

def fetch_papers_simple(query, pages=3):
    """Fetch papers without strict filtering (faster)."""
    papers = []
    
    for page in range(1, pages + 1):
        url = f"{API_BASE}?search={urllib.parse.quote(query)}&per_page=50&page={page}&sort=-cited_by_count"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            for work in data.get("results", []):
                # Basic checks only
                if not work.get("title") or not work.get("doi"):
                    continue
                
                venue = work.get("primary_location", {}).get("source", {}).get("display_name", "")
                
                paper = {
                    "paperId": work.get("id", ""),
                    "title": work.get("title", ""),
                    "authors": [a.get("author", {}).get("display_name", "") 
                               for a in work.get("authorships", [])[:5]],
                    "year": work.get("publication_year", 0),
                    "venue": venue,
                    "citations": work.get("cited_by_count", 0),
                    "url": work.get("doi", ""),
                    "openAccessPdf": work.get("best_oa_location", {}).get("pdf_url", ""),
                }
                papers.append(paper)
            
            time.sleep(1.0)  # Polite delay
        except Exception as e:
            print(f"      ⚠ Page {page}: {type(e).__name__}")
            time.sleep(2)
    
    return papers

def is_good_venue(venue_str):
    """Check if venue is from a good conference/journal."""
    if not venue_str:
        return False
    v = venue_str.lower()
    return any(tv.lower() in v for tv in TOP_VENUES)

def is_good_paper(paper):
    """Check if paper is relevant and from good source."""
    title = paper.get("title", "").lower()
    venue = paper.get("venue", "").lower()
    
    # Skip blacklisted
    if any(bad in title or bad in venue for bad in BAD_KEYWORDS):
        return False
    
    # Check venue
    return is_good_venue(paper.get("venue", ""))

def main():
    print("🔍 Collecting papers from OpenAlex...")
    print(f"   Queries: {len(QUERIES)}, Pages per query: 3\n")
    
    all_papers = {}
    
    for i, query in enumerate(QUERIES, 1):
        print(f"  [{i:2d}/{len(QUERIES)}] {query:30s} ", end="", flush=True)
        papers = fetch_papers_simple(query, pages=3)
        
        # Deduplicate
        for p in papers:
            pid = p["paperId"]
            if pid not in all_papers:
                all_papers[pid] = p
        
        print(f"→ {len(papers):3d} found, {len(all_papers):4d} total")
    
    print(f"\n✓ Collected {len(all_papers)} unique papers (raw)")
    
    # Filter to good venues
    good_papers = [p for p in all_papers.values() if is_good_paper(p)]
    print(f"✓ After venue filtering: {len(good_papers)} papers from top venues")
    
    # Sort by citations + year
    ranked = sorted(good_papers, 
                   key=lambda x: (x["citations"], -x["year"]),
                   reverse=True)
    
    # Select top 100
    selected = ranked[:100]
    
    # Add metadata fields
    for i, p in enumerate(selected, 1):
        p["index"] = i
        # Infer domain
        v = p.get("venue", "").lower()
        if any(x in v for x in ["icse", "fse", "ase", "issta", "tosem", "tse", "emse"]):
            domain = "SE"
        elif any(x in v for x in ["pldi", "popl", "oopsla", "icfp", "cav", "vmcai", "ecoop"]):
            domain = "PL"
        elif any(x in v for x in ["neurips", "icml", "iclr", "aaai", "ijcai"]):
            domain = "AI"
        else:
            domain = "Other"
        p["domain"] = domain
        p["summary"] = ""
        p["strong_points"] = ""
        p["weaknesses"] = ""
        p["pdf_download_status"] = "pending"
        p["pdf_file"] = ""
    
    # Save JSON
    root = Path("/Users/ngonhattoan/PycharmProjects/Thesis")
    json_path = root / "data" / "papers_100.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2))
    
    # Stats
    domain_dist = Counter(p["domain"] for p in selected)
    print(f"\n📊 Selected {len(selected)} papers:")
    for domain, count in sorted(domain_dist.items(), key=lambda x: -x[1]):
        print(f"   {domain:8s}: {count:3d} papers")
    
    print(f"\n✓ Saved to: {json_path}")
    print(f"   Next steps: Generate summaries, download PDFs")

if __name__ == "__main__":
    main()
