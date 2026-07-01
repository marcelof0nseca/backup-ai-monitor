import json
from pathlib import Path


GRAPH_FILE = Path("graph") / "components.json"


def load_graph(path=GRAPH_FILE):
    path = Path(path)

    if not path.exists():
        return {"components": [], "relations": []}

    with open(path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return {
        "components": data.get("components", []),
        "relations": data.get("relations", []),
    }


def normalize(text):
    return (text or "").lower()


def build_search_text(analysis, context_lines, documents):
    document_text = "\n".join(
        document.get("text", "")
        for document in documents
    )
    parts = [
        analysis.get("diagnosis", ""),
        analysis.get("explanation", ""),
        " ".join(analysis.get("targets", [])),
        " ".join(analysis.get("events", {}).keys()),
        "\n".join(context_lines[-10:]),
        document_text,
    ]
    return normalize("\n".join(part for part in parts if part))


def component_matches(component, search_text):
    candidates = [
        component.get("id", ""),
        component.get("name", ""),
        *component.get("aliases", []),
    ]
    return any(normalize(candidate) in search_text for candidate in candidates)


def find_components(search_text, components):
    return [
        component
        for component in components
        if component_matches(component, search_text)
    ]


def component_by_id(components):
    return {component["id"]: component for component in components}


def find_relations(component_id, relations, components_index):
    found = []

    for relation in relations:
        source = relation.get("from")
        target = relation.get("to")

        if source == component_id:
            related = components_index.get(target)
            direction = "sai para"
        elif target == component_id:
            related = components_index.get(source)
            direction = "vem de"
        else:
            continue

        if not related:
            continue

        found.append(
            {
                "type": relation.get("type", "RELATED_TO"),
                "direction": direction,
                "description": relation.get("description", ""),
                "related_component": related,
            }
        )

    return found


def find_dependency_context(analysis, context_lines, documents=None):
    documents = documents or []
    graph = load_graph()
    components = graph["components"]
    relations = graph["relations"]
    search_text = build_search_text(analysis, context_lines, documents)
    matched_components = find_components(search_text, components)
    components_index = component_by_id(components)

    return [
        {
            "component": component,
            "relations": find_relations(
                component["id"],
                relations,
                components_index,
            ),
        }
        for component in matched_components
    ]
