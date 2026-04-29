"""Create the required 8-slide hackathon presentation PDF."""

from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_DIR = ROOT / "presentation_previews"
PDF_PATH = ROOT / "presentation.pdf"

W, H = 1920, 1080
MARGIN = 110

COLORS = {
    "bg": "#F6F8FB",
    "ink": "#18212F",
    "muted": "#5A6575",
    "teal": "#0F766E",
    "teal_dark": "#0B4F4A",
    "amber": "#E8A317",
    "coral": "#D95D47",
    "blue": "#2563A8",
    "line": "#D8E0EA",
    "white": "#FFFFFF",
    "soft": "#EAF3F1",
    "soft_amber": "#FFF2D6",
    "soft_blue": "#E9F0FA",
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    font_dir = Path("C:/Windows/Fonts")
    candidates = {
        "regular": ["segoeui.ttf", "arial.ttf"],
        "bold": ["segoeuib.ttf", "arialbd.ttf"],
        "semibold": ["seguisb.ttf", "arialbd.ttf"],
        "mono": ["consola.ttf", "cour.ttf"],
    }[name]
    for candidate in candidates:
        path = font_dir / candidate
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


F = {
    "eyebrow": font("semibold", 25),
    "title": font("bold", 72),
    "title_small": font("bold", 58),
    "subtitle": font("regular", 34),
    "body": font("regular", 31),
    "body_bold": font("semibold", 31),
    "label": font("semibold", 24),
    "small": font("regular", 21),
    "metric": font("bold", 82),
    "mono": font("mono", 27),
}


def text_size(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=face)
    return box[2] - box[0], box[3] - box[1]


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    face: ImageFont.ImageFont,
    fill: str,
    line_gap: int = 10,
    max_lines: int | None = None,
) -> int:
    approx = max(14, int(max_width / max(face.size * 0.52, 1)))
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        current = ""
        for word in words:
            trial = f"{current} {word}".strip()
            if text_size(draw, trial, face)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                if text_size(draw, word, face)[0] > max_width:
                    lines.extend(wrap(word, width=approx))
                    current = ""
                else:
                    current = word
        if current:
            lines.append(current)
    if max_lines:
        lines = lines[:max_lines]

    cursor = y
    for line in lines:
        draw.text((x, cursor), line, font=face, fill=fill)
        cursor += face.size + line_gap
    return cursor


def pill(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, color: str) -> None:
    pad_x, pad_y = 18, 9
    w, h = text_size(draw, label, F["label"])
    draw.rounded_rectangle((x, y, x + w + 2 * pad_x, y + h + 2 * pad_y), 22, fill=color)
    draw.text((x + pad_x, y + pad_y - 2), label, font=F["label"], fill=COLORS["white"])


def footer(draw: ImageDraw.ImageDraw, index: int) -> None:
    draw.line((MARGIN, H - 72, W - MARGIN, H - 72), fill=COLORS["line"], width=2)
    draw.text((MARGIN, H - 54), "BIS Standards Recommendation Engine", font=F["small"], fill=COLORS["muted"])
    marker = f"{index}/8"
    tw, _ = text_size(draw, marker, F["small"])
    draw.text((W - MARGIN - tw, H - 54), marker, font=F["small"], fill=COLORS["muted"])


def base_slide(index: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), COLORS["bg"])
    draw = ImageDraw.Draw(image)
    footer(draw, index)
    return image, draw


def title(draw: ImageDraw.ImageDraw, eyebrow: str, heading: str, sub: str = "") -> int:
    draw.text((MARGIN, 92), eyebrow.upper(), font=F["eyebrow"], fill=COLORS["teal"])
    y = draw_wrapped(draw, heading, MARGIN, 140, 1200, F["title_small"], COLORS["ink"], line_gap=12)
    if sub:
        y = draw_wrapped(draw, sub, MARGIN, y + 20, 1180, F["subtitle"], COLORS["muted"], line_gap=9)
    return y + 22


