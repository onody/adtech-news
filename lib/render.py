#!/usr/bin/env python3
"""out/<date>.json を メール用の HTML とプレーンテキストにレンダリングする。

usage: render.py <digest.json>
出力: 同じディレクトリの <date>.html / <date>.txt
"""
import json
import os
import sys
from html import escape

FG = "#1a1a1a"
MUTED = "#6b7280"
RULE = "#e5e7eb"
ACCENT = "#1f6feb"
LABEL = "#b45309"

LABELS = {
    "ja": {
        "asis": "ASIS",
        "tobe": "TOBE",
        "new": "何が新しいか",
        "source": "出典",
        "followup": "続報",
        "japan": "日本市場",
        "runners": "次点",
        "empty": "本日は配信基準を満たすニュースがありませんでした。",
        "period": "対象期間",
    },
    "en": {
        "asis": "ASIS",
        "tobe": "TOBE",
        "new": "Why it matters",
        "source": "Source",
        "followup": "Follow-up",
        "japan": "Japan",
        "runners": "Also considered",
        "empty": "No stories met the bar today.",
        "period": "Window",
    },
}


def _block(label, text, color):
    if not text:
        return ""
    return (
        f'<p style="margin:0 0 12px;line-height:1.75;color:{FG};font-size:15px;">'
        f'<span style="color:{color};font-weight:700;font-size:12px;letter-spacing:.08em;">'
        f"{label}</span><br>{escape(text)}</p>"
    )


def _item_html(idx, item, lang):
    L = LABELS[lang]
    body = item.get(lang, {})
    tag = ""
    if item.get("is_followup"):
        tag = (
            f'<span style="display:inline-block;background:#fef3c7;color:{LABEL};'
            f'font-size:11px;font-weight:700;padding:2px 8px;border-radius:10px;'
            f'margin-right:8px;vertical-align:middle;">{L["followup"]}</span>'
        )

    links = [(item.get("source_name") or "source", item.get("source_url"))]
    for u in item.get("extra_urls") or []:
        if u:
            links.append((u.split("/")[2] if "//" in u else u, u))
    link_html = " &nbsp;/&nbsp; ".join(
        f'<a href="{escape(u)}" style="color:{ACCENT};text-decoration:none;">{escape(n)}</a>'
        for n, u in links
        if u
    )

    published = item.get("published") or ""
    meta = f'<span style="color:{MUTED};font-size:12px;">{escape(published)}</span>' if published else ""

    return f"""
<div style="margin:0 0 36px;">
  <h2 style="margin:0 0 4px;font-size:19px;line-height:1.45;color:{FG};font-weight:700;">
    <span style="color:{MUTED};">{idx}.</span> {tag}{escape(body.get('headline', ''))}
  </h2>
  <div style="margin:0 0 14px;">{meta}</div>
  {_block(L['asis'], body.get('asis'), MUTED)}
  {_block(L['tobe'], body.get('tobe'), MUTED)}
  {_block(L['new'], body.get('whats_new'), LABEL)}
  <p style="margin:0;font-size:13px;color:{MUTED};">{L['source']}: {link_html}</p>
</div>"""


def _section_html(data, lang):
    L = LABELS[lang]
    items = data.get("items") or []
    if items:
        parts = [_item_html(i + 1, it, lang) for i, it in enumerate(items)]
    else:
        parts = [f'<p style="color:{MUTED};font-size:15px;">{L["empty"]}</p>']

    note = data.get(f"japan_note_{lang}") or ""
    if note:
        parts.append(
            f'<div style="margin:0 0 28px;padding:14px 16px;background:#f7f8fa;'
            f'border-radius:8px;">'
            f'<div style="font-size:12px;font-weight:700;letter-spacing:.08em;'
            f'color:{MUTED};margin-bottom:6px;">{L["japan"]}</div>'
            f'<div style="font-size:14px;line-height:1.7;color:{FG};">{escape(note)}</div>'
            f"</div>"
        )

    runners = data.get("runners_up") or []
    if runners:
        rows = "".join(
            f'<li style="margin:0 0 6px;line-height:1.6;">'
            f'<a href="{escape(r.get("url", ""))}" style="color:{MUTED};">'
            f'{escape(r.get("title", ""))}</a></li>'
            for r in runners
            if r.get("url")
        )
        parts.append(
            f'<div style="margin:28px 0 0;padding-top:16px;border-top:1px solid {RULE};">'
            f'<div style="font-size:12px;font-weight:700;letter-spacing:.08em;'
            f'color:{MUTED};margin-bottom:8px;">{L["runners"]}</div>'
            f'<ul style="margin:0;padding-left:18px;font-size:13px;color:{MUTED};">'
            f"{rows}</ul></div>"
        )

    return "\n".join(parts)


