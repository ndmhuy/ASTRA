"""Pure-Python standalone SVG chart generators for the THPT benchmark report."""

from __future__ import annotations

from html import escape
from pathlib import Path

PALETTE = (
    "#2563EB",  # Blue (Hero / ASTRA Par)
    "#059669",  # Emerald (ASTRA Seq)
    "#D97706",  # Amber (Single-shot RAG)
    "#DC2626",  # Red (Naive Chat)
    "#7C3AED",  # Violet
    "#0891B2",  # Cyan
)


def _svg_wrap(width: int, height: int, title: str, body: list[str]) -> str:
    header = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
        "<style>",
        "text { font-family: 'Segoe UI', Arial, sans-serif; fill: #1F2937; }",
        ".title { font-size: 16px; font-weight: 700; }",
        ".subtitle { font-size: 12px; fill: #4B5563; }",
        ".axis { font-size: 11px; fill: #4B5563; }",
        ".val { font-size: 10px; font-weight: 600; fill: #111827; }",
        ".legend { font-size: 11px; }",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#FFFFFF" rx="8"/>',
    ]
    return "\n".join([*header, *body, "</svg>\n"])


def _truncate(text: str, limit: int = 34) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def render_hero_quality_bars_svg(rows: list[dict], out_path: Path, *, mode: str) -> Path:
    """Grouped bar chart comparing up to 4 runs across the 5 prioritized quality metrics."""
    selected = rows[:4]
    width, height = 920, 460
    left, right, top, bottom = 70, 30, 95, 95
    plot_w = width - left - right
    plot_h = height - top - bottom

    metrics = [
        ("template_rate", "1. Template"),
        ("math_rate", "2. Tính toán"),
        ("citation_rate", "3. Trích dẫn"),
        ("validator_rate", "4. Validator"),
        ("compliance_rate", "5. Compliance"),
    ]
    title = "So sánh 5 thước đo chất lượng ưu tiên"
    subtitle = (
        f"Chế độ: {mode.upper()} — Giá trị (%) tính trên tổng số ca chạy (ô mờ = Chưa chấm tay)"
    )

    body = [
        f'<text x="{left}" y="30" class="title">{escape(title)}</text>',
        f'<text x="{left}" y="50" class="subtitle">{escape(subtitle)}</text>',
    ]

    # Legend
    lx = left
    for idx, row in enumerate(selected):
        color = PALETTE[idx % len(PALETTE)]
        label = _truncate(row["label"], 30)
        body.append(f'<rect x="{lx}" y="62" width="12" height="12" fill="{color}" rx="2"/>')
        body.append(f'<text x="{lx + 17}" y="72" class="legend">{escape(label)}</text>')
        lx += max(150, len(label) * 6 + 34)
        if lx > width - 160:
            lx = left

    # Horizontal gridlines 0..100%
    for pct in (0, 25, 50, 75, 100):
        y = top + plot_h - (pct / 100.0) * plot_h
        body.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            'stroke="#E5E7EB" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="axis">{pct}%</text>'
        )

    group_w = plot_w / max(len(metrics), 1)
    n_series = max(len(selected), 1)
    bar_w = min(36.0, (group_w - 28.0) / n_series)

    for g_idx, (key, m_label) in enumerate(metrics):
        gx = left + g_idx * group_w
        cx = gx + group_w / 2.0
        body.append(
            f'<text x="{cx:.1f}" y="{top + plot_h + 24}" text-anchor="middle" class="axis">'
            f"{escape(m_label)}</text>"
        )
        start_x = cx - (n_series * bar_w) / 2.0
        for s_idx, row in enumerate(selected):
            val = row.get(key)
            bx = start_x + s_idx * bar_w + 2
            bw = max(8.0, bar_w - 4)
            color = PALETTE[s_idx % len(PALETTE)]
            if val is None:
                # Ungraded metric placeholder
                bh = 18.0
                by = top + plot_h - bh
                body.append(
                    f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                    'fill="#F3F4F6" stroke="#9CA3AF" stroke-dasharray="3,2" rx="2"/>'
                )
                body.append(
                    f'<text x="{bx + bw / 2:.1f}" y="{by - 4:.1f}" text-anchor="middle" '
                    'class="axis">N/A</text>'
                )
            else:
                pct = max(0.0, min(100.0, val * 100.0))
                bh = (pct / 100.0) * plot_h
                by = top + plot_h - bh
                body.append(
                    f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                    f'fill="{color}" rx="3"/>'
                )
                body.append(
                    f'<text x="{bx + bw / 2:.1f}" y="{by - 5:.1f}" text-anchor="middle" '
                    f'class="val">{pct:.0f}%</text>'
                )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_svg_wrap(width, height, title, body), encoding="utf-8")
    return out_path


