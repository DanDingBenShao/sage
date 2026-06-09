#!/usr/bin/env python3
"""
构建职业专家 System Prompt。

用法:
  python _build_expert.py video-editor          # 输出 system prompt
  python _build_expert.py video-editor --chat   # 交互式对话
  python _build_expert.py video-editor --ask "怎么调B站音频响度"
"""
import json, os, re, sys, urllib.request, ssl
from pathlib import Path
from collections import defaultdict

ssl._create_default_https_context = ssl._create_unverified_context

WIKI = Path("D:/TOOLS/cloude code/sage/kb/wiki")
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE = os.environ.get("DEEPSEEK_BASE", "https://api.deepseek.com")


def resolve_wikilinks(content: str, src_dir: str, all_pages: dict) -> list:
    """解析 wikilink，返回实际文件路径列表"""
    targets = []
    for m in re.finditer(r'\[\[([^\]]+)\]\]', content):
        target = m.group(1).split("|")[0].strip()
        # 跨层路径 (general/..., professions/...)
        if "/" in target:
            path = target + ".md"
            if path in all_pages:
                targets.append(path)
        else:
            # 同级目录
            path = src_dir + "/" + target + ".md"
            if path in all_pages:
                targets.append(path)
            else:
                # fallback: 全局搜索
                for p in all_pages:
                    if p.endswith("/" + target + ".md"):
                        targets.append(p)
                        break
    return targets


def load_all_pages() -> dict:
    """加载所有 wiki 页面，返回 {rel_path: (frontmatter, body)}"""
    pages = {}
    for f in sorted(WIKI.rglob("*.md")):
        if f.name.startswith("_") and f.name != "_index.md":
            continue
        rel = str(f.relative_to(WIKI)).replace("\\", "/")
        content = f.read_text(encoding="utf-8")
        pages[rel] = content
    return pages


def build_expert(profession: str, all_pages: dict) -> str:
    """构建一个职业专家的完整 system prompt"""
    prof_dir = f"professions/{profession}"
    profile_path = f"{prof_dir}/profile.md"

    if profile_path not in all_pages:
        raise ValueError(f"职业 {profession} 不存在 ({profile_path})")

    profile = all_pages[profile_path]

    # 收集该职业的所有页面
    own_pages = {}
    for path, content in all_pages.items():
        if path.startswith(prof_dir + "/") and not path.endswith("profile.md"):
            own_pages[path] = content

    # 从 profile 中提取引用的 general/ 页面
    general_refs = set()
    for m in re.finditer(r'\[\[(general/[^\]]+)\]\]', profile):
        target = m.group(1).split("|")[0].strip()
        path = target + ".md"
        if path in all_pages:
            general_refs.add(path)

    # 从所有自有页面中也提取 general 引用
    for content in own_pages.values():
        for m in re.finditer(r'\[\[(general/[^\]]+)\]\]', content):
            target = m.group(1).split("|")[0].strip()
            path = target + ".md"
            if path in all_pages:
                general_refs.add(path)

    # 构建 system prompt
    parts = []

    # 1. 职业定位
    prof_name = ""
    prof_desc = ""
    for line in profile.split("\n"):
        if line.startswith("title:"):
            prof_name = line.split(":", 1)[1].strip()
        if line.startswith("description:"):
            prof_desc = line.split(":", 1)[1].strip()

    parts.append(f"你是{prof_name}。{prof_desc}")
    parts.append("")
    parts.append("## 你的知识")
    parts.append("")
    parts.append("你掌握以下专业知识。回答问题时直接使用这些知识，不要说你不知道（你知道的就是下面这些）。如果问题超出你的知识范围，诚实说明。")
    parts.append("")

    # 2. 自有专业知识
    parts.append(f"### 专业知识 (professions/{profession}/)")
    parts.append("")
    for path in sorted(own_pages.keys()):
        content = own_pages[path]
        # 提取 frontmatter title
        title = ""
        body = content
        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                fm = content[3:fm_end]
                body = content[fm_end + 3:].strip()
                for line in fm.split("\n"):
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip()
        name = title or Path(path).stem.replace("-", " ").title()
        parts.append(f"#### {name}")
        parts.append(body[:2000])  # 每页最多2000字
        parts.append("")

    # 3. 通用知识引用
    if general_refs:
        parts.append("### 通用基础知识 (general/)")
        parts.append("")
        for path in sorted(general_refs):
            content = all_pages[path]
            title = ""
            body = content
            if content.startswith("---"):
                fm_end = content.find("---", 3)
                if fm_end > 0:
                    fm = content[3:fm_end]
                    body = content[fm_end + 3:].strip()
                    for line in fm.split("\n"):
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip()
            name = title or Path(path).stem.replace("-", " ").title()
            parts.append(f"#### {name}")
            parts.append(body[:1500])
            parts.append("")

    # 4. 行为准则
    parts.append("## 行为准则")
    parts.append("")
    parts.append("- 你是专家，直接用你的知识回答问题")
    parts.append("- 给出具体的、可操作的答案，包含命令、参数、数值")
    parts.append("- 如果用户的问题模糊，追问具体场景再给建议")
    parts.append("- 用中文回答")
    parts.append("")
    parts.append("现在，用户会向你提问。请用你的专业知识回答。")

    return "\n".join(parts)


def estimate_cost(text: str) -> float:
    """估算 token 数 (中文 ~2 chars/token)"""
    return len(text) / 2


# ====== CLI ======
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if len(sys.argv) < 2:
        print("用法: python _build_expert.py <profession> [--chat | --ask '问题']")
        print("可用职业: video-editor, software-dev")
        sys.exit(1)

    profession = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "build"
    question = sys.argv[3] if len(sys.argv) > 3 else None

    if mode == "--ask" and len(sys.argv) < 4:
        question = input("问题: ")

    print(f"构建 {profession} 专家...", file=sys.stderr)
    all_pages = load_all_pages()
    system_prompt = build_expert(profession, all_pages)

    prompt_tokens = estimate_cost(system_prompt)
    print(f"System Prompt: {len(system_prompt)} 字符 (~{prompt_tokens:.0f} tokens)", file=sys.stderr)

    if mode == "build":
        print(system_prompt)

    elif mode in ("--ask", "--chat"):
        if not API_KEY:
            print("ERROR: DEEPSEEK_API_KEY 未设置", file=sys.stderr)
            sys.exit(1)

        if mode == "--chat":
            print(f"\n{'='*60}")
            print(f"  {profession} 专家已就绪 ({len(all_pages)}页知识)")
            print(f"  System prompt: {len(system_prompt)} chars (~{prompt_tokens:.0f} tokens)")
            print(f"  输入问题开始对话，输入 quit 退出")
            print(f"{'='*60}\n")

        while True:
            if mode == "--chat":
                try:
                    question = input(">>> ").strip()
                except (EOFError, KeyboardInterrupt):
                    break
                if question.lower() in ("quit", "exit", "q"):
                    break
                if not question:
                    continue

            body = json.dumps({
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                "max_tokens": 2048,
                "temperature": 0.3,
            }).encode("utf-8")

            req = urllib.request.Request(
                f"{DEEPSEEK_BASE}/v1/chat/completions",
                data=body,
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            )

            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    reply = json.loads(resp.read())["choices"][0]["message"]["content"]
                usage = json.loads(resp.read() if 'resp' in dir() else '{}') if False else None
                print(reply)
                print()
            except Exception as e:
                print(f"API 错误: {e}", file=sys.stderr)

            if mode == "--ask":
                break