def slide_1() -> Image.Image:
    image = Image.new("RGB", (W, H), COLORS["ink"])
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, W, H), fill=COLORS["ink"])
    draw.polygon([(1150, 0), (1920, 0), (1920, 1080), (1330, 1080)], fill="#0F766E")
    draw.polygon([(1380, 0), (1920, 0), (1920, 780), (1510, 920)], fill="#E8A317")
    pill(draw, MARGIN, 110, "BIS x Sigma Squad AI Hackathon", COLORS["teal"])
    draw_wrapped(
        draw,
        "BIS Standards Recommendation Engine",
        MARGIN,
        205,
        980,
        F["title"],
        COLORS["white"],
        line_gap=14,
    )
    draw_wrapped(
        draw,
        "Fast, offline discovery of building-material standards from SP 21.",
        MARGIN,
        450,
        920,
        F["subtitle"],
        "#D9E6E4",
        line_gap=10,
    )
    draw.text((MARGIN, 650), "Input", font=F["label"], fill="#A9C7C4")
    draw.text((MARGIN, 692), "product description", font=F["body_bold"], fill=COLORS["white"])
    draw.line((MARGIN + 360, 710, MARGIN + 520, 710), fill=COLORS["amber"], width=8)
    draw.text((MARGIN + 560, 650), "Output", font=F["label"], fill="#A9C7C4")
    draw.text((MARGIN + 560, 692), "top 3-5 BIS standards", font=F["body_bold"], fill=COLORS["white"])
    draw.text((MARGIN, H - 130), "Submission package: inference.py, retriever, local demo, public evaluation, presentation PDF", font=F["small"], fill="#BBD4D1")
    return image


def slide_2() -> Image.Image:
    image, draw = base_slide(2)
    y = title(draw, "Problem Statement", "MSEs lose time mapping products to applicable BIS standards")
    left = MARGIN
    draw_wrapped(draw, "The current discovery task is manual: read dense SP 21 summaries, identify the right product family, then select the exact IS code and part.", left, y, 780, F["body"], COLORS["ink"], 12)
    draw_wrapped(draw, "For small teams, that turns a compliance question into days of document search and interpretation.", left, y + 185, 760, F["body_bold"], COLORS["teal_dark"], 12)
    x0, y0 = 1060, 330
    steps = [("Describe", "33 grade OPC cement"), ("Search", "SP 21 summaries"), ("Recommend", "IS 269: 1989")]
    for i, (head, body) in enumerate(steps):
        yy = y0 + i * 145
        draw.rounded_rectangle((x0, yy, x0 + 620, yy + 92), 18, fill=COLORS["white"], outline=COLORS["line"], width=2)
        draw.text((x0 + 28, yy + 18), head, font=F["label"], fill=COLORS["teal"])
        draw.text((x0 + 190, yy + 18), body, font=F["body_bold"], fill=COLORS["ink"])
        if i < len(steps) - 1:
            draw.line((x0 + 310, yy + 102, x0 + 310, yy + 132), fill=COLORS["amber"], width=6)
    return image


def slide_3() -> Image.Image:
    image, draw = base_slide(3)
    y = title(draw, "Solution Overview", "A judge-ready retriever that only returns standards parsed from the official PDF")
    cols = [
        ("Parse", "Extract 574 standard summaries, titles, scopes, page references, and canonical IS IDs."),
        ("Index", "Build a compact JSON index from standard IDs, title fields, scope text, and summary text."),
        ("Retrieve", "Score every query with BM25 plus deterministic field and phrase boosts."),
        ("Return", "Write the required JSON with top 5 standards and measured latency."),
    ]
    x = MARGIN
    for i, (head, body) in enumerate(cols):
        w = 390
        draw.rounded_rectangle((x, y + 55, x + w, y + 430), 18, fill=COLORS["white"], outline=COLORS["line"], width=2)
        draw.rectangle((x, y + 55, x + w, y + 70), fill=[COLORS["teal"], COLORS["blue"], COLORS["amber"], COLORS["coral"]][i])
        draw.text((x + 28, y + 102), head, font=F["title_small"], fill=COLORS["ink"])
        draw_wrapped(draw, body, x + 30, y + 208, w - 60, F["body"], COLORS["muted"], 10)
        x += w + 34
    draw_wrapped(
        draw,
        "Design choice: deterministic retrieval keeps the scoring path grounded in parsed SP 21 IDs.",
        MARGIN,
        870,
        1500,
        F["body_bold"],
        COLORS["teal_dark"],
        8,
    )
    return image


