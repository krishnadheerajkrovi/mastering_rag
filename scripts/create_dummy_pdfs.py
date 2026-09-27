from __future__ import annotations

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "pdfs"

DOCUMENTS = {
    "acme_security_handbook.pdf": {
        "title": "Acme Security and Deployment Handbook",
        "subtitle": "Internal training fixture - version 3.2",
        "sections": [
            ("Production access", "Production access follows least privilege. Engineers receive time-limited access through the identity gateway after manager approval. Shared accounts are prohibited. All privileged sessions are logged and reviewed each week by the security operations team."),
            ("Deployment controls", "Every production deployment requires a passing CI pipeline, peer approval from a code owner, and a linked change ticket. High-risk changes also require security review. The release service signs artifacts and records the artifact digest before promotion."),
            ("Emergency changes", "An incident commander may authorize an emergency change when waiting would materially increase customer impact. The engineer must open a retrospective change ticket within one business day. A code owner reviews the change after service restoration."),
            ("Audit and rollback", "Deployment records, approvals, test results, and artifact digests are retained for thirteen months. Each service must document an automated rollback procedure. Teams exercise rollback procedures once per quarter and record the result."),
        ],
    },
    "acme_incident_response.pdf": {
        "title": "Acme Incident Response Guide",
        "subtitle": "Internal training fixture - revision September 2026",
        "sections": [
            ("Severity model", "SEV-1 incidents involve broad unavailability, confirmed sensitive-data exposure, or critical safety impact. SEV-2 incidents cause substantial degradation with a viable workaround. The on-call engineer declares severity and may revise it as evidence changes."),
            ("Roles", "The incident commander owns coordination and decisions. The operations lead investigates and mitigates. The communications lead publishes internal updates every thirty minutes during a SEV-1. A scribe maintains the timeline, decisions, and evidence links."),
            ("Containment and recovery", "Responders first protect people and data, then stabilize the service. Credentials suspected of compromise are rotated immediately. Recovery changes use the emergency deployment process and must preserve logs needed for investigation."),
            ("Learning review", "A blameless review is scheduled within five business days. It records customer impact, contributing conditions, detection gaps, and owned corrective actions. Action owners provide status updates until verification is complete."),
        ],
    },
    "northwind_research_notes.pdf": {
        "title": "Northwind Retrieval Evaluation Notes",
        "subtitle": "Synthetic research fixture",
        "sections": [
            ("Evaluation design", "The team evaluates retrieval with a fixed set of forty questions. Each question has chunk-level relevance labels from two reviewers. Disagreements are adjudicated before experiments begin. Recall at ten is the primary retrieval metric."),
            ("Hybrid retrieval", "Dense search retrieves paraphrases well, while lexical search reliably matches identifiers and exact policy terms. Reciprocal rank fusion combines the two ranked lists without requiring their raw scores to share a scale. The constant sixty produced stable results in the pilot."),
            ("Context enrichment", "A short prefix identifies the document, section, and purpose of each chunk. Prefixes are generated during indexing and embedded together with chunk text. Reviewers found that concise prefixes helped ambiguous passages without overwhelming their original wording."),
            ("Generation checks", "Answers are scored for correctness, citation completeness, and abstention when evidence is absent. A second model flags unsupported claims, but human sampling remains necessary because an automated judge can repeat the first model's mistakes."),
        ],
    },
}


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#64748B"))
    canvas.drawString(0.75 * inch, 0.45 * inch, "Synthetic document for the mastering_rag sample")
    canvas.drawRightString(7.75 * inch, 0.45 * inch, f"Page {doc.page}")
    canvas.restoreState()


def create_pdf(filename: str, spec: dict) -> None:
    path = OUTPUT / filename
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=HexColor("#123047"), alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=12, leading=16, textColor=HexColor("#475569"), alignment=TA_CENTER, spaceAfter=18))
    styles.add(ParagraphStyle(name="Section", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=16, textColor=HexColor("#0F766E"), spaceBefore=12, spaceAfter=10))
    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].fontSize = 11
    styles["BodyText"].leading = 16
    story = [Spacer(1, 1.2 * inch), Paragraph(spec["title"], styles["Cover"]), Paragraph(spec["subtitle"], styles["Subtitle"]), Spacer(1, 0.35 * inch)]
    summary = [["Purpose", "Safe, fictional content for local RAG demonstrations"], ["Topics", ", ".join(title for title, _ in spec["sections"])], ["Data class", "Synthetic / non-confidential"]]
    table = Table(summary, colWidths=[1.15 * inch, 4.9 * inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), HexColor("#E2E8F0")), ("TEXTCOLOR", (0, 0), (-1, -1), HexColor("#1E293B")), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (1, 0), (1, -1), "Helvetica"), ("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CBD5E1")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    story += [table, PageBreak()]
    for index, (heading, body) in enumerate(spec["sections"], start=1):
        story += [Paragraph(f"{index}. {heading}", styles["Section"]), Paragraph(body, styles["BodyText"]), Spacer(1, 0.24 * inch)]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, spec in DOCUMENTS.items():
        create_pdf(filename, spec)
        print(f"Created {OUTPUT / filename}")


if __name__ == "__main__":
    main()
