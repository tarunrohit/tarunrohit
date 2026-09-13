#!/usr/bin/env python3
"""
generate_heatmap.py
Builds a custom-colored ("jet" colormap: blue -> cyan -> green -> yellow ->
red, instead of GitHub's default green) contribution heatmap SVG for a
GitHub user, using the official GitHub GraphQL API.

Requires:
    GH_TOKEN   - a GitHub Personal Access Token with the `read:user` scope
                 (classic PAT). Needed because contributionsCollection is
                 not exposed to the default GITHUB_TOKEN Actions provides.
    GH_LOGIN   - the GitHub username to fetch contributions for.

Usage (local test):
    GH_TOKEN=ghp_xxx GH_LOGIN=tarunrohit python3 scripts/generate_heatmap.py
"""
import json
import os
import sys
import urllib.request

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

# Blue -> cyan -> green -> yellow -> red, echoing the classic "jet" colormap.
JET_STOPS = [
    (0.00, (15, 23, 42)),     # empty day: near-background slate
    (0.01, (30, 58, 138)),    # any activity at all: deep blue
    (0.25, (8, 145, 178)),    # cyan
    (0.50, (5, 150, 105)),    # green
    (0.75, (234, 179, 8)),    # yellow
    (1.00, (220, 38, 38)),    # red: busiest days
]


def lerp(a, b, t):
    return a + (b - a) * t


def jet_color(t):
    """t in [0,1] -> '#rrggbb' interpolated across JET_STOPS."""
    t = max(0.0, min(1.0, t))
    for (t0, c0), (t1, c1) in zip(JET_STOPS, JET_STOPS[1:]):
        if t0 <= t <= t1:
            span = (t1 - t0) or 1
            local_t = (t - t0) / span
            r = round(lerp(c0[0], c1[0], local_t))
            g = round(lerp(c0[1], c1[1], local_t))
            b = round(lerp(c0[2], c1[2], local_t))
            return f"#{r:02x}{g:02x}{b:02x}"
    return "#0f172a"


def fetch_contributions(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "jet-heatmap-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")
    calendar = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return calendar["weeks"], calendar["totalContributions"]


def render_svg(weeks, total, cell=11, gap=3, theme="dark"):
    n_weeks = len(weeks)
    n_days = 7
    width = n_weeks * (cell + gap) + gap + 20
    height = n_days * (cell + gap) + gap + 34

    bg = "#0b0f17" if theme == "dark" else "#ffffff"
    text_col = "#94a3b8" if theme == "dark" else "#475569"

    max_count = max(
        (day["contributionCount"] for week in weeks for day in week["contributionDays"]),
        default=0,
    ) or 1

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, Menlo, Consolas, monospace">',
        f'<rect width="{width}" height="{height}" rx="8" fill="{bg}"/>',
        f'<text x="10" y="18" fill="{text_col}" font-size="12">'
        f'{total} contributions in the last year - jet colormap</text>',
    ]

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            count = day["contributionCount"]
            t = 0.0 if count == 0 else min(1.0, count / max_count)
            color = jet_color(t if count > 0 else 0.0)
            x = 10 + wi * (cell + gap)
            y = 28 + di * (cell + gap)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                f'fill="{color}"><title>{day["date"]}: {count} contribution(s)</title></rect>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    token = os.environ.get("GH_TOKEN")
    login = os.environ.get("GH_LOGIN")
    if not token or not login:
        print("GH_TOKEN and GH_LOGIN environment variables are required.", file=sys.stderr)
        sys.exit(1)

    weeks, total = fetch_contributions(login, token)

    os.makedirs("dist", exist_ok=True)
    with open("dist/github-jet-dark.svg", "w") as f:
        f.write(render_svg(weeks, total, theme="dark"))
    with open("dist/github-jet-light.svg", "w") as f:
        f.write(render_svg(weeks, total, theme="light"))

    print(f"Wrote dist/github-jet-dark.svg and dist/github-jet-light.svg "
          f"({total} total contributions)")


if __name__ == "__main__":
    main()
