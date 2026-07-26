#!/usr/bin/env python3
"""ダイジェスト JSON をメール送信し、配信済み状態を更新する。

usage: send.py <digest.json> --to a@b.com --sender x@gmail.com \
                [--sender-name NAME] [--keychain-service SERVICE] [--dry-run]

SMTP パスワードは macOS Keychain から取得する:
  security add-generic-password -a <sender> -s <service> -w <app-password>
"""
import argparse
import json
import os
import smtplib
import ssl
import subprocess
import sys
from datetime import date, datetime, timedelta
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render  # noqa: E402

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
STATE_RETENTION_DAYS = 120


def keychain_password(service, account):
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        sys.exit(
            f"Keychain にパスワードがありません (service={service}, account={account})。\n"
            f"  security add-generic-password -a {account} -s {service} -w '<app-password>'\n"
            "を実行してください。"
        )
    pw = out.stdout.strip()
    if not pw:
        sys.exit(f"Keychain のエントリが空です (service={service})")
    return pw


def build_message(data, sender, sender_name, recipient):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(render.subject(data), "utf-8")
    msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender))
    msg["To"] = recipient
    msg["Date"] = formatdate(localtime=True)
    msg.attach(MIMEText(render.to_text(data), "plain", "utf-8"))
    msg.attach(MIMEText(render.to_html(data), "html", "utf-8"))
    return msg


def update_state(state_path, data):
    if os.path.exists(state_path):
        with open(state_path, encoding="utf-8") as f:
            state = json.load(f)
    else:
        state = {"entries": []}

    seen_keys = {e.get("topic_key") for e in state["entries"]}
    seen_urls = {e.get("url") for e in state["entries"]}

    for item in data.get("items") or []:
        key, url = item.get("topic_key"), item.get("source_url")
        if key in seen_keys and url in seen_urls:
            continue
        state["entries"].append(
            {
                "date": data.get("date"),
                "topic_key": key,
                "url": url,
                "headline_ja": item.get("ja", {}).get("headline", ""),
                "is_followup": bool(item.get("is_followup")),
            }
        )

    cutoff = (date.today() - timedelta(days=STATE_RETENTION_DAYS)).isoformat()
    state["entries"] = [e for e in state["entries"] if (e.get("date") or "") >= cutoff]
    state["updated_at"] = datetime.now().isoformat(timespec="seconds")

    tmp = state_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, state_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("digest")
    ap.add_argument("--to", required=True)
    ap.add_argument("--sender", required=True)
    ap.add_argument("--sender-name", default="AdTech Daily")
    ap.add_argument("--keychain-service", default="adtech-news-smtp")
    ap.add_argument("--state", default=None)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.digest, encoding="utf-8") as f:
        data = json.load(f)

    msg = build_message(data, args.sender, args.sender_name, args.to)

    if args.dry_run:
        print(f"[dry-run] subject: {render.subject(data)}")
        print(f"[dry-run] to: {args.to}  items: {len(data.get('items') or [])}")
        return

    pw = keychain_password(args.keychain_service, args.sender)
    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=60) as s:
        s.login(args.sender, pw)
        s.sendmail(args.sender, [args.to], msg.as_string())
    print(f"sent: {args.to} ({len(data.get('items') or [])} items)")

    state_path = args.state or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(args.digest))), "state", "seen.json"
    )
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    update_state(state_path, data)
    print(f"state updated: {state_path}")


if __name__ == "__main__":
    main()
