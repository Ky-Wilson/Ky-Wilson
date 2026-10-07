"""Génère metrics/languages.svg : langages utilisés sur tous les dépôts (privés inclus).

Compte, pour chaque langage, le nombre de dépôts où il représente au moins 10 % du code.
Ce comptage par dépôt est plus parlant que les octets, faussés par les templates et dépendances versionnés.
"""
import json
import os
import urllib.request

USER = "Ky-Wilson"
TOKEN = os.environ["GH_TOKEN"]
MIN_SHARE = 0.10
LIMIT = 10
IGNORED = {
    "HTML", "CSS", "SCSS", "Less", "Blade", "Twig", "Handlebars", "CMake", "C", "C++",
    "Objective-C", "Swift", "Shell", "Batchfile", "Dockerfile", "Procfile", "Hack",
}
COLORS = {
    "PHP": "#4F5D95", "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Dart": "#00B4AB",
    "Kotlin": "#A97BFF", "Rust": "#dea584", "Python": "#3572A5", "Vue": "#41b883",
}


def api(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as res:
        return json.load(res)


repos, page = [], 1
while True:
    batch = api(f"/user/repos?affiliation=owner&per_page=100&page={page}")
    repos += [r for r in batch if not r["fork"]]
    if len(batch) < 100:
        break
    page += 1

counts = {}
for repo in repos:
    langs = {k: v for k, v in api(f"/repos/{repo['full_name']}/languages").items() if k not in IGNORED}
    total = sum(langs.values())
    for lang, size in langs.items():
        if total and size / total >= MIN_SHARE:
            counts[lang] = counts.get(lang, 0) + 1

top = sorted(counts.items(), key=lambda kv: -kv[1])[:LIMIT]
peak = top[0][1] if top else 1

row_h, width, label_w, bar_w = 28, 480, 110, 300
height = 56 + row_h * len(top)
rows = []
for i, (lang, n) in enumerate(top):
    y = 52 + i * row_h
    w = max(4, round(bar_w * n / peak))
    color = COLORS.get(lang, "#8b949e")
    rows.append(
        f'<text x="16" y="{y + 13}" class="l">{lang}</text>'
        f'<rect x="{16 + label_w}" y="{y}" width="{w}" height="16" rx="4" fill="{color}"/>'
        f'<text x="{16 + label_w + w + 8}" y="{y + 13}" class="n">{n} dépôt{"s" if n > 1 else ""}</text>'
    )

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">
<title id="t">Langages principaux sur {len(repos)} dépôts, privés inclus : {", ".join(f"{l} ({n})" for l, n in top)}</title>
<style>
text{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;fill:#57606a}}
.h{{font-size:15px;font-weight:600;fill:#58a6ff}}.s{{font-size:11px}}.l{{font-size:12px;font-weight:600}}.n{{font-size:11px}}
@media (prefers-color-scheme:dark){{text{{fill:#c9d1d9}}.h{{fill:#58a6ff}}}}
</style>
<text x="16" y="24" class="h">Langages principaux</text>
<text x="16" y="40" class="s">{len(repos)} dépôts, privés inclus · nombre de dépôts où le langage pèse au moins 10 % du code</text>
{"".join(rows)}
</svg>
"""

os.makedirs("metrics", exist_ok=True)
with open("metrics/languages.svg", "w", encoding="utf-8") as f:
    f.write(svg)
print(dict(top))