def slide_4() -> Image.Image:
    image, draw = base_slide(4)
    title(draw, "System Architecture", "One offline pipeline powers both judge execution and the demo UI")
    y = 340
    nodes = [
        ("dataset.pdf", "BIS SP 21 source"),
        ("build_index.py", "PDF parser"),
        ("standards.json", "574 records"),
        ("retriever.py", "hybrid scorer"),
        ("inference.py", "judge output"),
    ]
    x = 140
    for i, (head, body) in enumerate(nodes):
        draw.rounded_rectangle((x, y, x + 280, y + 150), 18, fill=COLORS["white"], outline=COLORS["line"], width=2)
        draw.text((x + 24, y + 30), head, font=F["body_bold"], fill=COLORS["ink"])
        draw.text((x + 24, y + 82), body, font=F["small"], fill=COLORS["muted"])
        if i < len(nodes) - 1:
            draw.line((x + 292, y + 75, x + 352, y + 75), fill=COLORS["teal"], width=7)
            draw.polygon([(x + 352, y + 75), (x + 330, y + 63), (x + 330, y + 87)], fill=COLORS["teal"])
        x += 342
    draw.rounded_rectangle((MARGIN, 660, W - MARGIN, 830), 20, fill=COLORS["soft_blue"], outline="#C8D7ED", width=2)
    draw.text((MARGIN + 34, 700), "Required judge command", font=F["label"], fill=COLORS["blue"])
    draw.text((MARGIN + 34, 748), "python inference.py --input hidden_private_dataset.json --output team_results.json", font=F["mono"], fill=COLORS["ink"])
    return image


