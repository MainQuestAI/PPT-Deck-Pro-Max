#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from html import escape
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def split_clean_page(clean_page: str, page_id: str) -> tuple[str, list[str]]:
    lines = [line.strip() for line in clean_page.splitlines()]
    content = [line for line in lines if line and not line.startswith("#") and not line.startswith(">")]
    if not content:
        return page_id, []
    title = content[0]
    body = content[1:]
    return title, body


def relative_asset_path(output_html: Path, project_dir: Path, final_path: str) -> str:
    asset_path = (project_dir / final_path).resolve()
    if asset_path.exists():
        return os.path.relpath(asset_path, output_html.parent.resolve())
    return str(Path("..") / ".." / final_path)


def render_asset(asset: dict, output_html: Path, project_dir: Path) -> str:
    src = relative_asset_path(output_html, project_dir, asset.get("final_path", ""))
    position = escape(asset.get("position", "right"))
    desc = escape(asset.get("desc", asset.get("asset_id", "visual")))
    return (
        f'<figure class="approved-asset approved-asset--{position}">'
        f'<img src="{escape(src)}" alt="{desc}" />'
        f"</figure>"
    )


def render_page(page: dict, output_html: Path, project_dir: Path) -> str:
    page_id = page.get("page_id", "slide_unknown")
    role = page.get("role", "")
    title, body = split_clean_page(page.get("clean_page", ""), page_id)
    body_html = "\n".join(f"<p>{escape(paragraph)}</p>" for paragraph in body)
    assets_html = "\n".join(render_asset(asset, output_html, project_dir) for asset in page.get("approved_assets", []))
    return f"""
    <section class="slide" data-slide="{escape(page_id)}" data-role="{escape(role)}">
      <div class="slide-copy">
        <div class="section-label">{escape(role.upper() or page_id.upper())}</div>
        <h1>{escape(title)}</h1>
        {body_html}
      </div>
      <div class="slide-visual">
        {assets_html}
      </div>
    </section>
    """.strip()


def render_html(pages: list[dict], output_html: Path, project_dir: Path) -> str:
    slides = "\n".join(render_page(page, output_html, project_dir) for page in pages)
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Deck Batch</title>
    <link rel="stylesheet" href="../fonts/fonts.css" />
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <main class="deck">
      {slides}
    </main>
  </body>
</html>
"""


def ensure_styles(styles_path: Path) -> None:
    extra = """

.deck {
  display: grid;
  gap: 40px;
  padding: 32px 0 64px;
}

.slide {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 32px;
  align-items: center;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 32px;
  backdrop-filter: blur(12px);
}

.slide-copy h1 {
  margin: 12px 0 16px;
  font-size: 40px;
  line-height: 1.1;
}

.slide-copy p {
  margin: 0 0 12px;
  color: rgba(234, 242, 249, 0.88);
  font-size: 18px;
  line-height: 1.55;
}

.slide-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.approved-asset {
  width: 100%;
  margin: 0;
}

.approved-asset img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.35);
}
""".strip("\n")
    current = styles_path.read_text(encoding="utf-8") if styles_path.exists() else ""
    if ".deck {" in current:
        return
    styles_path.write_text(current.rstrip() + "\n" + extra + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assemble batch HTML from assemble_context.json into starter index.html.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--context")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).expanduser().resolve()
    context_path = Path(args.context).expanduser().resolve() if args.context else project_dir / "assemble" / args.batch_id / "assemble_context.json"
    context = load_json(context_path)
    if not context:
        raise SystemExit(f"[ERROR] assemble context not found: {context_path}")

    output_html = Path(context.get("output_html", "")).expanduser().resolve()
    output_css = Path(context.get("output_css", "")).expanduser().resolve()
    pages = context.get("pages", [])
    if not output_html:
        raise SystemExit("[ERROR] output_html missing in assemble context.")
    output_html.parent.mkdir(parents=True, exist_ok=True)
    ensure_styles(output_css)
    html = render_html(pages, output_html, project_dir)
    output_html.write_text(html, encoding="utf-8")
    print(f"[OK] assembled html batch: {output_html}")


if __name__ == "__main__":
    main()
