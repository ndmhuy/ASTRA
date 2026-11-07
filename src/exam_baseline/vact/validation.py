"""Verify template-group bindings before accepting a model response."""

import re


def validate_batch(section, batch):
    if [q.id for q in section.questions] != batch.ids:
        raise ValueError("VACT question IDs/count/order differ from the template batch")
    required = {g.id: g for g in batch.groups if g.shared}
    if len(section.passages) != len(required) or {p.id for p in section.passages} != set(required):
        raise ValueError(
            f"Expected passage IDs {list(required)}, received {[p.id for p in section.passages]}. "
            "Use the exact shared_groups IDs, never invent p1/p2 IDs."
        )
    for q in section.questions:
        number = int(q.id[1:])
        group = next(g for g in batch.groups if g.start <= number <= g.end)
        expected = group.id if group.shared else None
        if q.passage_id is None:
            # Fixed metadata comes from the template, after all required passages exist.
            q.passage_id = expected
        elif q.passage_id != expected:
            raise ValueError(f"{q.id} must bind passage_id={expected}, received {q.passage_id}")
        if re.search(r"hình (vẽ|bên|dưới)|đồ thị như|diagram (below|shown)", q.stem, re.I):
            has_visual = q.illustration_request or any(
                other.illustration_request and other.passage_id == q.passage_id
                for other in section.questions
                if q.passage_id
            )
            if not has_visual:
                raise ValueError(f"{q.id} refers to an unrequested drawing")
    return section
