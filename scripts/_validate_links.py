#!/usr/bin/env python3
"""Validate wiki structure — broken wikilinks + orphan pages"""
import re, sys
from pathlib import Path
from collections import defaultdict

WIKI = Path("D:/TOOLS/cloude code/sage/kb/wiki")

pages = {}
all_links = defaultdict(set)
inbound = defaultdict(set)

for f in sorted(WIKI.rglob("*.md")):
    rel = str(f.relative_to(WIKI)).replace("\\", "/")
    content = f.read_text(encoding='utf-8')
    pages[rel] = content

for rel, content in pages.items():
    for link in re.findall(r'\[\[([^\]]+)\]\]', content):
        target = link.split("|")[0].strip()
        all_links[rel].add(target)
        inbound[target].add(rel)

print(f"Pages: {len(pages)}")
print(f"Wikilinks: {sum(len(v) for v in all_links.values())}")
print()

# Broken links
print("=" * 60)
print("Broken Links")
print("=" * 60)
broken = 0
META_EXAMPLES = {"page1", "page2", "page-name", "dir/page-name", "../dir/page-name",
                 "example-page-1", "example-page-2", "wikilinks"}
for rel, links in all_links.items():
    src_dir = str(Path(rel).parent) + "/"
    for target in links:
        if target in META_EXAMPLES:
            continue
        candidates = [
            target + ".md",
            src_dir + target + ".md",
        ]
        found = any(c in pages for c in candidates)
        if not found:
            basename = Path(target).stem
            for p in pages:
                if p.endswith("/" + target + ".md") or p.endswith("/" + basename + ".md"):
                    found = True
                    break
        if not found:
            print(f"  BROKEN: [{rel}] -> [[{target}]]")
            broken += 1

print(f"  {'[OK] No broken links' if broken == 0 else f'{broken} broken links'}")

# Orphans
print()
print("=" * 60)
print("Orphan Pages (no inbound + no outbound)")
print("=" * 60)
orphans = []
META_SKIP = {"_schema.md", "_index.md", "_log.md", "rules.md", "false-beliefs.md", "kb-CLAUDE.md"}
for rel in pages:
    if rel in META_SKIP or rel.endswith("profile.md"):
        continue
    basename = Path(rel).stem
    has_inbound = (rel in inbound or rel.replace(".md", "") in inbound or basename in inbound)
    has_outbound = rel in all_links and len(all_links[rel]) > 0
    if not has_inbound:
        print(f"  NO INBOUND: {rel}")
        orphans.append(rel)
    if not has_outbound:
        print(f"  NO OUTBOUND: {rel}")
        if rel not in orphans:
            orphans.append(rel)

print(f"  {'[OK] No orphan pages' if not orphans else f'{len(orphans)} orphan pages'}")

# Layer stats
print()
print("=" * 60)
print("Layer Distribution")
print("=" * 60)
for layer in ["general", "professions", "projects"]:
    count = sum(1 for p in pages if p.startswith(layer + "/"))
    print(f"  {layer}/: {count} pages")

root_meta = [p for p in pages if "/" not in p]
print(f"  root/: {len(root_meta)} pages")

for prof_dir in sorted((WIKI / "professions").iterdir()):
    if prof_dir.is_dir():
        count = len(list(prof_dir.rglob("*.md")))
        print(f"    professions/{prof_dir.name}/: {count} pages")