def to_html(data):
    date = data.get("date", "")
    wd = data.get("weekday_ja", "")
    title_ja = f"AdTech Daily — {date}" + (f"({wd})" if wd else "")

    return f"""<div style="margin:0;padding:0;background:#ffffff;">
<div style="max-width:660px;margin:0 auto;padding:28px 22px 48px;
     font-family:-apple-system,BlinkMacSystemFont,'Hiragino Sans','Noto Sans JP',
     'Segoe UI',Helvetica,Arial,sans-serif;background:#ffffff;">

  <div style="padding-bottom:18px;border-bottom:2px solid {FG};margin-bottom:32px;">
    <div style="font-size:22px;font-weight:800;color:{FG};letter-spacing:-.01em;">
      {escape(title_ja)}</div>
  </div>

  {_section_html(data, 'ja')}

  <div style="margin:44px 0 32px;padding-top:24px;border-top:2px solid {FG};">
    <div style="font-size:13px;font-weight:800;letter-spacing:.12em;color:{MUTED};">
      ENGLISH</div>
  </div>

  {_section_html(data, 'en')}

  <div style="margin-top:44px;padding-top:16px;border-top:1px solid {RULE};
       font-size:11px;color:{MUTED};line-height:1.6;">
    Generated by adtech-news. Sources: Digiday / AdExchanger / IAB Tech Lab and others.
  </div>
</div>
</div>"""


def _item_text(idx, item, lang):
    L = LABELS[lang]
    b = item.get(lang, {})
    head = f"{idx}. {b.get('headline', '')}"
    if item.get("is_followup"):
        head = f"{idx}. [{L['followup']}] {b.get('headline', '')}"
    lines = [head, "-" * 60]
    if item.get("published"):
        lines.append(item["published"])
        lines.append("")
    for key, label in (("asis", L["asis"]), ("tobe", L["tobe"]), ("whats_new", L["new"])):
        if b.get(key):
            lines.append(f"[{label}] {b[key]}")
            lines.append("")
    urls = [item.get("source_url")] + list(item.get("extra_urls") or [])
    lines.append(f"{L['source']}: " + " / ".join(u for u in urls if u))
    return "\n".join(lines)


def _section_text(data, lang):
    L = LABELS[lang]
    items = data.get("items") or []
    out = [_item_text(i + 1, it, lang) for i, it in enumerate(items)] or [L["empty"]]
    note = data.get(f"japan_note_{lang}") or ""
    if note:
        out.append(f"[{L['japan']}] {note}")
    runners = data.get("runners_up") or []
    if runners:
        out.append(
            f"[{L['runners']}]\n"
            + "\n".join(f"  - {r.get('title','')} {r.get('url','')}" for r in runners)
        )
    return "\n\n\n".join(out)


def to_text(data):
    date = data.get("date", "")
    wd = data.get("weekday_ja", "")
    header = f"AdTech Daily — {date}" + (f"({wd})" if wd else "")
    return (
        f"{header}\n{'=' * 60}\n\n"
        + _section_text(data, "ja")
        + f"\n\n\n{'=' * 60}\nENGLISH\n{'=' * 60}\n\n"
        + _section_text(data, "en")
        + "\n"
    )


def subject(data):
    date = data.get("date", "")
    wd = data.get("weekday_ja", "")
    items = data.get("items") or []
    base = f"AdTech Daily {date}" + (f"({wd})" if wd else "")
    if items:
        return f"{base} — {items[0].get('ja', {}).get('headline', '')}"
    return f"{base} — 該当ニュースなし"


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: render.py <digest.json>")
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    stem = os.path.splitext(path)[0]
    with open(stem + ".html", "w", encoding="utf-8") as f:
        f.write(to_html(data))
    with open(stem + ".txt", "w", encoding="utf-8") as f:
        f.write(to_text(data))
    print(stem + ".html")


if __name__ == "__main__":
    main()
