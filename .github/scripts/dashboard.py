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
    createdAt
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

ISSUES_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title url state createdAt closedAt
        labels(first: 20) { nodes { name } }
        blockedBy(first: 50) { nodes { state } }
      }
    }
  }
}
"""


def gh(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out)


def graphql(query, **variables):
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is not None:
            args += ["-f", f"{key}={value}"]
    return gh(*args)["data"]["repository"]


def all_issues(owner, name):
    issues, after = [], None
    while True:
        page = graphql(ISSUES_QUERY, owner=owner, name=name, after=after)["issues"]
        issues += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            return issues
        after = page["pageInfo"]["endCursor"]


def parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def building_products():
    """building の issue と、その本文の「実装リポジトリ」に書かれたリポジトリを返す。"""
    issues = gh("issue", "list", "-R", HUB, "--label", "building", "--state", "open", "--limit", "200",
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


def ci_chip(pr):
    commits = pr["commits"]["nodes"]
    rollup = commits[0]["commit"]["statusCheckRollup"] if commits else None
    state = rollup["state"] if rollup else None
    if state == "SUCCESS":
        return chip("good", "✓", "CI 通過")
    if state in ("FAILURE", "ERROR"):
        return chip("critical", "✕", "CI 失敗")
    if state in ("PENDING", "EXPECTED"):
        return chip("neutral", "…", "CI 実行中")
    return chip("neutral", "–", "CI なし")


def chip(kind, icon, text):
    return f'<span class="chip {kind}"><b aria-hidden="true">{icon}</b>{html.escape(text)}</span>'


def labels(node):
    return [label["name"] for label in node["labels"]["nodes"]]


def link(node):
    return f'<a href="{html.escape(node["url"])}">#{node["number"]}</a> {html.escape(node["title"])}'


def item_list(items, empty="なし"):
    if not items:
        return f'<p class="none">{empty}</p>'
    return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"


def tile(label, value, note="", kind=""):
    note_html = f'<span class="note">{html.escape(note)}</span>' if note else ""
    return (f'<div class="tile {kind}"><span class="label">{html.escape(label)}</span>'
            f'<span class="value">{value}</span>{note_html}</div>')


def burnup_series(issues, now):
    """日ごと（日本時間）の、全体の枚数と完了の枚数。最初の issue の日から今日まで。"""
    if not issues:
        return []
    created = [parse_time(i["createdAt"]).astimezone(JST).date() for i in issues]
    closed = [parse_time(i["closedAt"]).astimezone(JST).date() for i in issues if i["closedAt"] and i["state"] == "CLOSED"]
    day, today = min(created), now.astimezone(JST).date()
    series = []
    while day <= today:
        series.append({"date": day,
                       "total": sum(1 for d in created if d <= day),
                       "done": sum(1 for d in closed if d <= day)})
        day += timedelta(days=1)
    return series


def render_burnup(series, chart_id):
    """バーンアップチャート。横軸は最初の issue の日から、今日を含む週の日曜まで。"""
    if not series:
        return '<p class="none">issue がまだない</p>'
    start, today = series[0]["date"], series[-1]["date"]
    end = max(today + timedelta(days=6 - today.weekday()), start + timedelta(days=1))
    span = (end - start).days
    width, height, left, right, top, bottom = 400, 240, 30, 74, 14, 28
    plot_w, plot_h = width - left - right, height - top - bottom
    peak = max(point["total"] for point in series)
    step = next(s for s in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000) if peak / s <= 5)
    y_max = max(step, -(-peak // step) * step)

    def x(day):
        return left + plot_w * (day - start).days / span

    def y(value):
        return top + plot_h * (1 - value / y_max)

    parts = []
    for value in range(0, y_max + 1, step):
        cls = "axis" if value == 0 else "grid"
        parts.append(f'<line class="{cls}" x1="{left}" x2="{left + plot_w}" y1="{y(value):.1f}" y2="{y(value):.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 6}" y="{y(value) + 4:.1f}" text-anchor="end">{value}</text>')

    # 月曜（スプリントの始まり）に目盛りを打つ。期間が短い時は両端も足す
    ticks = [start + timedelta(days=n) for n in range(span + 1) if (start + timedelta(days=n)).weekday() == 0]
    if len(ticks) < 2:
        ticks = sorted(set(ticks + [start, end]))
    for day in ticks:
        parts.append(f'<line class="grid" x1="{x(day):.1f}" x2="{x(day):.1f}" y1="{top}" y2="{top + plot_h}"/>')
        parts.append(f'<text class="tick" x="{x(day):.1f}" y="{height - 8}" text-anchor="middle">{day.month}/{day.day}</text>')

    def path(key):
        return " ".join(f'{"M" if n == 0 else "L"}{x(p["date"]):.1f},{y(p[key]):.1f}' for n, p in enumerate(series))

    last = series[-1]
    end_x, total_y, done_y = x(last["date"]), y(last["total"]), y(last["done"])
    parts.append(f'<path class="line s2" d="{path("total")}"/>')
    parts.append(f'<path class="line s1" d="{path("done")}"/>')
    parts.append(f'<circle class="dot s2" cx="{end_x:.1f}" cy="{total_y:.1f}" r="4"/>')
    parts.append(f'<circle class="dot s1" cx="{end_x:.1f}" cy="{done_y:.1f}" r="4"/>')
    # 終点のラベル。2本が近い時は重なるので、1つにまとめる
    if done_y - total_y < 16:
        parts.append(f'<text class="end" x="{end_x + 9:.1f}" y="{total_y + 4:.1f}">完了 {last["done"]} / {last["total"]}</text>')
    else:
        parts.append(f'<text class="end" x="{end_x + 9:.1f}" y="{total_y + 4:.1f}">全体 {last["total"]}</text>')
        parts.append(f'<text class="end" x="{end_x + 9:.1f}" y="{done_y + 4:.1f}">完了 {last["done"]}</text>')
    parts.append('<line class="cross" y1="{}" y2="{}" hidden/>'.format(top, top + plot_h))
    parts.append('<circle class="dot s2 hover" r="4" hidden/><circle class="dot s1 hover" r="4" hidden/>')

    points = [{"label": f'{p["date"].month}/{p["date"].day}', "x": round(x(p["date"]), 1),
               "total": p["total"], "done": p["done"],
               "ty": round(y(p["total"]), 1), "dy": round(y(p["done"]), 1)} for p in series]
    rows = "".join(f'<tr><td>{p["label"]}</td><td>{p["total"]}</td><td>{p["done"]}</td></tr>' for p in reversed(points))
    return f"""<figure class="chart" id="{chart_id}" data-points='{json.dumps(points)}'>
