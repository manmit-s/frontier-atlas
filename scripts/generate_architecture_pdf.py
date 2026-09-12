import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
from reportlab.pdfgen import canvas

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_PDF = BASE_DIR / "architecture.pdf"

class NumberedCanvas(canvas.Canvas):
    """Canvas that computes total pages dynamically and prints headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        
        # Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(54, 750, "GraphOne / FrontierAtlas — System Architecture Specification")
            self.drawRightString(558, 750, "Confidential & Proprietary")
            self.setStrokeColor(colors.HexColor("#CBD5E0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "Production Ingestion Architecture — 500k+ Entity Scale")
        self.setStrokeColor(colors.HexColor("#CBD5E0"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        str(OUTPUT_PDF),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'Callout',
        parent=body_style,
        fontName='Helvetica-Oblique',
        textColor=colors.HexColor("#2C5282")
    )

    story = []

    # =========================================================================
    # PAGE 1: EXECUTIVE OVERVIEW, TRIAL VS PROD, 500K SCALE ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("GraphOne / FrontierAtlas Intelligence Ingestion Architecture", title_style))
    story.append(Paragraph("Technical Design Specification: Scaling from 3-Day Trial to 500,000+ Multi-Dimensional Entities", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

    story.append(Paragraph("1. System Paradigm: Trial Implementation vs. 500k+ Production Architecture", h1_style))
    story.append(Paragraph(
        "To satisfy the rigorous requirements of the assessment, we explicitly bifurcate the operational footprint between the <b>3-Day Local Trial</b> "
        "and the <b>Distributed Production Architecture</b>. The local trial operates under a hard storage budget of <b>&lt; 1 GB (target &lt; 700 MB)</b>, "
        "leveraging an in-memory streaming ingestion pipeline, zero raw HTML persistence, zero PDF storage, bounded SQLite indexing, and direct API adapters. "
        "Conversely, the production system is designed to acquire and continuously reconcile <b>500,000+ entities (lakhs of records)</b> across startups, "
        "products, research papers, jobs, and news without manual intervention.",
        body_style
    ))

    # Architecture Comparison Table
    table_data = [
        [Paragraph("<b>Component</b>", body_style), Paragraph("<b>3-Day Trial Implementation</b>", body_style), Paragraph("<b>500k+ Production Target Architecture</b>", body_style)],
        [Paragraph("<b>Concurrency</b>", body_style), Paragraph("asyncio + aiohttp Semaphore (15-20 conn)", body_style), Paragraph("Distributed Ray / Celery Workers on Kubernetes (HPA)", body_style)],
        [Paragraph("<b>Message Queue</b>", body_style), Paragraph("In-memory async Queue & Generator Streams", body_style), Paragraph("Apache Kafka (Partitioned Event Streams) + Redis", body_style)],
        [Paragraph("<b>Storage Layer</b>", body_style), Paragraph("WAL-compacted SQLite (< 5 MB footprint)", body_style), Paragraph("Sharded PostgreSQL 16 + Citus + MinIO S3 Lakehouse", body_style)],
        [Paragraph("<b>Intelligence Graph</b>", body_style), Paragraph("Relational Foreign Keys + SQLite Indices", body_style), Paragraph("Neo4j / Amazon Neptune + pgvector (Embedding Index)", body_style)],
        [Paragraph("<b>LLM Processing</b>", body_style), Paragraph("Gemini Flash -> Groq -> DeepSeek Fallback", body_style), Paragraph("vLLM Local Self-Hosted Mesh + Cloud Fallback Gateway", body_style)]
    ]
    t = Table(table_data, colWidths=[100, 190, 214])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1A202C")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. Scaling to 500,000+ Records Without Bottlenecks", h1_style))
    story.append(Paragraph(
        "Scaling data acquisition by orders of magnitude (from 1,000 to 500,000+ records) requires eliminating shared locks, decoupling discovery "
        "from extraction, and enforcing horizontal backpressure across all ingestion nodes:",
        body_style
    ))
    story.append(Paragraph("• <b>Distributed Frontier Coordinator:</b> A centralized Source Registry schedules periodic discovery jobs across millions of seed URLs. URL states are tracked in a partitioned Redis Bloom Filter (100M keys ~12MB RAM) combined with Kafka topic partitions keyed by domain hashes.", bullet_style))
    story.append(Paragraph("• <b>Stateless Async Scraping Workers:</b> Crawler pods run asynchronously using <code>aiohttp</code> for high-throughput HTTP/JSON endpoints and headless Chromium instances (Playwright Cluster) for dynamic DOM rendering. Workers scale dynamically via KEDA based on Kafka queue lag.", bullet_style))
    story.append(Paragraph("• <b>Zero-Accumulation Streaming Buffer:</b> Scraped HTML/text is streamed directly into an ephemeral pipeline. Bounded text segments are emitted to extraction queues; raw markup is dumped into S3/MinIO cold archival tier (lifecycle rule: 7 days) and immediately purged from worker memory.", bullet_style))
    story.append(Paragraph("• <b>Multi-Stage Parallel Ingestion:</b> Vertical-specific ingestion pipelines (Startups, Products, Papers, News, Jobs) execute independently on dedicated worker pools, guaranteeing that high-volume arXiv paper streams never starve real-time news monitors.", bullet_style))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: RESILIENT LLM INTEGRATION (413 & 429), HALLUCINATION PREVENTION
    # =========================================================================
    story.append(Paragraph("3. Resilient LLM Extraction Engine: Managing 413s & 429s", h1_style))
    story.append(Paragraph(
        "Large-scale LLM extraction fails when pipelines naively blast raw DOM trees into model endpoints. Our architecture employs a multi-tiered defense "
        "mechanism that simultaneously eliminates context overflows (HTTP 413) and rate limits (HTTP 429).",
        body_style
    ))

    story.append(Paragraph("A. Context Window Governance & HTTP 413 Payload Reduction", h2_style))
    story.append(Paragraph(
        "Web pages contain 70–90% noise (inline JavaScript, SVG assets, CSS style blocks, tracking pixels, cookie consent popups, and boilerplate footers). "
        "Before any content is forwarded to an LLM, it traverses the <b>Intelligent Content Reduction Pipeline</b>:",
        body_style
    ))
    story.append(Paragraph("1. <b>Deterministic DOM Stripping:</b> Removes all script, style, nav, footer, header, and cookie tags via parser-level AST decomposition.", bullet_style))
    story.append(Paragraph("2. <b>Whitespace Normalization & Density Extraction:</b> Collapses multiple blank lines and extracts only semantically dense article and metadata nodes.", bullet_style))
    story.append(Paragraph("3. <b>Token Budget Estimator:</b> Calculates token footprint (approx. 4 characters/token). If content exceeds <code>MAX_INPUT_CHARS</code> (12,000 chars ~ 3,000 tokens), it invokes semantic chunking across natural paragraph and sentence boundaries.", bullet_style))
    story.append(Paragraph("4. <b>Dynamic 413 Catch & Halve Strategy:</b> If an API returns HTTP 413 or payload-too-large, the orchestrator catches the exception, halves the payload window (<code>reduction_factor=0.5</code>), and retries with the compacted payload before escalating to secondary providers.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("B. Rate Limiting (HTTP 429), Backoff & Multi-Tier Provider Fallback", h2_style))
    story.append(Paragraph(
        "Commercial LLM providers enforce tight Requests-Per-Minute (RPM) and Tokens-Per-Minute (TPM) quotas. The pipeline deploys an adaptive fallback chain:",
        body_style
    ))

    # Flow Diagram / Steps
    flow_data = [
        [Paragraph("<b>Step 1: Primary Gateway</b>", body_style), Paragraph("<b>Step 2: Secondary Failover</b>", body_style), Paragraph("<b>Step 3: Tertiary Failover</b>", body_style), Paragraph("<b>Step 4: Deterministic Fallback</b>", body_style)],
        [
            Paragraph("<b>Gemini Flash</b><br/>High-throughput, low latency structured extraction with JSON mode.", body_style),
            Paragraph("<b>Groq (Llama 3.1)</b><br/>Triggered on Gemini 429, timeout, or service disruption.", body_style),
            Paragraph("<b>DeepSeek Chat</b><br/>Triggered if Groq exhausts retry budget or encounters 429.", body_style),
            Paragraph("<b>Rule Extractor</b><br/>Zero-hallucination heuristic parse to preserve pipeline continuity.", body_style)
        ]
    ]
    flow_table = Table(flow_data, colWidths=[126, 126, 126, 126])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 4))

    story.append(Paragraph("• <b>Exponential Backoff with Full Jitter:</b> Retries follow <i>t = min(t_max, t_base * 2^attempt) * uniform(0.5, 1.5)</i>. This desynchronizes thundering herd requests across concurrent scraping tasks.", bullet_style))
    story.append(Paragraph("• <b>Respect for Retry-After Headers:</b> When upstream providers specify a mandatory cooling-off period, the worker suspends execution for the exact duration before re-engaging.", bullet_style))

    story.append(Paragraph("C. Zero-Tolerance Hallucination Prevention", h2_style))
    story.append(Paragraph(
        "Hallucinated records disqualify venture intelligence graphs. To guarantee 100% data fidelity: "
        "<br/>1. <b>Strict Schema Contracts:</b> All extractions must validate against Pydantic models with constrained enums (e.g. <code>FREE, FREEMIUM, PAID, ENTERPRISE</code>). "
        "<br/>2. <b>Mandatory Source Provenance:</b> Every record retains its immutable <code>source.url</code> and <code>collectedAt</code> timestamp. "
        "<br/>3. <b>Null-on-Missing:</b> Missing data (e.g. employee count, pricing tier) is set strictly to <code>null</code>; speculative generation is forbidden. "
        "<br/>4. <b>Bounded Evidence Snippets:</b> For unstructured text, an auditing snippet of &lt;= 500 characters is preserved to verify provenance without disk bloating.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: FRESHNESS, ENTITY RESOLUTION, DATABASE & GRAPH STORAGE STRATEGY
    # =========================================================================
    story.append(Paragraph("4. Freshness Tracking & Distributed Idempotency", h1_style))
    story.append(Paragraph(
        "News and jobs require rigorous freshness guarantees (&lt;= 24 hours). The pipeline implements a <b>Deterministic Extraction Hierarchy</b>:",
        body_style
    ))
    story.append(Paragraph("1. <b>RSS/Atom Protocol Headers:</b> <code>pubDate</code>, <code>published</code>, <code>updated</code> tags parsed via RFC-2822/ISO-8601.", bullet_style))
    story.append(Paragraph("2. <b>Microdata & JSON-LD:</b> <code>datePublished</code>, <code>uploadDate</code> in schema.org structured scripts.", bullet_style))
    story.append(Paragraph("3. <b>OpenGraph Metadata:</b> <code>og:published_time</code> and <code>article:published_time</code> tags.", bullet_style))
    story.append(Paragraph("4. <b>Semantic DOM Tags:</b> HTML5 <code>&lt;time datetime='...'&gt;</code> attributes.", bullet_style))
    story.append(Paragraph("5. <b>Deterministic Relative Parsing:</b> Expressions like '2 hours ago' or 'yesterday' computed against UTC reference time.", bullet_style))
    story.append(Paragraph(
        "<b>Freshness Filter:</b> Any article or job published earlier than <code>now - 24 hours</code> is strictly rejected. A 15-minute future tolerance "
        "is enforced to accommodate server clock drift. "
        "<br/><b>Distributed Idempotency:</b> Each record computes a composite fingerprint: <code>SHA256(canonical_url + published_timestamp)</code>. "
        "In production, a distributed Redis set and PostgreSQL <code>ON CONFLICT DO NOTHING</code> clause prevent duplicate ingestion across worker nodes.",
        body_style
    ))

    story.append(Paragraph("5. Deterministic Entity Resolution Engine", h1_style))
    story.append(Paragraph(
        "Raw venture data is notoriously noisy (e.g. 'OpenAI, Inc.', 'Open AI', 'openai-org' all represent the same entity). The resolution pipeline operates as follows:",
        body_style
    ))
    story.append(Paragraph("• <b>Normalization Pipeline:</b> Unicode NFKD normalization -&gt; lowercase conversion -&gt; corporate suffix stripping (Inc, LLC, Corp, Ltd, PBC, GmbH, AG, SAS, Labs, Tech) -&gt; punctuation strip -&gt; whitespace collapse.", bullet_style))
    story.append(Paragraph("• <b>Exact Alias Matching:</b> Matches against a curated canonical dictionary of 50+ prominent AI companies and products (100% confidence).", bullet_style))
    story.append(Paragraph("• <b>Conservative RapidFuzz Scoring:</b> Employs <code>fuzz.token_sort_ratio</code>. Scores &gt;= 88.0% automatically canonicalize; scores between 75–87% are flagged for review; scores &lt; 75% retain distinct identity to avoid false merges.", bullet_style))
    story.append(Paragraph("• <b>Auditable Entity Mapping Log:</b> Every resolution records <code>raw_name</code>, <code>canonical_name</code>, <code>method</code>, <code>confidence</code>, and <code>source_url</code>.", bullet_style))

    story.append(Paragraph("6. Storage Strategy: Primary Database, Vector & Graph Storage", h1_style))
    story.append(Paragraph(
        "To map complex venture relationships across founders, companies, products, patents, and hiring trends at 500k+ scale:",
        body_style
    ))

    # Storage Comparison Table
    storage_table_data = [
        [Paragraph("<b>Storage Layer</b>", body_style), Paragraph("<b>Technology</b>", body_style), Paragraph("<b>Architectural Justification & Role</b>", body_style)],
        [
            Paragraph("<b>Primary Relational DB</b>", body_style),
            Paragraph("PostgreSQL 16 + Citus", body_style),
            Paragraph("ACID compliance, relational integrity, row-level idempotency via unique hash constraints, and horizontal sharding across millions of records.", body_style)
        ],
        [
            Paragraph("<b>Vector Semantic Index</b>", body_style),
            Paragraph("pgvector / Qdrant", body_style),
            Paragraph("Enables high-speed cosine similarity search across research paper abstracts, product descriptions, and news embeddings for semantic deduplication.", body_style)
        ],
        [
            Paragraph("<b>Intelligence Graph DB</b>", body_style),
            Paragraph("Neo4j / Amazon Neptune", body_style),
            Paragraph("Enables multi-hop graph traversals: <i>(Founder)-[:FOUNDED]->(Startup)-[:PRODUCES]->(Product)-[:IMPLEMENTS]->(ResearchPaper)</i>.", body_style)
        ]
    ]
    st = Table(storage_table_data, colWidths=[110, 110, 284])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#EDF2F7")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(st)
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Local Trial Compliance Note:</b> In our local implementation, SQLite in WAL mode delivers the exact normalized schema and unique constraints of PostgreSQL while consuming only ~3.0 MB of disk space, easily satisfying the &lt; 1 GB hard storage budget.", callout_style))

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Architecture PDF generated successfully at: {OUTPUT_PDF}")

if __name__ == "__main__":
    build_pdf()