def render_pareto_cost_quality_svg(
    rows: list[dict],
    out_path: Path,
    *,
    cost_target_vnd: float = 2_000.0,
    mode: str = "replay",
) -> Path:
    """Scatter plot: VND/exam (X) vs Overall Quality % (Y), bubble size = median latency."""
    width, height = 920, 460
    left, right, top, bottom = 75, 45, 78, 70
    plot_w = width - left - right
    plot_h = height - top - bottom

    max_cost = max([cost_target_vnd * 1.25, *(r.get("mean_cost_vnd", 0.0) for r in rows)])
    max_cost = max(max_cost, 100.0)
    max_lat = max([1.0, *(r.get("median_wall_seconds", 0.0) for r in rows)])

    title = "Biểu đồ Pareto: Chi phí (VNĐ/đề) vs Chất lượng tổng hợp (%)"
    subtitle = (
        f"Chế độ: {mode.upper()} — Góc trên bên trái là tối ưu "
        f"(rẻ ≤ {cost_target_vnd:,.0f} VNĐ & chất lượng cao; kích thước chấm = độ trễ)"
    )

    body = [
        f'<text x="{left}" y="30" class="title">{escape(title)}</text>',
        f'<text x="{left}" y="50" class="subtitle">{escape(subtitle)}</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" '
        'fill="#F9FAFB" stroke="#D1D5DB"/>',
    ]

    # Gridlines Y (0..100%)
    for pct in (0, 25, 50, 75, 100):
        y = top + plot_h - (pct / 100.0) * plot_h
        body.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            'stroke="#E5E7EB" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" class="axis">{pct}%</text>'
        )

    # Gridlines X (0..max_cost)
    for step in range(5):
        vnd = (max_cost * step) / 4.0
        x = left + (vnd / max_cost) * plot_w
        body.append(
            f'<line x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_h}" '
            'stroke="#E5E7EB" stroke-width="1"/>'
        )
        body.append(
            f'<text x="{x:.1f}" y="{top + plot_h + 20}" text-anchor="middle" class="axis">'
            f"{vnd:,.0f} đ</text>"
        )

    # Target cost vertical threshold
    tx = left + min(1.0, cost_target_vnd / max_cost) * plot_w
    body.append(
        f'<line x1="{tx:.1f}" y1="{top}" x2="{tx:.1f}" y2="{top + plot_h}" '
        'stroke="#059669" stroke-width="2" stroke-dasharray="6,4"/>'
    )
    body.append(
        f'<text x="{tx + 6:.1f}" y="{top + 16}" class="val" fill="#059669">'
        f"Mục tiêu ≤ {cost_target_vnd:,.0f} VNĐ</text>"
    )

    # Points
    for idx, row in enumerate(rows):
        color = PALETTE[idx % len(PALETTE)]
        vnd = row.get("mean_cost_vnd", 0.0)
        quality_pct = max(0.0, min(100.0, (row.get("composite_quality_rate") or 0.0) * 100.0))
        lat = row.get("median_wall_seconds", 0.0)
        x = left + (vnd / max_cost) * plot_w
        y = top + plot_h - (quality_pct / 100.0) * plot_h
        radius = 7.0 + 11.0 * (lat / max_lat)
        body.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" '
            f'fill="{color}" fill-opacity="0.78" stroke="#111827" stroke-width="1.2"/>'
        )
        anchor = "end" if x > left + plot_w * 0.72 else "start"
        dx = -radius - 6 if anchor == "end" else radius + 6
        label = f"{_truncate(row['label'], 26)} ({vnd:,.0f}đ, {quality_pct:.0f}%)"
        body.append(
            f'<text x="{x + dx:.1f}" y="{y + 4:.1f}" text-anchor="{anchor}" class="val">'
            f"{escape(label)}</text>"
        )

    body.append(
        f'<text x="{left + plot_w / 2:.1f}" y="{height - 18}" text-anchor="middle" class="axis">'
        "Chi phí ước tính chuẩn mỗi đề (VNĐ)</text>"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_svg_wrap(width, height, title, body), encoding="utf-8")
    return out_path


