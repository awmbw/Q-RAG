"""Render the editable manuscript with ReportLab and inspect with Poppler afterward."""

import argparse
import re
from html import escape
from io import BytesIO
from pathlib import Path

from matplotlib import mathtext
from matplotlib.font_manager import FontProperties
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    LongTable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)


def inline(text):
    text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = escape(text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" color="#175e56">\1</a>', text
    )
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("paper/manuscript.md"))
    parser.add_argument(
        "--output", type=Path, default=Path("output/pdf/manuscript.pdf")
    )
    args = parser.parse_args()
    text = args.source.read_text()
    if any(
        marker in text
        for marker in [
            "Final numerical abstract",
            "Definitive tables and interpretation",
            "final conclusion follows",
        ]
    ):
        raise ValueError("Manuscript still contains unfinished result blocks")
    font_dir = Path("/usr/share/fonts/truetype/liberation")
    for name, file in [
        ("ResearchSerif", "LiberationSerif-Regular.ttf"),
        ("ResearchSerifBold", "LiberationSerif-Bold.ttf"),
        ("ResearchSerifItalic", "LiberationSerif-Italic.ttf"),
        ("ResearchSerifBoldItalic", "LiberationSerif-BoldItalic.ttf"),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(font_dir / file)))
    pdfmetrics.registerFontFamily(
        "ResearchSerif",
        normal="ResearchSerif",
        bold="ResearchSerifBold",
        italic="ResearchSerifItalic",
        boldItalic="ResearchSerifBoldItalic",
    )
    body = ParagraphStyle(
        "ResearchBody",
        fontName="ResearchSerif",
        fontSize=10.5,
        leading=14.2,
        spaceAfter=7,
    )
    title = ParagraphStyle(
        "ResearchTitle",
        parent=body,
        fontName="ResearchSerifBold",
        fontSize=19,
        leading=23,
        spaceAfter=14,
    )
    heading = ParagraphStyle(
        "ResearchHeading",
        parent=body,
        fontName="ResearchSerifBold",
        fontSize=13,
        leading=16,
        spaceBefore=13,
        spaceAfter=7,
        keepWithNext=True,
    )
    subheading = ParagraphStyle(
        "ResearchSubheading", parent=heading, fontSize=11, leading=14
    )
    cell = ParagraphStyle(
        "ResearchCell", parent=body, fontSize=8, leading=10, spaceAfter=0
    )
    small = ParagraphStyle("ResearchSmall", parent=body, fontSize=8.5, leading=11)
    code = ParagraphStyle(
        "ResearchCode", fontName="Courier", fontSize=7.5, leading=10, spaceAfter=8
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(args.output),
        pagesize=(8.5 * inch, 11 * inch),
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title="An Encoding-Aware Evaluation of Sparse QAOA Context Selection for Multi-Hop RAG",
        author="Q-RAG research project",
    )
    story = []
    lines = text.splitlines()
    i = 0

    def equation(latex):
        stream = BytesIO()
        mathtext.math_to_image(
            "$" + latex + "$",
            stream,
            prop=FontProperties(size=11),
            dpi=240,
            format="png",
            color="black",
        )
        stream.seek(0)
        image = PILImage.open(stream)
        w, h = image.size
        width = w * 72 / 240
        height = h * 72 / 240
        scale = min(1, doc.width / width)
        stream.seek(0)
        flow = Image(stream, width=width * scale, height=height * scale)
        flow.hAlign = "CENTER"
        return flow

    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("<!--"):
            i += 1
            continue
        if line == "$$":
            expression = []
            i += 1
            while i < len(lines) and lines[i].strip() != "$$":
                expression.append(lines[i].strip())
                i += 1
            group = [Spacer(1, 5), equation(" ".join(expression)), Spacer(1, 10)]
            if (
                story
                and isinstance(story[-1], Paragraph)
                and story[-1].getPlainText().endswith(":")
            ):
                group.insert(0, story.pop())
            story.append(KeepTogether(group))
            i += 1
            continue
        if line.startswith("```"):
            content = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                content.append(lines[i])
                i += 1
            story.append(Preformatted("\n".join(content), code))
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                values = [v.strip() for v in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", v) for v in values):
                    rows.append([Paragraph(inline(v), cell) for v in values])
                i += 1
            count = len(rows[0])
            first = 0.31 * doc.width if count > 3 else 0.48 * doc.width
            widths = [first] + [(doc.width - first) / (count - 1)] * (count - 1)
            headers = [p.getPlainText() for p in rows[0]]
            proportions = None
            if count == 6:
                proportions = [0.17, 0.28, 0.09, 0.11, 0.17, 0.18]
            elif count == 7:
                proportions = [0.13, 0.10, 0.07, 0.22, 0.14, 0.14, 0.20]
            elif count == 4:
                proportions = [0.17, 0.47, 0.13, 0.23]
            elif count == 5 and headers[1] == "Method":
                proportions = (
                    [0.25, 0.31, 0.12, 0.16, 0.16]
                    if headers[0] == "Dataset / generator"
                    else [0.15, 0.31, 0.18, 0.18, 0.18]
                )
            elif count == 5 and headers[1] == "Budget":
                proportions = [0.28, 0.12, 0.07, 0.23, 0.30]
            elif count == 5 and headers[0] == "Candidates":
                proportions = [0.13, 0.16, 0.25, 0.25, 0.21]
            if proportions:
                widths = [p * doc.width for p in proportions]
            table = LongTable(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f1ed")),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#46695e")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        (
                            "LINEBELOW",
                            (0, 1),
                            (-1, -1),
                            0.2,
                            colors.HexColor("#d7dfdc"),
                        ),
                    ]
                )
            )
            story.extend([table, Spacer(1, 9)])
            continue
        image = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line)
        if image:
            path = args.source.parent / image.group(2)
            w, h = PILImage.open(path).size
            story.append(
                KeepTogether(
                    [
                        Image(str(path), width=doc.width, height=doc.width * h / w),
                        Paragraph(inline(image.group(1)), small),
                        Spacer(1, 8),
                    ]
                )
            )
            i += 1
            continue
        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), title))
            i += 1
            continue
        if line.startswith("## "):
            if line[3:] == "References":
                story.append(PageBreak())
            story.append(Paragraph(inline(line[3:]), heading))
            i += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), subheading))
            i += 1
            continue
        if line.startswith("- "):
            story.append(Paragraph(inline(line[2:]), body, bulletText="-"))
            i += 1
            continue
        paragraph = [line]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not lines[i].startswith(("#", "|", "$$", "```", "<!--", "!["))
        ):
            paragraph.append(lines[i].strip())
            i += 1
        story.append(Paragraph(inline(" ".join(paragraph)), body))

    def page(canvas, document):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#bbc9c4"))
        canvas.line(
            doc.leftMargin, 0.47 * inch, 8.5 * inch - doc.rightMargin, 0.47 * inch
        )
        canvas.setFont("ResearchSerif", 8)
        canvas.setFillColor(colors.HexColor("#486057"))
        canvas.drawString(
            doc.leftMargin,
            0.30 * inch,
            "Q-RAG | Encoding-aware context selection | Research draft",
        )
        canvas.drawRightString(
            8.5 * inch - doc.rightMargin, 0.30 * inch, str(document.page)
        )
        canvas.restoreState()

    doc.build(story, onFirstPage=page, onLaterPages=page)
    print("Rendered", args.output)


if __name__ == "__main__":
    main()
