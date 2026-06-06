"""
Read all Groovy/GSH/XSL script files in tmp/ and append plain-English
summaries to tmp/parsed.json under a 'scripts' key.

Tries the Claude API first (ANTHROPIC_API_KEY env var); falls back to
static analysis if the API is unavailable or has no credits.

Usage:
    python tools/parse_groovy.py
"""

import json
import os
import re
import sys
from pathlib import Path

TMP_DIR = Path(__file__).parent.parent / "tmp"
PARSED_JSON = TMP_DIR / "parsed.json"
SCRIPT_EXTS = {".groovy", ".gsh", ".xsl", ".xslt"}

MODEL = "claude-haiku-4-5-20251001"

SYSTEM = """\
You are a technical documentation assistant specialising in SAP Integration Suite (SAP CPI) iFlow scripts.

When given the source code of a Groovy/GSH script or XSLT file used inside an SAP CPI iFlow, respond with a \
concise plain-English summary (3–6 sentences) covering:
- What the script's overall purpose is
- Which message properties or headers it reads
- Which message properties or headers it sets or modifies
- Any external calls, transformations, or validations it performs
- Any notable error handling

Be factual and specific. Do not include code snippets in your answer."""


# ---------------------------------------------------------------------------
# Static-analysis fallback
# ---------------------------------------------------------------------------

def _extract(pattern: str, source: str) -> list[str]:
    return sorted(set(re.findall(pattern, source)))


def static_summary(filename: str, source: str) -> str:
    ext = Path(filename).suffix.lower()

    if ext in {".xsl", ".xslt"}:
        templates = _extract(r'match="([^"]+)"', source)
        return (
            f"{filename} is an XSLT stylesheet. "
            + (f"It defines templates matching: {', '.join(templates[:6])}." if templates else "")
        ).strip()

    props_read  = _extract(r'(?:getProperty|pmap\.get)\(["\'](\w+)["\']', source)
    props_set   = _extract(r'setProperty\(["\'](\w+)["\']', source)
    headers_set = _extract(r'setHeader\(["\'](\w+)["\']', source)
    errors      = _extract(r'throw new \w*Exception\("([^"]{0,80})', source)
    calls       = _extract(r'(?:messageLog|client|http|soap)\.\w+', source)

    parts = [f"{filename} is a Groovy/GSH script used in an SAP CPI iFlow."]

    if props_read:
        parts.append(f"It reads properties: {', '.join(props_read[:8])}{'…' if len(props_read) > 8 else ''}.")
    if props_set:
        parts.append(f"It sets properties: {', '.join(props_set[:8])}{'…' if len(props_set) > 8 else ''}.")
    if headers_set:
        parts.append(f"It sets headers: {', '.join(headers_set)}.")
    if errors:
        parts.append(f"It validates inputs and raises errors such as: \"{errors[0]}\".")
    if calls:
        parts.append(f"Notable calls: {', '.join(calls[:5])}.")

    if len(parts) == 1:
        parts.append("No properties, headers, or explicit error handling detected.")

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Claude API summariser
# ---------------------------------------------------------------------------

def api_summary(client, filename: str, source: str) -> str:
    ext = Path(filename).suffix.lower()
    lang = "XSLT" if ext in {".xsl", ".xslt"} else "Groovy"
    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": f"Summarise this {lang} script ({filename}):\n\n```\n{source}\n```"}],
    )
    return response.content[0].text.strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not PARSED_JSON.exists():
        sys.exit(f"Error: {PARSED_JSON} not found — run parse_iflow_xml.py first.")

    parsed = json.loads(PARSED_JSON.read_text(encoding="utf-8"))

    script_files = sorted(
        f for f in TMP_DIR.rglob("*") if f.suffix.lower() in SCRIPT_EXTS
    )

    if not script_files:
        print("No script files found in tmp/ — noting 'no custom scripts found'.")
        parsed["scripts"] = []
        parsed["scripts_note"] = "no custom scripts found"
        PARSED_JSON.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
        return

    # Try to set up the API client; fall back gracefully if unavailable
    client = None
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            # Probe with a tiny request to detect credit/auth issues early
            client.messages.create(
                model=MODEL, max_tokens=1,
                messages=[{"role": "user", "content": "hi"}],
            )
            print("Claude API available — using AI summaries.")
        except Exception as e:
            print(f"Claude API unavailable ({e}); falling back to static analysis.")
            client = None
    else:
        print("ANTHROPIC_API_KEY not set — using static analysis.")

    scripts = []
    for path in script_files:
        source = path.read_text(encoding="utf-8", errors="replace")
        print(f"Summarising {path.name} …")

        if client is not None:
            try:
                summary = api_summary(client, path.name, source)
            except Exception as e:
                print(f"  API error ({e}); falling back to static analysis.")
                summary = static_summary(path.name, source)
        else:
            summary = static_summary(path.name, source)

        scripts.append({
            "filename": path.name,
            "path":     path.relative_to(TMP_DIR).as_posix(),
            "type":     "xslt" if path.suffix.lower() in {".xsl", ".xslt"} else "groovy",
            "summary":  summary,
        })
        print(f"  > {summary[:100]}{'...' if len(summary) > 100 else ''}")

    parsed["scripts"] = scripts
    parsed.pop("scripts_note", None)
    PARSED_JSON.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone. {len(scripts)} script(s) written to {PARSED_JSON}")


if __name__ == "__main__":
    main()
