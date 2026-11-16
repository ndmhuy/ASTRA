"""Small transport schema; full bounds and semantic checks remain enforced in Python."""

_LOCAL_CONSTRAINTS = {
    "title",
    "default",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "minProperties",
    "maxProperties",
    "pattern",
}


def compact_schema(value):
    if isinstance(value, list):
        return [compact_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        if key in _LOCAL_CONSTRAINTS:
            continue
        if key in {"properties", "$defs"}:
            result[key] = {name: compact_schema(node) for name, node in item.items()}
        else:
            result[key] = compact_schema(item)
    return result