<div class="legend"><span><i class="key s2"></i>全体（issue の枚数）</span><span><i class="key s1"></i>完了</span></div>
<div class="plot">
<svg viewBox="0 0 {width} {height}" role="img" aria-label="バーンアップチャート。全体 {last["total"]}枚のうち {last["done"]}枚が完了">
{"".join(parts)}
</svg>
<div class="tip" hidden></div>
</div>
<details><summary>表で見る</summary>
<table><thead><tr><th>日付</th><th>全体</th><th>完了</th></tr></thead><tbody>{rows}</tbody></table>
</details>
</figure>"""


def render_product(product, now, index):
    issue = product["issue"]
    head = f'<h2>{html.escape(issue["title"])}</h2>'
    hub_link = f'<a href="{html.escape(issue["url"])}">{html.escape(HUB)}#{issue["number"]}</a>'
    if not product["repo"]:
        return f'<section>{head}<p class="meta">{hub_link}</p><p class="warn">実装リポジトリが issue に書かれていない</p></section>'

    owner, name = product["repo"]
    repo_link = f'<a href="https://github.com/{owner}/{name}">{owner}/{name}</a>'
    # 1つのリポジトリが読めなくても、ほかの製品と在庫は出す
    try:
        repo = graphql(REPO_QUERY, owner=owner, name=name)
        issues = all_issues(owner, name) if repo else []
    except (subprocess.CalledProcessError, KeyError, TypeError, ValueError) as error:
        print(f"{owner}/{name} を読めなかった: {getattr(error, 'stderr', None) or error}", file=sys.stderr)
        repo = None
    if not repo:
        return f'<section>{head}<p class="meta">{hub_link} / {repo_link}</p><p class="warn">実装リポジトリを読めなかった</p></section>'

    since = now - timedelta(hours=24)
    open_issues = [i for i in issues if i["state"] == "OPEN"]
    closed = [i for i in issues if i["state"] == "CLOSED" and i["closedAt"]]
    open_prs = repo["openPRs"]["nodes"]
    merged = [p for p in repo["mergedPRs"]["nodes"] if p["mergedAt"]]

    waiting = [link(n) for n in open_prs + open_issues if WAITING_LABEL in labels(n)]

    pr_items, unanswered_total = [], 0
    for pr in open_prs:
        unanswered = unanswered_threads(pr)
        unanswered_total += unanswered
        chips = [chip("neutral", "→", pr["baseRefName"]), ci_chip(pr)]
        if pr["isDraft"]:
            chips.append(chip("neutral", "–", "下書き"))
        chips.append(chip("warning", "!", f"未返信の指摘 {unanswered}件") if unanswered
                     else chip("good", "✓", "未返信の指摘なし"))
        pr_items.append(f'{link(pr)}<div class="chips">{"".join(chips)}</div>')

    done, remaining = len(closed), len(open_issues)
    total = done + remaining
    percent = done * 100 // total if total else 0
    merged_recent = [link(p) for p in merged if parse_time(p["mergedAt"]) >= since]
    closed_recent = [link(i) for i in closed if parse_time(i["closedAt"]) >= since]

    times = [parse_time(p["mergedAt"]) for p in merged] + [parse_time(i["closedAt"]) for i in closed]
    if times:
        days = (now - max(times)).days
        last = f'最後のマージか close: {max(times).astimezone(JST):%m/%d %H:%M}（{days}日前）'
    else:
        created = parse_time(repo["createdAt"])
        days = (now - created).days
        last = f'マージも close もまだない（リポジトリの作成: {created.astimezone(JST):%m/%d %H:%M}、{days}日前）'
    stale = days >= STALE_DAYS
    stale_note = (f'<p>{chip("warning", "!", f"停滞（{STALE_DAYS}日以上、マージも close もない）")}</p>' if stale
                  else f'<p>{chip("good", "✓", "停滞なし")}</p>')

    with_pr = {i["number"] for pr in open_prs for i in pr["closingIssuesReferences"]["nodes"]}
    startable = [link(i) for i in open_issues
                 if all(b["state"] == "CLOSED" for b in i["blockedBy"]["nodes"]) and i["number"] not in with_pr]

    tiles = "".join([
        tile("あなた待ち", len(waiting), f"{WAITING_LABEL} のラベル", "attn" if waiting else ""),
        tile("完了", f'{done}<small> / {total}</small>', f"{percent}%、残り {remaining}件"),
        tile("open の PR", len(open_prs), f"未返信の指摘 {unanswered_total}件", "attn" if unanswered_total else ""),
        tile("直近24時間", f'{len(merged_recent)}<small> マージ</small>', f"close {len(closed_recent)}件"),
    ])

    return f"""<section>
{head}
<p class="meta">{hub_link} / {repo_link}</p>
<div class="tiles">{tiles}</div>
<div class="card"><h3>あなた待ち</h3>
{item_list(waiting, f"なし（{WAITING_LABEL} のラベルが付いた issue と PR が出る）")}</div>
<div class="card"><h3>バーンアップ</h3>
<p class="meta">issue の枚数で数える。縦の線は月曜（スプリントの始まり）</p>
{render_burnup(burnup_series(issues, now), f"burnup-{index}")}</div>
<div class="card"><h3>open の PR</h3>
{item_list(pr_items)}</div>
<div class="card"><h3>直近24時間に終わったもの</h3>
<h4>マージされた PR</h4>
{item_list(merged_recent)}
<h4>close された issue</h4>
{item_list(closed_recent)}</div>
<div class="card"><h3>詰まり</h3>
<p>{last}</p>
{stale_note}
<h4>着手できる issue（ブロックなし、PR なし）</h4>
{item_list(startable)}</div>
</section>"""


def render_stock():
    issues = gh("issue", "list", "-R", HUB, "--state", "open", "--limit", "200",
                "--json", "number,title,url,labels")
    tiles, parts = [], []
    for name in STOCK_LABELS:
        matched = [i for i in issues if name in [label["name"] for label in i["labels"]]]
        tiles.append(tile(name, len(matched)))
        if matched:
            parts.append(f"<h4>{name}</h4>" + item_list([link(i) for i in matched]))
    detail = f'<div class="card">{"".join(parts)}</div>' if parts else ""
    return f'<section><h2>アイデアの在庫</h2><div class="tiles three">{"".join(tiles)}</div>{detail}</section>'


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>workbench ダッシュボード</title>
<style>
:root {
  color-scheme: light;
  --plane: #f9f9f7; --surface: #fcfcfb; --ink: #0b0b0b; --ink2: #52514e; --muted: #898781;
  --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,.10);
  --s1: #2a78d6; --s2: #eb6834;
  --good: #0ca30c; --warning: #fab219; --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --plane: #0d0d0d; --surface: #1a1a19; --ink: #fff; --ink2: #c3c2b7; --muted: #898781;
    --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,.10);
    --s1: #3987e5; --s2: #d95926;
  }
}
* { box-sizing: border-box; }
body { margin: 0 auto; padding: 16px; max-width: 720px; background: var(--plane); color: var(--ink);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", "Hiragino Sans", sans-serif; }
h1 { font-size: 1.3rem; margin: 0; }
h2 { font-size: 1.15rem; margin: 0 0 2px; }
h3 { font-size: 1rem; margin: 0 0 6px; }
h4 { font-size: .85rem; margin: 12px 0 2px; color: var(--ink2); font-weight: 600; }
section { margin-top: 28px; }
p { margin: 4px 0; }
ul { margin: 4px 0; padding-left: 20px; }
li { margin: 8px 0; overflow-wrap: anywhere; }
a { color: inherit; }
small { font-size: .55em; font-weight: 400; color: var(--ink2); }
.meta, .none { color: var(--ink2); font-size: .85rem; }
.warn { font-weight: 600; }
.card, .tile { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
.card { padding: 14px 16px; margin-top: 12px; }
.tiles { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 12px; }
.tiles.three { grid-template-columns: repeat(3, 1fr); }
@media (min-width: 600px) { .tiles { grid-template-columns: repeat(4, 1fr); } }
.tile { padding: 10px 12px; display: flex; flex-direction: column; min-width: 0; }
.tile .label, .tile .note { font-size: .8rem; color: var(--ink2); }
.tile .value { font-size: 1.9rem; font-weight: 600; line-height: 1.25; }
.tile.attn { border-color: var(--warning); box-shadow: inset 4px 0 0 var(--warning); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }
.chip { display: inline-flex; align-items: center; gap: 4px; padding: 1px 8px; border-radius: 999px;
  border: 1px solid var(--border); font-size: .8rem; color: var(--ink2); overflow-wrap: anywhere; }
.chip b { font-weight: 700; color: var(--muted); }
.chip.good b { color: var(--good); }
.chip.warning b { color: var(--warning); }
.chip.critical b { color: var(--critical); }
.chip.warning, .chip.critical { color: var(--ink); font-weight: 600; }
.chart { margin: 8px 0 0; max-width: 520px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: .8rem; color: var(--ink2); }
.key { display: inline-block; width: 14px; height: 2px; border-radius: 1px; vertical-align: middle; margin-right: 6px; }
.key.s1, .tip .s1 { background: var(--s1); }
.key.s2, .tip .s2 { background: var(--s2); }
.plot { position: relative; }
svg { display: block; width: 100%; height: auto; touch-action: pan-y; }
svg [hidden] { display: none; }
.grid { stroke: var(--grid); stroke-width: 1; }
.axis { stroke: var(--axis); stroke-width: 1; }
.tick { fill: var(--muted); font-size: 11px; font-variant-numeric: tabular-nums; }
.end { fill: var(--ink); font-size: 12px; font-weight: 600; }
.line { fill: none; stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.line.s1 { stroke: var(--s1); }
.line.s2 { stroke: var(--s2); }
.dot { stroke: var(--surface); stroke-width: 2; }
.dot.s1 { fill: var(--s1); }
.dot.s2 { fill: var(--s2); }
.cross { stroke: var(--axis); stroke-width: 1; }
.tip { position: absolute; top: 0; padding: 6px 10px; border-radius: 8px; background: var(--surface);
  border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,.15); font-size: .8rem; pointer-events: none; white-space: nowrap; }
.tip div { display: flex; align-items: center; gap: 6px; }
.tip i { display: inline-block; width: 12px; height: 2px; border-radius: 1px; }
.tip strong { margin-left: auto; padding-left: 12px; }
.tip .day { color: var(--ink2); }
details { margin-top: 6px; font-size: .85rem; color: var(--ink2); }
table { border-collapse: collapse; margin-top: 6px; font-variant-numeric: tabular-nums; }
th, td { padding: 2px 14px 2px 0; text-align: right; font-weight: 400; }
th { color: var(--muted); }
th:first-child, td:first-child { text-align: left; }
</style>
</head>
<body>
<h1>workbench ダッシュボード</h1>
<p class="meta">更新: __UPDATED__（日本時間）</p>
__BODY__
<script>
// バーンアップの上をなぞると、いちばん近い日の値を出す
for (const chart of document.querySelectorAll('.chart')) {
  const points = JSON.parse(chart.dataset.points);
  const svg = chart.querySelector('svg'), tip = chart.querySelector('.tip');
  const cross = chart.querySelector('.cross');
  const [dotTotal, dotDone] = chart.querySelectorAll('.dot.hover');
  const row = (cls, name, value) => {
    const div = document.createElement('div'), key = document.createElement('i'), strong = document.createElement('strong');
    key.className = cls; strong.textContent = value;
    div.append(key, name, strong);
    return div;
  };
  const show = (event) => {
    const box = svg.getBoundingClientRect(), scale = svg.viewBox.baseVal.width / box.width;
    const x = (event.clientX - box.left) * scale;
    const p = points.reduce((a, b) => Math.abs(b.x - x) < Math.abs(a.x - x) ? b : a);
    cross.setAttribute('x1', p.x); cross.setAttribute('x2', p.x);
    dotTotal.setAttribute('cx', p.x); dotTotal.setAttribute('cy', p.ty);
    dotDone.setAttribute('cx', p.x); dotDone.setAttribute('cy', p.dy);
    for (const el of [cross, dotTotal, dotDone, tip]) el.removeAttribute('hidden');
    const day = document.createElement('div');
    day.className = 'day'; day.textContent = p.label;
    tip.replaceChildren(day, row('s2', '全体', p.total), row('s1', '完了', p.done));
    const left = p.x / scale + 12;
    tip.style.left = (left + tip.offsetWidth > box.width ? p.x / scale - tip.offsetWidth - 12 : left) + 'px';
  };
  const hide = () => { for (const el of [cross, dotTotal, dotDone, tip]) el.setAttribute('hidden', ''); };
  svg.addEventListener('pointermove', show);
  svg.addEventListener('pointerdown', show);
  svg.addEventListener('pointerleave', hide);
}
</script>
</body>
</html>
"""


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "_site"
    now = datetime.now(timezone.utc)
    products = building_products()
    sections = [render_product(p, now, n) for n, p in enumerate(products)]
    if not sections:
        sections.append('<section><p class="none">building の issue はない</p></section>')
    sections.append(render_stock())
    page = PAGE.replace("__UPDATED__", f"{now.astimezone(JST):%Y-%m-%d %H:%M}").replace("__BODY__", "\n".join(sections))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    main()
