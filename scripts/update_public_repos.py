#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
from datetime import datetime

README_PATH = os.getenv("README_PATH", "README.md")
USERNAME = os.getenv("GITHUB_USERNAME", "Ezakgean")
LIMIT = int(os.getenv("REPOS_LIMIT", "8"))

START = "<!-- REPOS:START -->"
END = "<!-- REPOS:END -->"


def fetch_repos(username: str):
    url = (
        f"https://api.github.com/users/{username}/repos"
        "?per_page=100&sort=updated&direction=desc"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "readme-repo-updater",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)


def build_lines(repos):
    public_repos = []
    for repo in repos:
        if repo.get("private"):
            continue
        if repo.get("fork"):
            continue
        if repo.get("archived"):
            continue
        public_repos.append(repo)

    public_repos.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    public_repos = public_repos[:LIMIT]

    lines = []
    for repo in public_repos:
        name = repo.get("name", "")
        url = repo.get("html_url", "")
        desc = repo.get("description") or "Sem descricao."
        stars = repo.get("stargazers_count", 0)
        updated = repo.get("updated_at") or ""
        try:
            updated_date = datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ").date()
            updated_str = updated_date.isoformat()
        except ValueError:
            updated_str = updated

        line = (
            f"- [`{name}`]({url}) — {desc} "
            f"⭐ {stars} • Atualizado em {updated_str}"
        )
        lines.append(line)

    if not lines:
        lines.append("- Nenhum repositorio publico encontrado.")

    return lines


def update_readme(path: str, lines):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    start_idx = content.find(START)
    end_idx = content.find(END)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError("Marcadores de repositorios nao encontrados no README.")

    before = content[: start_idx + len(START)]
    after = content[end_idx:]
    block = "\n" + "\n".join(lines) + "\n"
    new_content = before + block + after

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)


if __name__ == "__main__":
    try:
        repos = fetch_repos(USERNAME)
        lines = build_lines(repos)
        update_readme(README_PATH, lines)
    except Exception as exc:
        print(f"Erro ao atualizar README: {exc}", file=sys.stderr)
        sys.exit(1)
