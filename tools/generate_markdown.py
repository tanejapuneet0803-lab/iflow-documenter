"""
Read tmp/parsed.json and generate a markdown documentation file in output/.
The output filename is derived from the iFlow name in the JSON.

Usage:
    python tools/generate_markdown.py
"""

import json
import re
from pathlib import Path

TMP_DIR = Path(__file__).parent.parent / "tmp"
OUT_DIR = Path(__file__).parent.parent / "output"
PARSED_JSON = TMP_DIR / "parsed.json"


def slugify(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")


def extract_placeholders(obj) -> set[str]:
    """Recursively find all {{PARAM}} placeholders in any string value."""
    found = set()
    if isinstance(obj, str):
        found.update(re.findall(r"\{\{([^}]+)\}\}", obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            found.update(extract_placeholders(v))
    elif isinstance(obj, list):
        for item in obj:
            found.update(extract_placeholders(item))
    return found


def build_summary(data: dict) -> str:
    cfg = data.get("global_config", {})
    senders = data.get("senders", [])
    receivers = data.get("receivers", [])
    processes = data.get("processes", [])
    scripts = data.get("scripts", [])

    lines = [
        "## Summary\n",
        f"**iFlow Name:** {data['iflow_name']}  ",
        f"**Description:** {data.get('description', '_Not provided_')}  ",
        "",
        "| Property | Value |",
        "| --- | --- |",
        f"| Component Version | {cfg.get('componentVersion', '-')} |",
        f"| HTTP Session Handling | {cfg.get('httpSessionHandling', '-')} |",
        f"| Log Level | {cfg.get('log', '-')} |",
        f"| Server Trace | {cfg.get('ServerTrace', '-')} |",
        f"| Return Exception to Sender | {cfg.get('returnExceptionToSender', '-')} |",
        f"| Allowed Headers | {cfg.get('allowedHeaderList', '-')} |",
        f"| Namespace Mapping | `{cfg.get('namespaceMapping', '-')}` |",
        "",
        f"**Senders:** {', '.join(s['name'] for s in senders)}  ",
        f"**Receivers:** {', '.join(r['name'] for r in receivers)}  ",
        f"**Processes:** {len(processes)}  ",
        f"**Groovy Scripts:** {len(scripts)}  ",
    ]
    return "\n".join(lines)


def build_data_flow_diagram(data: dict) -> str:
    sender_adapters = data.get("sender_adapters", [])
    receiver_adapters = data.get("receiver_adapters", [])
    processes = data.get("processes", [])

    lines = ["## Data Flow Diagram (ASCII)\n", "```"]

    # Collect top-level (entry point) processes — those with no process_type or MessageStartEvent
    entry_processes = [
        p for p in processes
        if not p.get("process_type") or p["process_type"] == ""
    ]
    sub_processes = [p for p in processes if p.get("process_type") == "directCall"]

    # Build sender → process lines
    for sa in sender_adapters:
        system = sa.get("system", "?")
        adapter = sa.get("component_type", sa.get("name", "?"))
        address = sa.get("address", "")
        addr_label = f" ({address})" if address and address != "Not Applicable" else ""
        lines.append(f"  [{system}] --{adapter}{addr_label}--> [iFlow Entry]")

    lines.append("       |")

    # Main processes
    for ep in entry_processes:
        lines.append(f"       +--> [{ep['name']}]")
        for step in ep.get("steps", []):
            atype = step.get("activity_type", "")
            if atype == "ProcessCallElement":
                lines.append(f"       |        +--> (calls) [{step['name'].replace('Call: ', '')}]")
            elif atype == "Script":
                lines.append(f"       |        +--> [Script: {step['script']}]")
        lines.append("       |")

    # Sub-processes
    if sub_processes:
        lines.append("  Sub-processes (called internally):")
        for sp in sub_processes:
            lines.append(f"    [{sp['name']}]")

    lines.append("       |")

    # Receiver adapters
    for ra in receiver_adapters:
        system = ra.get("system", "?")
        adapter = ra.get("component_type", ra.get("name", "?"))
        address = ra.get("address", "")
        addr_label = f" ({address})" if address and address != "Not Applicable" else ""
        lines.append(f"       +--> [{system}] via {adapter}{addr_label}")

    lines.append("```")
    return "\n".join(lines)


def build_adapter_configuration(data: dict) -> str:
    lines = ["## Adapter Configuration\n"]

    sender_adapters = data.get("sender_adapters", [])
    if sender_adapters:
        lines.append("### Sender Adapters\n")
        lines += [
            "| Name | System | Type | Address | Transport | Message Protocol | Authentication |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for a in sender_adapters:
            lines.append(
                f"| {a.get('name','-')} | {a.get('system','-')} | {a.get('component_type','-')} "
                f"| `{a.get('address','-')}` | {a.get('transport_protocol','-')} "
                f"| {a.get('message_protocol','-')} | {a.get('authentication','-') or '-'} |"
            )
        lines.append("")

    receiver_adapters = data.get("receiver_adapters", [])
    if receiver_adapters:
        lines.append("### Receiver Adapters\n")
        lines += [
            "| Name | System | Type | Address | Transport | Message Protocol | Authentication |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for a in receiver_adapters:
            lines.append(
                f"| {a.get('name','-')} | {a.get('system','-')} | {a.get('component_type','-')} "
                f"| `{a.get('address','-')}` | {a.get('transport_protocol','-')} "
                f"| {a.get('message_protocol','-')} | {a.get('authentication','-') or '-'} |"
            )
        lines.append("")

    # Extra config for adapters that have it
    all_adapters = sender_adapters + receiver_adapters
    extras = [(a.get("name", "-"), a.get("extra", {})) for a in all_adapters if a.get("extra")]
    if extras:
        lines.append("### Additional Adapter Properties\n")
        for name, extra in extras:
            lines.append(f"**{name}**\n")
            lines += [
                "| Key | Value |",
                "| --- | --- |",
            ]
            for k, v in extra.items():
                safe_v = str(v).replace("|", "\\|")
                lines.append(f"| `{k}` | {safe_v} |")
            lines.append("")

    return "\n".join(lines)


def build_mapping_logic(data: dict) -> str:
    lines = ["## Mapping Logic\n"]

    # Scripts used for mapping
    scripts = data.get("scripts", [])
    mapping_scripts = [s for s in scripts if "mapping" in s["filename"].lower() or "map" in s["filename"].lower()]
    if mapping_scripts:
        lines.append("### Mapping Scripts\n")
        for s in mapping_scripts:
            lines.append(f"**`{s['filename']}`**  ")
            lines.append(f"{s['summary']}\n")

    # Routing conditions
    conditions = data.get("routing_conditions", [])
    if conditions:
        lines.append("### Routing Conditions\n")
        lines += [
            "| Route Name | Expression Type | Condition |",
            "| --- | --- | --- |",
        ]
        for c in conditions:
            cond = str(c.get("condition", "")).replace("|", "\\|")
            lines.append(
                f"| {c.get('name', '-')} | {c.get('expression_type', '-')} | `{cond}` |"
            )
        lines.append("")

    # Steps across all processes that reference scripts (non-error)
    lines.append("### Script Steps by Process\n")
    for proc in data.get("processes", []):
        script_steps = [s for s in proc.get("steps", []) if s.get("script")]
        if script_steps:
            lines.append(f"**{proc['name']}**\n")
            for step in script_steps:
                lines.append(f"- `{step['script']}` — _{step['name']}_")
            lines.append("")

    return "\n".join(lines)


def build_error_handling(data: dict) -> str:
    lines = ["## Error Handling\n"]

    has_content = False
    for proc in data.get("processes", []):
        handlers = proc.get("error_handlers", [])
        if not handlers:
            continue
        has_content = True
        lines.append(f"### Process: {proc['name']}\n")
        for handler in handlers:
            lines.append(f"**Exception Subprocess:** `{handler['name']}`  ")
            lines.append("")
            lines += [
                "| Step | Type | Script |",
                "| --- | --- | --- |",
            ]
            for step in handler.get("steps", []):
                script = f"`{step['script']}`" if step.get("script") else "-"
                lines.append(f"| {step['name']} | {step.get('activity_type', '-') or '-'} | {script} |")
            lines.append("")

    # Scripts that raise errors
    error_scripts = [
        s for s in data.get("scripts", [])
        if "validates inputs" in s.get("summary", "") or "raises errors" in s.get("summary", "")
    ]
    if error_scripts:
        has_content = True
        lines.append("### Scripts with Error / Validation Logic\n")
        for s in error_scripts:
            lines.append(f"**`{s['filename']}`**  ")
            lines.append(f"{s['summary']}\n")

    if not has_content:
        lines.append("_No error handlers detected._\n")

    return "\n".join(lines)


def build_externalised_parameters(data: dict) -> str:
    lines = ["## Externalised Parameters\n"]

    placeholders = extract_placeholders(data)
    if not placeholders:
        lines.append("_No externalised parameters detected._\n")
        return "\n".join(lines)

    lines += [
        "| Parameter | Used In |",
        "| --- | --- |",
    ]

    # Build a map of param → where it appears
    def find_usages(param: str, obj, path="") -> list[str]:
        usages = []
        if isinstance(obj, str) and f"{{{{{param}}}}}" in obj:
            usages.append(path)
        elif isinstance(obj, dict):
            for k, v in obj.items():
                usages.extend(find_usages(param, v, f"{path}.{k}" if path else k))
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                usages.extend(find_usages(param, item, f"{path}[{i}]"))
        return usages

    for param in sorted(placeholders):
        usages = find_usages(param, data)
        # Simplify usage paths to be human-readable
        readable = []
        for u in usages:
            if u.startswith("sender_adapters") or u.startswith("receiver_adapters"):
                readable.append("Adapter config")
            elif u.startswith("scripts"):
                readable.append("Script summary")
            elif u.startswith("global_config"):
                readable.append("Global config")
            else:
                readable.append(u.split(".")[0].replace("_", " ").title())
        unique_usages = ", ".join(sorted(set(readable)))
        lines.append(f"| `{{{{{param}}}}}` | {unique_usages} |")

    lines.append("")
    return "\n".join(lines)


def build_dependencies(data: dict) -> str:
    lines = ["## Dependencies\n"]

    # External systems
    systems = set()
    for a in data.get("sender_adapters", []) + data.get("receiver_adapters", []):
        sys_name = a.get("system", "")
        adapter = a.get("component_type", "")
        if sys_name:
            systems.add((sys_name, adapter, a.get("direction", "")))

    if systems:
        lines.append("### External Systems\n")
        lines += [
            "| System | Adapter Type | Direction |",
            "| --- | --- | --- |",
        ]
        for sys_name, adapter, direction in sorted(systems):
            lines.append(f"| {sys_name} | {adapter} | {direction} |")
        lines.append("")

    # Scripts
    scripts = data.get("scripts", [])
    if scripts:
        lines.append("### Groovy Scripts\n")
        lines += [
            "| Script | Summary |",
            "| --- | --- |",
        ]
        for s in scripts:
            summary = s.get("summary", "-")
            # Trim to first sentence for the table
            first_sentence = summary.split(". ")[0].rstrip(".")
            lines.append(f"| `{s['filename']}` | {first_sentence} |")
        lines.append("")

    # Adapter component types
    adapter_types = set(
        a.get("component_type", "") for a in
        data.get("sender_adapters", []) + data.get("receiver_adapters", [])
        if a.get("component_type")
    )
    if adapter_types:
        lines.append("### Adapter Types Used\n")
        for t in sorted(adapter_types):
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines)


def generate(parsed_path: Path = PARSED_JSON, out_dir: Path = OUT_DIR) -> Path:
    with open(parsed_path, encoding="utf-8") as f:
        data = json.load(f)

    iflow_name = data.get("iflow_name", "iflow")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{slugify(iflow_name)}.md"

    sections = [
        f"# {iflow_name}\n",
        build_summary(data),
        "",
        build_data_flow_diagram(data),
        "",
        build_adapter_configuration(data),
        "",
        build_mapping_logic(data),
        "",
        build_error_handling(data),
        "",
        build_externalised_parameters(data),
        "",
        build_dependencies(data),
    ]

    content = "\n".join(sections)
    out_file.write_text(content, encoding="utf-8")
    print(f"Done. Documentation written to {out_file}")
    return out_file


if __name__ == "__main__":
    generate()
