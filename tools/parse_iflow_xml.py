"""
Parse a SAP iFlow .iflw (BPMN2) XML file and emit tmp/parsed.json.

Extracts: processes/steps, sender/receiver adapters, routing conditions,
and error-handling subprocesses.

Usage:
    python tools/parse_iflow_xml.py <zip_stem>
    # zip_stem is the folder name inside tmp/ created by unzip_iflow.py
    # e.g. "SAP SuccessFactors Employee Central Integration with SAP S_4HANA Cloud_ Employee Data"
"""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

TMP_DIR = Path(__file__).parent.parent / "tmp"

NS = {
    "bpmn2": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "ifl":   "http:///com.sap.ifl.model/Ifl.xsd",
}


def ifl_props(element: ET.Element) -> dict:
    """Return all ifl:property key/value pairs as a dict."""
    props = {}
    ext = element.find("bpmn2:extensionElements", NS)
    if ext is None:
        return props
    for prop in ext.findall("ifl:property", NS):
        k = prop.findtext("key", default="", namespaces=NS)
        v = prop.findtext("value", default="", namespaces=NS)
        if k:
            props[k] = v
    return props


def parse_step(el: ET.Element) -> dict:
    tag = el.tag.split("}")[-1]  # strip namespace
    props = ifl_props(el)
    return {
        "id":           el.get("id"),
        "name":         el.get("name", ""),
        "element_type": tag,
        "activity_type": props.get("activityType", ""),
        "sub_type":     props.get("subActivityType", ""),
        "script":       props.get("script", ""),
        "cmd_variant":  props.get("cmdVariantUri", ""),
    }


def parse_gateway_routes(root: ET.Element) -> list[dict]:
    routes = []
    for sf in root.iter(f"{{{NS['bpmn2']}}}sequenceFlow"):
        cond = sf.find("bpmn2:conditionExpression", NS)
        if cond is None:
            continue
        props = ifl_props(sf)
        routes.append({
            "id":             sf.get("id"),
            "name":           sf.get("name", ""),
            "source":         sf.get("sourceRef", ""),
            "target":         sf.get("targetRef", ""),
            "expression_type": props.get("expressionType", ""),
            "condition":      (cond.text or "").strip(),
        })
    return routes


def parse_adapter(mf: ET.Element) -> dict:
    props = ifl_props(mf)
    return {
        "id":               mf.get("id"),
        "name":             mf.get("name", ""),
        "source":           mf.get("sourceRef", ""),
        "target":           mf.get("targetRef", ""),
        "component_type":   props.get("ComponentType", ""),
        "direction":        props.get("direction", ""),
        "system":           props.get("system", ""),
        "address":          props.get("address", ""),
        "transport_protocol": props.get("TransportProtocol", ""),
        "message_protocol": props.get("MessageProtocol", ""),
        "authentication":   props.get("authenticationType") or props.get("authentication") or props.get("senderAuthType", ""),
        "extra":            {k: v for k, v in props.items()
                            if k not in {"ComponentType", "direction", "system", "address",
                                         "TransportProtocol", "MessageProtocol",
                                         "authenticationType", "authentication", "senderAuthType",
                                         "Description", "cmdVariantUri", "componentVersion",
                                         "ComponentNS", "ComponentSWCVName", "ComponentSWCVId",
                                         "TransportProtocolVersion", "MessageProtocolVersion",
                                         "Name", "Vendor"} and v},
    }


def parse_process(proc: ET.Element) -> dict:
    pid = proc.get("id")
    name = proc.get("name", "")
    props = ifl_props(proc)

    step_tags = {
        f"{{{NS['bpmn2']}}}callActivity",
        f"{{{NS['bpmn2']}}}serviceTask",
        f"{{{NS['bpmn2']}}}startEvent",
        f"{{{NS['bpmn2']}}}endEvent",
        f"{{{NS['bpmn2']}}}exclusiveGateway",
        f"{{{NS['bpmn2']}}}parallelGateway",
    }

    steps = []
    for child in proc:
        if child.tag in step_tags:
            steps.append(parse_step(child))

    # error-handling subprocesses
    error_handlers = []
    for sp in proc.findall(f"{{{NS['bpmn2']}}}subProcess"):
        sp_props = ifl_props(sp)
        sp_steps = []
        for child in sp:
            if child.tag in step_tags:
                sp_steps.append(parse_step(child))
        error_handlers.append({
            "id":            sp.get("id"),
            "name":          sp.get("name", ""),
            "activity_type": sp_props.get("activityType", ""),
            "steps":         sp_steps,
        })

    return {
        "id":             pid,
        "name":           name,
        "process_type":   props.get("processType", ""),
        "transaction":    props.get("transactionalHandling", ""),
        "steps":          steps,
        "error_handlers": error_handlers,
    }