def slide_5() -> Image.Image:
    image, draw = base_slide(5)
    title(draw, "Chunking & Retrieval Strategy", "Use standards as first-class records, not arbitrary page fragments")
    items = [
        ("Record-level chunks", "Each recommendation maps to one canonical standard ID, title, scope, summary, and source pages."),
        ("BM25 lexical core", "Good fit for exact product names, material families, standard numbers, grades, and part numbers."),
        ("Field-aware boosts", "Extra weight for title coverage, exact standard IDs, grade phrases, and material-specific terms."),
        ("No hallucination path", "The output list is selected from parsed SP 21 IDs only; the system cannot invent an IS code."),
    ]
    y = 310
    for i, (head, body) in enumerate(items):
        x = MARGIN + (i % 2) * 840
        yy = y + (i // 2) * 220
        color = [COLORS["teal"], COLORS["amber"], COLORS["blue"], COLORS["coral"]][i]
        draw.ellipse((x, yy + 8, x + 34, yy + 42), fill=color)
        draw.text((x + 56, yy), head, font=F["body_bold"], fill=COLORS["ink"])
        draw_wrapped(draw, body, x + 56, yy + 52, 675, F["body"], COLORS["muted"], 9)
    return image


def slide_6() -> Image.Image:
    image, draw = base_slide(6)
    title(draw, "Demo Highlights", "The same retriever serves CLI judging, API responses, and a local UI")
    query = "White Portland cement for architectural and decorative purposes"
    draw.rounded_rectangle((MARGIN, 310, W - MARGIN, 420), 18, fill=COLORS["white"], outline=COLORS["line"], width=2)
    draw.text((MARGIN + 28, 342), query, font=F["body_bold"], fill=COLORS["ink"])
    draw.line((W // 2, 452, W // 2, 520), fill=COLORS["amber"], width=8)
    draw.polygon([(W // 2, 530), (W // 2 - 18, 505), (W // 2 + 18, 505)], fill=COLORS["amber"])
    results = [
        ("1", "IS 8042: 1989", "White Portland cement"),
        ("2", "IS 8041: 1990", "Rapid hardening Portland cement"),
        ("3", "IS 269: 1989", "33 grade ordinary Portland cement"),
    ]
    y = 560
    for rank, std, label in results:
        draw.rounded_rectangle((MARGIN, y, W - MARGIN, y + 90), 16, fill=COLORS["white"], outline=COLORS["line"], width=2)
        draw.text((MARGIN + 28, y + 24), rank, font=F["body_bold"], fill=COLORS["teal"])
        draw.text((MARGIN + 90, y + 24), std, font=F["body_bold"], fill=COLORS["ink"])
        draw.text((MARGIN + 420, y + 24), label, font=F["body"], fill=COLORS["muted"])
        y += 108
    return image


def slide_7() -> Image.Image:
    image, draw = base_slide(7)
    title(draw, "Evaluation Results", "Public set results exceed all automated targets")
    metrics = [
        ("100%", "Hit Rate @3", "target >80%"),
        ("1.000", "MRR @5", "target >0.7"),
        ("0.05s", "Avg latency", "target <5s"),
    ]
    x = MARGIN
    for value, label, target in metrics:
        draw.text((x, 360), value, font=F["metric"], fill=COLORS["teal_dark"])
        draw.text((x, 465), label, font=F["body_bold"], fill=COLORS["ink"])
        draw.text((x, 510), target, font=F["small"], fill=COLORS["muted"])
        draw.line((x, 565, x + 420, 565), fill=COLORS["amber"], width=8)
        x += 560
    draw_wrapped(
        draw,
        "Measured by running the organizers' eval_script.py against data/public/public_test_set.json. Hidden set performance depends on the private query distribution, but the scoring path is deterministic and offline.",
        MARGIN,
        690,
        1500,
        F["body"],
        COLORS["muted"],
        11,
    )
    return image


def slide_8() -> Image.Image:
    image, draw = base_slide(8)
    title(draw, "Impact on MSEs", "Compliance discovery becomes guided search in seconds")
    impacts = [
        ("Speed", "Immediate standard shortlist for product planning and documentation."),
        ("Trust", "Recommendations are traceable to official SP 21 summaries and page references."),
        ("Reproducibility", "Offline repo runs on standard hardware with one judge command."),
    ]
    y = 350
    for i, (head, body) in enumerate(impacts):
        color = [COLORS["teal"], COLORS["blue"], COLORS["coral"]][i]
        draw.rectangle((MARGIN, y + 8, MARGIN + 18, y + 110), fill=color)
        draw.text((MARGIN + 46, y), head, font=F["title_small"], fill=COLORS["ink"])
        draw_wrapped(draw, body, MARGIN + 46, y + 80, 1250, F["body"], COLORS["muted"], 10)
        y += 170
    draw.rounded_rectangle((MARGIN, 865, W - MARGIN, 940), 18, fill=COLORS["soft"], outline="#C9DED9", width=2)
    draw.text((MARGIN + 28, 887), "Team: BIS Standards Recommendation Engine Team | Acknowledgement: BIS SP 21 dataset and organizer-provided evaluation assets", font=F["small"], fill=COLORS["teal_dark"])
    return image


def main() -> None:
    PREVIEW_DIR.mkdir(exist_ok=True)
    slides = [slide_1(), slide_2(), slide_3(), slide_4(), slide_5(), slide_6(), slide_7(), slide_8()]
    for index, slide in enumerate(slides, start=1):
        slide.save(PREVIEW_DIR / f"slide_{index:02d}.png", optimize=True)
    slides[0].save(PDF_PATH, "PDF", resolution=150.0, save_all=True, append_images=slides[1:])
    print(f"Wrote {PDF_PATH}")
    print(f"Wrote previews to {PREVIEW_DIR}")


if __name__ == "__main__":
    main()
