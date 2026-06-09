#!/usr/bin/env python3
"""验证新结构完整性 — wikilink断链 + 孤儿页"""
import re, sys
from pathlib import Path
from collections import defaultdict

WIKI = Path("D:/TOOLS/cloude code/sage/kb/wiki")

# 收集所有页面和它们的 wikilinks
pages = {}      # relative_path → content
all_links = defaultdict(set)  # page → set of outbound links
inbound = defaultdict(set)    # page → set of inbound links

for f in sorted(WIKI.rglob("*.md")):
    rel = str(f.relative_to(WIKI)).replace("\\", "/")
    content = f.read_text(encoding='utf-8')
    pages[rel] = content

# 提取 wikilinks
for rel, content in pages.items():
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    for link in links:
        # 去掉可能的别名 ([[target|alias]])
        target = link.split("|")[0].strip()
        all_links[rel].add(target)
        inbound[target].add(rel)

print(f"总页面: {len(pages)}")
print(f"总 wikilink 引用: {sum(len(v) for v in all_links.values())}")
print()

# 检查断链
print("=" * 60)
print("断链检查")
print("=" * 60)
broken = 0
for rel, links in all_links.items():
    src_dir = str(Path(rel).parent) + "/"
    for target in links:
        candidates = [
            target + ".md",                          # 同级目录
            src_dir + target + ".md",                # 同级目录 (带路径)
            target.replace("::", "/") + ".md",       # C++ 引用修复
        ]
        found = any(c in pages for c in candidates)
        if not found:
            # 也尝试直接匹配（target 可能已含路径）
            if target in pages or (target + ".md") in pages:
                found = True
        if not found:
            # 尝试从根目录查找
            for p in pages:
                if p.endswith("/" + target + ".md") or p == target + ".md":
                    found = True
                    break
        if not found:
            print(f"  BROKEN: [{rel}] → [[{target}]]")
            broken += 1

if broken == 0:
    print("  ✅ 无断链")
else:
    print(f"\n  共 {broken} 个断链")

# 孤儿页检查
print()
print("=" * 60)
print("孤儿页检查 (无入链 + 无出链)")
print("=" * 60)
orphans = []
for rel in pages:
    rel_no_ext = rel.replace(".md", "")
    has_inbound = rel in inbound or rel_no_ext in inbound
    has_outbound = rel in all_links and len(all_links[rel]) > 0

    # 跳过 meta 文件和 profile.md（它们是入口点，不算孤儿）
    if rel in ("_schema.md", "_index.md", "_log.md", "rules.md", "false-beliefs.md", "kb-CLAUDE.md"):
        continue
    if rel.endswith("profile.md"):
        continue

    if not has_inbound:
        print(f"  NO INBOUND: {rel}")
        orphans.append(rel)
    if not has_outbound:
        print(f"  NO OUTBOUND: {rel}")
        if rel not in orphans:
            orphans.append(rel)

if not orphans:
    print("  ✅ 无孤儿页")

# 按层统计
print()
print("=" * 60)
print("各层页面分布")
print("=" * 60)
for layer in ["general", "professions", "projects"]:
    count = sum(1 for p in pages if p.startswith(layer + "/"))
    print(f"  {layer}/: {count} 页")

root_meta = [p for p in pages if "/" not in p]
print(f"  root/: {len(root_meta)} 页 ({', '.join(root_meta)})")

# 职业统计
for prof_dir in (WIKI / "professions").iterdir():
    if prof_dir.is_dir():
        count = len(list(prof_dir.rglob("*.md")))
        print(f"  professions/{prof_dir.name}/: {count} 页")