def find_iflw(tmp_stem: Path) -> Path:
    """
    iFlow exports have a two-level zip structure:
      outer zip  → tmp/<stem>/  (contains *_content files)
      _content   → another zip  → src/main/resources/scenarioflows/**/*.iflw

    Try direct search first (handles already-extracted inner zips), then
    crack open any *_content files that look like zips.
    """
    import zipfile

    matches = list(tmp_stem.rglob("*.iflw"))
    if matches:
        return matches[0]

    # Also check all of TMP_DIR in case a previous run extracted things elsewhere
    matches = list(TMP_DIR.rglob("*.iflw"))
    if matches:
        return matches[0]

    # Extract _content files that are zip archives
    inner_dir = TMP_DIR / "_iflow_extracted"
    for content_file in tmp_stem.glob("*_content"):
        try:
            with zipfile.ZipFile(content_file) as zf:
                names = zf.namelist()
                if any(n.endswith(".iflw") for n in names):
                    zf.extractall(inner_dir)
        except zipfile.BadZipFile:
            continue

    matches = list(inner_dir.rglob("*.iflw")) if inner_dir.exists() else []
    if matches:
        return matches[0]

    raise FileNotFoundError(
        f"No .iflw file found under {tmp_stem} or in _content zip files."
    )


def parse(zip_stem: str) -> dict:
    base_dir = TMP_DIR / zip_stem

    # The outer package zip extracts with no inner folder; the iFlow zip is
    # one of the _content files — we may need to look in both places.
    iflw_path = find_iflw(base_dir)
    print(f"Parsing: {iflw_path.relative_to(TMP_DIR)}")

    tree = ET.parse(iflw_path)
    root = tree.getroot()

    collab = root.find("bpmn2:collaboration", NS)
    collab_props = ifl_props(collab) if collab is not None else {}

    # Participants
    senders, receivers = [], []
    if collab is not None:
        for p in collab.findall("bpmn2:participant", NS):
            ptype = p.get(f"{{{NS['ifl']}}}type", "")
            entry = {"id": p.get("id"), "name": p.get("name", ""), "type": ptype}
            if ptype == "EndpointSender":
                senders.append(entry)
            elif ptype == "EndpointRecevier":
                receivers.append(entry)

    # Adapters (message flows)
    sender_adapters, receiver_adapters = [], []
    if collab is not None:
        for mf in collab.findall("bpmn2:messageFlow", NS):
            adapter = parse_adapter(mf)
            if adapter["direction"] == "Sender":
                sender_adapters.append(adapter)
            else:
                receiver_adapters.append(adapter)

    # Integration processes
    processes = []
    for proc in root.findall("bpmn2:process", NS):
        processes.append(parse_process(proc))

    # Routing conditions (all sequence flows with conditions, across all processes)
    routing_conditions = parse_gateway_routes(root)

    result = {
        "iflow_name":         collab.get("name", "") if collab is not None else "",
        "description":        (collab.find("bpmn2:documentation", NS).text or "").strip()
                              if collab is not None and collab.find("bpmn2:documentation", NS) is not None
                              else "",
        "global_config":      {k: v for k, v in collab_props.items() if v},
        "senders":            senders,
        "receivers":          receivers,
        "sender_adapters":    sender_adapters,
        "receiver_adapters":  receiver_adapters,
        "processes":          processes,
        "routing_conditions": routing_conditions,
    }

    out_path = TMP_DIR / "parsed.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written: {out_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse iFlow XML → tmp/parsed.json")
    parser.add_argument(
        "zip_stem",
        nargs="?",
        help="Folder name inside tmp/ (stem of the original zip). "
             "If omitted, uses the first folder found in tmp/.",
    )
    args = parser.parse_args()

    if args.zip_stem:
        stem = args.zip_stem
    else:
        candidates = [p for p in TMP_DIR.iterdir() if p.is_dir() and p.name != "iflow_inner"]
        if not candidates:
            raise SystemExit("No folders found in tmp/. Run unzip_iflow.py first.")
        stem = candidates[0].name
        print(f"Auto-detected folder: {stem}")

    parse(stem)
