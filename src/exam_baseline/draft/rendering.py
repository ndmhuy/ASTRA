"""Legacy Pillow renderer for draft-only fixtures; native pipeline uses TikZ."""

from pathlib import Path

from exam_baseline.core.hashing import digest
from exam_baseline.draft.models import FigureArtifact, VisualSpec


def render_visual(spec: VisualSpec, destination: Path) -> FigureArtifact:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (900, 600), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font = ImageFont.truetype("DejaVuSans.ttf", 22)
    left, top, right, bottom = 105, 60, 820, 490
    if spec.kind != "geometry_segments":
        draw.line([(left, top), (left, bottom), (right, bottom)], fill="black", width=3)

    def xy(point, x_domain, y_domain):
        x, y = point
        return (
            left + (x - x_domain[0]) / (x_domain[1] - x_domain[0]) * (right - left),
            bottom - (y - y_domain[0]) / (y_domain[1] - y_domain[0]) * (bottom - top),
        )

    if spec.kind == "line_graph":
        coords = [xy(p, spec.x_domain, spec.y_domain) for p in spec.points]
        for value in sorted({x for x, _ in spec.points}):
            x = xy((value, spec.y_domain[0]), spec.x_domain, spec.y_domain)[0]
            draw.line([(x, bottom), (x, bottom + 7)], fill="black", width=2)
            draw.text((x - 10, bottom + 12), f"{value:g}", fill="black", font=font)
        for value in sorted({y for _, y in spec.points}):
            y = xy((spec.x_domain[0], value), spec.x_domain, spec.y_domain)[1]
            draw.line([(left - 7, y), (left, y)], fill="black", width=2)
            draw.text((left - 48, y - 12), f"{value:g}", fill="black", font=font)
        draw.line(coords, fill="blue", width=4)
        for x, y in coords:
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="blue")
        draw.text((right - 45, bottom + 12), f"{spec.x_domain[1]:g}", fill="black", font=font)
        draw.text((left - 48, top - 12), f"{spec.y_domain[1]:g}", fill="black", font=font)
    elif spec.kind == "bar_chart":
        maximum = max(spec.values)
        if maximum <= 0:
            raise ValueError("Bar values must contain a positive maximum")
        step = (right - left) / len(spec.values)
        for i, (label, value) in enumerate(zip(spec.labels, spec.values, strict=True)):
            if value < 0:
                raise ValueError("Bar values must be nonnegative")
            x0 = left + i * step + step * 0.2
            x1 = left + (i + 1) * step - step * 0.2
            y0 = bottom - value / maximum * (bottom - top)
            draw.rectangle((x0, y0, x1, bottom), fill="steelblue")
            draw.text((x0, bottom + 8), label, fill="black", font=font)
            draw.text((x0, y0 - 28), str(value), fill="black", font=font)
    else:
        xs, ys = [p[0] for p in spec.points], [p[1] for p in spec.points]
        x_domain = spec.x_domain or (min(xs) - 1, max(xs) + 1)
        y_domain = spec.y_domain or (min(ys) - 1, max(ys) + 1)
        if x_domain[0] >= x_domain[1] or y_domain[0] >= y_domain[1]:
            raise ValueError("Geometry domain must increase")
        if spec.scaling == "equal":
            x_mid = sum(x_domain) / 2
            y_mid = sum(y_domain) / 2
            x_span = max(
                x_domain[1] - x_domain[0],
                (y_domain[1] - y_domain[0]) * (right - left) / (bottom - top),
            )
            y_span = x_span * (bottom - top) / (right - left)
            x_domain = (x_mid - x_span / 2, x_mid + x_span / 2)
            y_domain = (y_mid - y_span / 2, y_mid + y_span / 2)
        coords = [xy(p, x_domain, y_domain) for p in spec.points]
        for a, b in spec.segments:
            draw.line([coords[a], coords[b]], fill="black", width=4)
        for label, (x, y) in zip(spec.labels, coords, strict=True):
            draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="black")
            draw.text((x + 8, y - 28), label, fill="black", font=font)
    draw.text((left, 545), spec.x_label or "", fill="black", font=font)
    draw.text((left, 20), spec.y_label or spec.units or "", fill="black", font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG")
    asset = destination.read_bytes()
    if not asset.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Renderer did not produce PNG")
    return FigureArtifact(
        visual_id=spec.visual_id,
        question_id=spec.question_id,
        revision=spec.revision,
        path=f"figures/{destination.name}",
        asset_sha256=digest(asset),
        spec_sha256=digest(spec.model_dump_json().encode()),
        width_px=int.from_bytes(asset[16:20], "big"),
        height_px=int.from_bytes(asset[20:24], "big"),
    )