def render_latency_cost_breakdown_svg(
    rows: list[dict], out_path: Path, *, mode: str = "replay"
) -> Path:
    """Horizontal stacked bar splitting median API compute vs rate-limit wait seconds."""
    bar_h = 26
    row_gap = 14
    top, bottom = 84, 48
    left, right = 250, 130
    width = 920
    height = max(260, top + bottom + len(rows) * (bar_h + row_gap))
    plot_w = width - left - right

    max_s = max(
        [
            0.5,
            *(
                r.get("median_compute_seconds", 0.0) + r.get("median_wait_seconds", 0.0)
                for r in rows
            ),
        ]
    )

    title = "Phân tách thời gian sinh đề (API Compute vs Chờ 429) & Chi phí"
    subtitle = f"Chế độ: {mode.upper()} — Trung vị thời gian tính toán và thời gian chờ giới hạn"

    body = [
        f'<text x="24" y="30" class="title">{escape(title)}</text>',
        f'<text x="24" y="50" class="subtitle">{escape(subtitle)}</text>',
        '<rect x="24" y="60" width="12" height="12" fill="#2563EB" rx="2"/>',
        '<text x="41" y="70" class="legend">API Compute (s)</text>',
        '<rect x="165" y="60" width="12" height="12" fill="#F59E0B" rx="2"/>',
        '<text x="182" y="70" class="legend">Chờ Rate-Limit 429 (s)</text>',
    ]

    for idx, row in enumerate(rows):
        y = top + idx * (bar_h + row_gap)
        comp = row.get("median_compute_seconds", 0.0)
        wait = row.get("median_wait_seconds", 0.0)
        vnd = row.get("mean_cost_vnd", 0.0)
        comp_w = (comp / max_s) * plot_w
        wait_w = (wait / max_s) * plot_w
        body.append(
            f'<text x="{left - 10}" y="{y + 17}" text-anchor="end" class="axis">'
            f"{escape(_truncate(row['label'], 34))}</text>"
        )
        body.append(
            f'<rect x="{left}" y="{y}" width="{max(2.0, comp_w):.1f}" height="{bar_h}" '
            'fill="#2563EB" rx="3"/>'
        )
        if wait > 0:
            body.append(
                f'<rect x="{left + comp_w:.1f}" y="{y}" width="{max(2.0, wait_w):.1f}" '
                f'height="{bar_h}" fill="#F59E0B" rx="3"/>'
            )
        end_x = left + comp_w + wait_w + 8
        summary_txt = f"{comp:.2f}s + {wait:.2f}s | {vnd:,.0f} VNĐ"
        body.append(f'<text x="{end_x:.1f}" y="{y + 17}" class="val">{escape(summary_txt)}</text>')

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_svg_wrap(width, height, title, body), encoding="utf-8")
    return out_path
