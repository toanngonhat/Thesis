#!/usr/bin/env python3
"""
Collect 100 papers using curl (more reliable than Python urllib on macOS)
"""
import json
import subprocess
import time
from pathlib import Path
from collections import Counter

# Queries
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

TOP_VENUES = {
    "ICSE", "FSE", "ASE", "ISSTA", "TOSEM", "TSE", "EMSE",
    "PLDI", "POPL", "OOPSLA", "ICFP", "ECOOP", "CAV", "VMCAI",
    "NeurIPS", "ICML", "ICLR", "AAAI", "IJCAI",
}

BAD_KEYWORDS = {"medical", "clinical", "disease", "cancer", "drug", "nursing", "biology", "psychology"}

def fetch_with_curl(query, pages=3):
    """Fetch papers using curl - NO FILTERING HERE, just collect."""
    import urllib.parse
    papers = []
    
    for page in range(1, pages + 1):
        query_enc = urllib.parse.quote(query)
        url = f"https://api.openalex.org/works?search={query_enc}&per_page=50&page={page}&sort=-cited_by_count"
        
        try:
            result = subprocess.run(
                ["curl", "-s", url],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                print(f"      ⚠ Page {page}")
                time.sleep(1)
                continue
            
            data = json.loads(result.stdout)
            
            # Accept ANY result from search
            for work in data.get("results", []):
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
            
            time.sleep(0.5)
        except Exception as e:
            print(f"      ⚠ Page {page}: {type(e).__name__}")
            time.sleep(1)
    
    return papers

def is_good_paper(paper):
    """Filter paper by venue and keywords - RELAXED."""
    title = (paper.get("title", "") + " " + paper.get("venue", "")).lower()
    
    if any(bad in title for bad in BAD_KEYWORDS):
        return False
    
    venue = paper.get("venue", "").lower()
    
    # Accept if from a TOP venue
    if any(tv.lower() in venue for tv in TOP_VENUES):
        return True
    
    # OR if highly cited (>100 citations suggests quality)
    if paper.get("citations", 0) >= 100:
        return True
    
    # OR if from recognizable academic venue containing "proceeding", "journal", "transactions"
    if any(word in venue for word in ["proceeding", "journal", "transaction", "conference"]):
        # But exclude obvious spam
        if not any(x in venue for x in ["medical", "clinical", "nursing", "agriculture"]):
            return True
    
    return False

def main():
    print("🔍 Collecting papers using curl...\n")
    
    all_papers = {}
    
    for i, query in enumerate(QUERIES, 1):
        print(f"  [{i:2d}/{len(QUERIES)}] {query:30s} ", end="", flush=True)
        papers = fetch_with_curl(query, pages=3)
        
        for p in papers:
            pid = p["paperId"]
            if pid not in all_papers:
                all_papers[pid] = p
        
        print(f"→ {len(papers):3d} found, {len(all_papers):4d} total")
    
    print(f"\n✓ Collected {len(all_papers)} unique papers (raw)")
    
    # Filter
    good = [p for p in all_papers.values() if is_good_paper(p)]
    good_ranked = sorted(good, key=lambda x: (x["citations"], -x["year"]), reverse=True)
    selected = good_ranked[:100]
    
    print(f"✓ After filtering: {len(selected)} from top venues")
    
    # Add metadata
    for i, p in enumerate(selected, 1):
        p["index"] = i
        v = p.get("venue", "").lower()
        if any(x in v for x in ["icse", "fse", "ase", "issta", "tosem", "tse"]):
            domain = "SE"
        elif any(x in v for x in ["pldi", "popl", "oopsla", "icfp", "cav"]):
            domain = "PL"
        elif any(x in v for x in ["neurips", "icml", "iclr", "aaai"]):
            domain = "AI"
        else:
            domain = "Other"
        p["domain"] = domain
        p["summary"] = ""
        p["strong_points"] = ""
        p["weaknesses"] = ""
        p["pdf_download_status"] = "pending"
        p["pdf_file"] = ""
    
    # Save
    root = Path("/Users/ngonhattoan/PycharmProjects/Thesis")
    json_path = root / "data" / "papers_100.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2))
    
    dist = Counter(p["domain"] for p in selected)
    print(f"\n📊 Selected {len(selected)} papers:")
    for d, c in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"   {d:8s}: {c:3d}")
    
    print(f"\n✓ Saved to: data/papers_100.json")

if __name__ == "__main__":
    main()
