#!/usr/bin/env python3
"""Turn a blog_critic.py run into WordPress (Gutenberg) block markup: summary, editor synthesis, then every item with
all five critiques in collapsible Details blocks, with prompts, models, timing and token counts.

  python3 agents/blog_critic_to_wp.py results/blog_critique   -> results/blog_critique/wp_post.html
"""
import html
import json
import re
import sys
from pathlib import Path

ROLE_NAMES = {"methods_referee": "Methods and statistics referee", "ecm_biologist": "ECM and aging biologist",
              "simulation_auditor": "Simulation auditor", "integrity_auditor": "Research-integrity auditor",
              "science_communicator": "Science editor", "synthesis": "Editor-in-chief synthesis"}


def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def para(t):
    return f"<!-- wp:paragraph -->\n<p>{t}</p>\n<!-- /wp:paragraph -->"


def heading(t, level):
    return f'<!-- wp:heading {{"level":{level}}} -->\n<h{level} class="wp-block-heading">{t}</h{level}>\n<!-- /wp:heading -->'


def md_blocks(md, base_level=4):
    """Small markdown -> core blocks converter (headings, bullet/numbered lists, paragraphs)."""
    out, lst, ordered = [], [], False

    def flush():
        nonlocal lst
        if lst:
            tag = "ol" if ordered else "ul"
            attrs = ' {"ordered":true}' if ordered else ""
            items = "\n".join(f"<!-- wp:list-item -->\n<li>{x}</li>\n<!-- /wp:list-item -->" for x in lst)
            out.append(f"<!-- wp:list{attrs} -->\n<{tag} class=\"wp-block-list\">{items}</{tag}>\n<!-- /wp:list -->")
            lst = []

    buf = []

    def flush_para():
        nonlocal buf
        if buf:
            out.append(para(inline(" ".join(buf))))
            buf = []

    for raw in md.splitlines():
        line = raw.rstrip()
        m_h = re.match(r"^(#{1,6})\s+(.*)", line)
        m_b = re.match(r"^\s*[-*•]\s+(.*)", line)
        m_n = re.match(r"^\s*\d+[.)]\s+(.*)", line)
        if not line.strip():
            flush_para(); flush(); continue
        if m_h:
            flush_para(); flush()
            out.append(heading(inline(m_h.group(2).strip("# ")), min(6, base_level + max(0, len(m_h.group(1)) - 2))))
        elif m_b or m_n:
            flush_para()
            if lst and ordered != bool(m_n):
                flush()
            ordered = bool(m_n)
            lst.append(inline((m_b or m_n).group(1)))
        elif line.strip() in ("---", "***"):
            flush_para(); flush()
        else:
            flush()
            buf.append(line.strip())
    flush_para(); flush()
    return "\n\n".join(out)


def details(summary, inner):
    return (f"<!-- wp:details -->\n<details class=\"wp-block-details\"><summary>{summary}</summary>"
            f"{inner}</details>\n<!-- /wp:details -->")


def main(res):
    res = Path(res)
    items = json.loads((res / "items.json").read_text())
    log = [json.loads(l) for l in (res / "log.jsonl").read_text().splitlines()]
    synth = json.loads((res / "synthesis.json").read_text())
    meta = json.loads((res / "meta.json").read_text())
    b = []
    b.append(para(inline(
        f"An experiment in AI peer review. A swarm of five independent critic agents, each a different Gemini model "
        f"with its own reviewer role, read every public post and page on this site ({meta['items']} items, "
        f"{meta['critiques']} critiques), and an editor agent synthesised the results. This is the complete, unedited "
        f"log, published for the learning record. The critiques are AI-generated: they can be wrong, and they have not "
        f"been fact-checked. Run on {meta['run_utc']} through the Gemini API (ScienceClaw hackathon lab account).")))
    roles = "".join(f"<li><strong>{ROLE_NAMES[r]}</strong> — <code>{m}</code></li>" for r, m in meta["roles"].items())
    b.append(heading("The panel", 2))
    b.append(f"<!-- wp:list -->\n<ul class=\"wp-block-list\">{roles}<li><strong>Editor-in-chief synthesis</strong> — <code>{meta['synthesis_model']}</code></li></ul>\n<!-- /wp:list -->")
    b.append(para(inline(f"Shared instruction to every critic: {log[0]['instruction']}")))
    b.append(heading("Editor-in-chief synthesis", 2))
    b.append(md_blocks(synth.get("text") or "(synthesis failed: " + str(synth.get("error")) + ")", 3))
    b.append(heading("Every critique, item by item", 2))
    by_item = {}
    for r in log:
        by_item.setdefault(r["item_id"], []).append(r)
    for it in items:
        b.append(heading(f'<a href="{html.escape(it["url"])}">{html.escape(it["title"])}</a>', 3))
        b.append(para(inline(f"{it['kind'].title()}, {it['date'][:10]}, {len(it['text']):,} characters.")))
        for r in sorted(by_item.get(it["id"], []), key=lambda r: list(ROLE_NAMES).index(r["role"])):
            u = r.get("usage") or {}
            head = (f"{ROLE_NAMES[r['role']]} · {html.escape(r['model'])} · {r['seconds']} s · "
                    f"{u.get('prompt_tokens', '?')} in / {u.get('completion_tokens', '?')} out tokens")
            body = md_blocks(r["text"]) if r["text"] else para(inline(f"Error: {r['error']}"))
            body = para(f"<em>Reviewer role: {html.escape(r['system_prompt'])}</em>") + "\n\n" + body
            b.append(details(head, body))
    b.append(heading("Method", 2))
    b.append(para(inline(
        "Items were fetched from the public WordPress.com API and converted to plain text (tables flattened). Each "
        "critic saw one item at a time with its role prompt; an item's text was treated as material, not instructions. "
        f"Total tokens: {meta['usage']['prompt_tokens']:,} in, {meta['usage']['completion_tokens']:,} out; "
        f"{meta['errors']} failed calls. Code: agents/blog_critic.py on branch claude/oxidative-tensegrity of "
        "InquilineKea/gaia-hackathon-2026-codex-openbci-motion-tracking.")))
    text = "\n\n".join(b)
    (res / "wp_post.html").write_text(text)
    print("wrote", res / "wp_post.html", len(text), "chars")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/blog_critique")
