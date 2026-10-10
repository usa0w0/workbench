#!/usr/bin/env python3
"""building の issue が指す実装リポジトリの状況を集め、1枚の HTML にする。

使い方: GH_TOKEN を設定して `python3 dashboard.py <出力先ディレクトリ>`
GitHub の読み出しは gh CLI で行う。
"""

import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone

HUB = os.environ.get("GITHUB_REPOSITORY", "usa0w0/workbench")
JST = timezone(timedelta(hours=9))
WAITING_LABEL = "ユーザー待ち"
STALE_DAYS = 3
STOCK_LABELS = ["idea", "spec", "ready"]

REPO_QUERY = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    openIssues: issues(states: OPEN, first: 100, orderBy: {field: CREATED_AT, direction: ASC}) {
      totalCount
      nodes {
        number title url
        labels(first: 20) { nodes { name } }
        blockedBy(first: 50) { nodes { state } }
      }
    }
    closedIssues: issues(states: CLOSED, first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
      totalCount
      nodes { number title url closedAt }
    }
    openPRs: pullRequests(states: OPEN, first: 50, orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        number title url baseRefName isDraft
        author { login }
        labels(first: 20) { nodes { name } }
        closingIssuesReferences(first: 20) { nodes { number } }
        reviewThreads(first: 100) {
          nodes { isResolved comments(last: 1) { nodes { author { login } } } }
        }
        commits(last: 1) { nodes { commit { statusCheckRollup { state } } } }
      }
    }
    mergedPRs: pullRequests(states: MERGED, first: 50, orderBy: {field: UPDATED_AT, direction: DESC}) {
      nodes { number title url mergedAt }
    }
  }
}
"""


def gh(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def building_products():
    """building の issue と、その本文の「実装リポジトリ」に書かれたリポジトリを返す。"""
    issues = gh("issue", "list", "-R", HUB, "--label", "building", "--state", "open",
                "--json", "number,title,url,body")
    products = []
    for issue in sorted(issues, key=lambda i: i["number"]):
        section = issue["body"].split("## 実装リポジトリ")[-1]
        match = re.search(r"https://github\.com/([\w.-]+)/([\w.-]+)", section)
        products.append({"issue": issue, "repo": match.groups() if match else None})
    return products


def unanswered_threads(pr):
    """未解決で、最後のコメントが PR の作者以外のスレッドの数。"""
    author = (pr["author"] or {}).get("login")
    count = 0
    for thread in pr["reviewThreads"]["nodes"]:
        last = thread["comments"]["nodes"]
        last_author = (last[0]["author"] or {}).get("login") if last else None
        if not thread["isResolved"] and last_author != author:
            count += 1
    return count


def ci_state(pr):
    commits = pr["commits"]["nodes"]
    rollup = commits[0]["commit"]["statusCheckRollup"] if commits else None
    return {"SUCCESS": "CI 通過", "FAILURE": "CI 失敗", "ERROR": "CI 失敗",
            "PENDING": "CI 実行中", "EXPECTED": "CI 実行中"}.get(rollup["state"] if rollup else None, "CI なし")


def labels(node):
    return [label["name"] for label in node["labels"]["nodes"]]


def link(node):
    return f'<a href="{html.escape(node["url"])}">#{node["number"]}</a> {html.escape(node["title"])}'


def item_list(items, empty="なし"):
    if not items:
        return f'<p class="none">{empty}</p>'
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def render_product(product, now):
    issue = product["issue"]
    head = f'<h2>{html.escape(issue["title"])}</h2>'
    hub_link = f'<a href="{html.escape(issue["url"])}">{html.escape(HUB)}#{issue["number"]}</a>'
    if not product["repo"]:
        return f'<section>{head}<p class="meta">{hub_link}</p><p class="none">実装リポジトリが issue に書かれていない</p></section>'

    owner, name = product["repo"]
    repo = gh("api", "graphql", "-f", f"query={REPO_QUERY}", "-f", f"owner={owner}", "-f", f"name={name}")["data"]["repository"]
    since = now - timedelta(hours=24)

    open_issues = repo["openIssues"]["nodes"]
    open_prs = repo["openPRs"]["nodes"]
    closed = [i for i in repo["closedIssues"]["nodes"] if i["closedAt"]]
    merged = [p for p in repo["mergedPRs"]["nodes"] if p["mergedAt"]]

    waiting = [link(n) for n in open_prs + open_issues if WAITING_LABEL in labels(n)]

    pr_items = []
    for pr in open_prs:
        notes = [f'{html.escape(pr["baseRefName"])} 向け', ci_state(pr)]
        if pr["isDraft"]:
            notes.append("下書き")
        unanswered = unanswered_threads(pr)
        notes.append(f"未返信の指摘 {unanswered}件")
        cls = ' class="warn"' if unanswered or "失敗" in notes[1] else ""
        pr_items.append(f'{link(pr)}<br><span{cls}>{" / ".join(notes)}</span>')

    done, remaining = repo["closedIssues"]["totalCount"], repo["openIssues"]["totalCount"]
    total = done + remaining
    percent = round(done * 100 / total) if total else 0
    merged_recent = [link(p) for p in merged if parse_time(p["mergedAt"]) >= since]
    closed_recent = [link(i) for i in closed if parse_time(i["closedAt"]) >= since]

    times = [parse_time(p["mergedAt"]) for p in merged] + [parse_time(i["closedAt"]) for i in closed]
    if times:
        days = (now - max(times)).days
        last = f'最後のマージか close: {max(times).astimezone(JST):%m/%d %H:%M}（{days}日前）'
        stale = days >= STALE_DAYS
    else:
        last, stale = "マージも close もまだない", False
    stale_note = f'<p class="warn">停滞（{STALE_DAYS}日以上、マージも close もない）</p>' if stale else '<p>停滞なし</p>'

    with_pr = {i["number"] for pr in open_prs for i in pr["closingIssuesReferences"]["nodes"]}
    startable = [link(i) for i in open_issues
                 if all(b["state"] == "CLOSED" for b in i["blockedBy"]["nodes"]) and i["number"] not in with_pr]

    return f"""<section>
{head}
<p class="meta">{hub_link} / <a href="https://github.com/{owner}/{name}">{owner}/{name}</a></p>
<h3>あなた待ち（{WAITING_LABEL} のラベル）</h3>
{item_list(waiting)}
<h3>open の PR</h3>
{item_list(pr_items)}
<h3>進み具合</h3>
<p>issue {done} / {total} 完了（残り {remaining}件、{percent}%）</p>
<div class="bar"><div style="width:{percent}%"></div></div>
<h4>直近24時間にマージされた PR</h4>
{item_list(merged_recent)}
<h4>直近24時間に close された issue</h4>
{item_list(closed_recent)}
<h3>詰まり</h3>
<p>{last}</p>
{stale_note}
<h4>着手できる issue（ブロックなし、PR なし）</h4>
{item_list(startable)}
</section>"""


def render_stock():
    issues = gh("issue", "list", "-R", HUB, "--state", "open", "--limit", "200",
                "--json", "number,title,url,labels")
    parts = []
    for name in STOCK_LABELS:
        matched = [i for i in issues if name in [label["name"] for label in i["labels"]]]
        parts.append(f"<h4>{name}（{len(matched)}件）</h4>" + item_list([link(i) for i in matched]))
    return "<section><h2>アイデアの在庫</h2>" + "".join(parts) + "</section>"


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>workbench ダッシュボード</title>
<style>
:root {{ --bg: #fff; --fg: #1f2328; --sub: #59636e; --line: #d1d9e0; --warn: #9a6700; --bar: #1a7f37; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg: #0d1117; --fg: #f0f6fc; --sub: #9198a1; --line: #3d444d; --warn: #d29922; --bar: #3fb950; }}
}}
body {{ margin: 0 auto; padding: 16px; max-width: 720px; background: var(--bg); color: var(--fg);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Hiragino Sans", sans-serif; }}
h1 {{ font-size: 1.3rem; margin: 0; }}
h2 {{ font-size: 1.15rem; margin: 0 0 4px; }}
h3 {{ font-size: 1rem; margin: 20px 0 4px; border-bottom: 1px solid var(--line); }}
h4 {{ font-size: .9rem; margin: 12px 0 2px; color: var(--sub); }}
section {{ margin-top: 24px; padding-top: 16px; border-top: 2px solid var(--line); }}
p {{ margin: 4px 0; }}
ul {{ margin: 4px 0; padding-left: 20px; }}
li {{ margin: 6px 0; overflow-wrap: anywhere; }}
a {{ color: inherit; }}
.meta, .none, li span {{ color: var(--sub); font-size: .9rem; }}
.warn, li span.warn {{ color: var(--warn); font-weight: 600; }}
.bar {{ height: 8px; background: var(--line); border-radius: 4px; overflow: hidden; }}
.bar div {{ height: 100%; background: var(--bar); }}
</style>
</head>
<body>
<h1>workbench ダッシュボード</h1>
<p class="meta">更新: {updated}（日本時間）</p>
{body}
</body>
</html>
"""


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "_site"
    now = datetime.now(timezone.utc)
    products = building_products()
    sections = [render_product(p, now) for p in products]
    if not sections:
        sections.append('<section><p class="none">building の issue はない</p></section>')
    sections.append(render_stock())
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(PAGE.format(updated=f"{now.astimezone(JST):%Y-%m-%d %H:%M}", body="\n".join(sections)))


if __name__ == "__main__":
    main()
