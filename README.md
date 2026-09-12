# Web Intelligence Ingestion Pipeline (GraphOne / FrontierAtlas)

A production-oriented, asynchronous web intelligence ingestion pipeline engineered for the artificial intelligence and venture capital ecosystem. Built to acquire, normalize, correlate, and enrich multi-dimensional datasets across **Startups**, **Products**, **Research Papers (with live GitHub stars)**, **24-hour Fresh News**, and **24-hour Fresh Jobs**.

Developed for the **AI Engineer Demo Task** with a hard storage constraint of **< 1 GB local disk footprint** (actual footprint: ~3.0 MB).

---

## Table of Contents

1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [Trial vs. 500k+ Production Architecture](#2-trial-vs-500k-production-architecture)
3. [Pipeline Flow & Data Lifecycle](#3-pipeline-flow--data-lifecycle)
4. [Technology Stack](#4-technology-stack)
5. [Storage Strategy (< 1 GB Hard Limit)](#5-storage-strategy--1-gb-hard-limit)
6. [Installation & Setup](#6-installation--setup)
7. [Environment Configuration](#7-environment-configuration)
8. [CLI Execution & Ingestion Commands](#8-cli-execution--ingestion-commands)
9. [Source Strategy & Registry](#9-source-strategy--registry)
10. [Multi-Tier LLM Fallback Engine](#10-multi-tier-llm-fallback-engine)
11. [Context Overflow (413) & Rate Limit (429) Handling](#11-context-overflow-413--rate-limit-429-handling)
12. [Anti-Hallucination Governance](#12-anti-hallucination-governance)
13. [Deterministic 24-Hour Freshness Tracking](#13-deterministic-24-hour-freshness-tracking)
14. [Deterministic Entity Resolution & Mapping Log](#14-deterministic-entity-resolution--mapping-log)
15. [GitHub Dynamic Star Tracking](#15-github-dynamic-star-tracking)
16. [Google Sheets & CSV Mirror Output](#16-google-sheets--csv-mirror-output)
17. [Testing Suite & Quality Verification](#17-testing-suite--quality-verification)
18. [Storage Breakdown & Diagnostic Audit](#18-storage-breakdown--diagnostic-audit)
19. [Anti-Bot Navigation Strategy](#19-anti-bot-navigation-strategy)
20. [Known Limitations & Production Roadmap](#20-known-limitations--production-roadmap)

---

## 1. Executive Summary & Problem Statement

GraphOne / FrontierAtlas is architecting the premier global Intelligence Graph for venture capital and AI ecosystems. This pipeline ingests entities across 5 distinct domains:
- **Startups**: Minimum 1,000 unique organizations with canonical entity names and headcount metadata.
- **Products**: Minimum 1,000 unique tools/models with canonical vendor mapping and standardized pricing tiers (`FREE`, `FREEMIUM`, `PAID`, `ENTERPRISE`).
- **Research Papers**: Minimum 1,000 unique arXiv papers correlated with their code repositories and live GitHub star metrics.
- **News Signals**: Monitored across 5 top-tier AI publications, strictly verified to be published within the previous 24 hours.
- **Job Signals**: Monitored across 5 distinct remote AI job boards, strictly verified to be published within the previous 24 hours.
- **Entity Mapping Log**: Auditable traceability matrix mapping raw noisy strings to canonical forms with confidence scores and provenance URLs.

---

## 2. Trial vs. 500k+ Production Architecture

We explicitly separate the **3-Day Local Trial Implementation** from the **500,000+ Production Target Architecture**:

| Architectural Dimension | 3-Day Local Trial (Implemented) | 500k+ Production Target (Documented) |
| :--- | :--- | :--- |
| **Concurrency Model** | `asyncio` + `aiohttp.ClientSession` with `Semaphore(15)` | Distributed Ray / Celery workers on Kubernetes with KEDA autoscaling |
| **Message Ingestion** | In-memory async streaming queues | Apache Kafka (partitioned by domain hash) + Redis Streams |
| **Persistence Layer** | Compact SQLite in WAL mode (~2.5 MB footprint) | Sharded PostgreSQL 16 + Citus with unique hash constraints |
| **Lakehouse / Raw Storage** | Zero raw HTML stored; ephemeral streaming buffers | MinIO / AWS S3 Glacier Lakehouse with 7-day lifecycle TTL |
| **Relationship Mapping** | Relational foreign keys + indexed hash constraints | Neo4j / Amazon Neptune Graph DB + `pgvector` for semantic embeddings |
| **LLM Orchestration** | Gemini Flash -> Groq Llama 3.1 -> DeepSeek Fallback | Self-hosted vLLM inference mesh with commercial cloud fallback |

Full 3-page architecture specification is compiled in [architecture.pdf](file:///c:/NEW/PROGRAMMING/PROJECTS/demo-task/architecture.pdf).

---

## 3. Pipeline Flow & Data Lifecycle

```
    [Configured Source Registry (config/sources.yaml)]
                          │
                          ▼
            [Async HTTP Client (aiohttp)]
             Bounded Semaphore Concurrency
             Exponential Backoff + Full Jitter
                          │
                          ▼
             [Ephemeral Streaming Parser]
           (Zero Raw HTML Stored on Disk)
                          │
      ┌───────────────────┴───────────────────┐
      │                                       │
      ▼                                       ▼
[Structured Feeds / APIs]          [Messy Unstructured Web DOM]
(ArXiv, HF Models, Job APIs)                  │
      │                                       ▼
      │                             [HTML Noise Stripper]
      │                           (Scripts, CSS, Nav removed)
      │                                       │
      │                                       ▼
      │                             [LLM Orchestration]
      │                           Gemini -> Groq -> DeepSeek
      │                            413 Halve / 429 Backoff
      │                                       │
      └───────────────────┬───────────────────┘
                          │
                          ▼
            [Pydantic Schema Validation]
         (Strict Enums, Mandatory Source URL)
                          │
                          ▼
             [24-Hour Freshness Filter]
        (Strict UTC ISO-8601 Verification)
                          │
                          ▼
          [Deterministic Entity Resolution]
          Unicode -> Suffix Strip -> RapidFuzz
                          │
                          ▼
           [Normalized SQLite Database (WAL)]
                          │
                          ▼
            [Google Sheets & CSV Exporter]
               (6 Output Worksheets)
```

---

## 4. Technology Stack

- **Runtime & Core**: Python 3.11+, `asyncio`, `aiohttp`, `httpx`
- **Validation & Schemas**: `pydantic v2`, `pydantic-settings`
- **HTML Extraction & Parsing**: `beautifulsoup4`, `lxml`
- **Date Normalization**: `python-dateutil`, standard `email.utils`
- **Entity Resolution**: `rapidfuzz` (token sort ratio algorithm)
- **Persistence**: SQLite 3 with WAL journal mode (`synchronous=NORMAL`)
- **Export**: `gspread`, `google-auth`, standard `csv`
- **Documentation Engine**: `reportlab` (dynamic canvas compilation)
- **Testing**: `pytest`

---

## 5. Storage Strategy (< 1 GB Hard Limit)

The assignment mandates strict disk management:
- **Hard Limit**: < 1,000 MB
- **Target Footprint**: < 700 MB
- **Observed Actual Footprint**: **~3.0 MB** (< 0.5% of limit)

### Prevention Policies Enforced:
1. **Zero PDF Storage**: Paper metadata and abstracts are parsed from APIs; raw PDF binaries are never downloaded.
2. **Zero Screenshot / Profile Dumps**: Browser profiles, traces, and screenshots are strictly avoided.
3. **Streaming Ephemeral Memory**: Raw HTML/JSON responses exist in memory only during parsing, then garbage-collected immediately.
4. **Bounded Temp Directory**: Monitored via `src/utils/cleanup.py` with automatic eviction if temp space exceeds 150 MB.
5. **Database Compaction**: SQLite `PRAGMA temp_store=MEMORY` and `VACUUM` executed after runs.

---

## 6. Installation & Setup

### Prerequisites
- Python 3.11 or higher
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/GraphOne/intelligence-pipeline.git
cd demo-task

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install lightweight dependencies
pip install -r requirements.txt
```

---

## 7. Environment Configuration

Copy the sample environment file:
```bash
cp .env.example .env
```

Key environment variables:
```ini
# LLM Providers (Optional: system works in deterministic offline mode if blank)
GEMINI_API_KEY=
GROQ_API_KEY=
DEEPSEEK_API_KEY=

# Configurable Model Identifiers
GEMINI_MODEL=gemini-1.5-flash
GROQ_MODEL=llama-3.1-8b-instant
DEEPSEEK_MODEL=deepseek-chat

# GitHub Token (Optional: increases rate limits from 60/hr to 5,000/hr)
GITHUB_TOKEN=

# Google Sheets Output (Optional: exports to data/sheets_export/ if blank)
GOOGLE_SERVICE_ACCOUNT_JSON=
GOOGLE_SHEET_ID=

# Storage Safeguards
MAX_PROJECT_FOOTPRINT_MB=900
MAX_TEMP_STORAGE_MB=150
```

---

## 8. CLI Execution & Ingestion Commands

Execute the ingestion pipeline using the modular CLI:

```bash
# 1. Ingest Startups (>= 1,000 unique records)
python -m src.main --target startups --limit 1000

# 2. Ingest Products (>= 1,000 unique records)
python -m src.main --target products --limit 1000

# 3. Ingest Research Papers with GitHub stars (>= 1,000 unique records)
python -m src.main --target papers --limit 1000

# 4. Ingest Fresh AI News (5 feeds, guaranteed <= 24h old)
python -m src.main --target news

# 5. Ingest Fresh AI Jobs (5 job boards, guaranteed <= 24h old)
python -m src.main --target jobs

# Complete Single-Command Pipeline Execution
python -m src.main --all --export-csv

# Inspect Local Storage Footprint
python scripts/check_disk_usage.py

# Recompile 3-Page Architecture PDF
python scripts/generate_architecture_pdf.py
```

---

## 9. Source Strategy & Registry

All ingestion endpoints are defined declaratively in `config/sources.yaml`:

- **Startups**: GitHub AI Organizations Search (`api.github.com/search/users?q=type:org+ai`)
- **Products**: Hugging Face Models API (`huggingface.co/api/models?limit=1000`)
- **Research Papers**: Hugging Face Daily Papers API with arXiv correlation & GitHub code repositories
- **News (5 sources)**:
  1. *TechCrunch AI* (`techcrunch.com/category/artificial-intelligence/feed/`)
  2. *The Verge AI* (`theverge.com/rss/ai-artificial-intelligence/index.xml`)
  3. *Ars Technica AI* (`feeds.arstechnica.com/arstechnica/index`)
  4. *Engadget AI* (`engadget.com/rss.xml`)
  5. *SiliconANGLE AI* (`siliconangle.com/feed/`)
- **Jobs (5 sources)**:
  1. *RemoteOK AI* (`remoteok.com/api?tag=ai`)
  2. *Jobicy AI* (`jobicy.com/api/v2/remote-jobs?count=50&tag=ai`)
  3. *Remotive AI* (`remotive.com/api/remote-jobs?category=software-dev&search=AI`)
  4. *WeWorkRemotely* (`weworkremotely.com/categories/remote-programming-jobs.rss`)
  5. *Arbeitnow AI* (`arbeitnow.com/api/job-board-api`)

---

## 10. Multi-Tier LLM Fallback Engine

Unstructured text passes through an automated resilience chain:
```
[Input Content] -> [Gemini Flash] 
                       │ (429 / 5xx / Timeout)
                       ▼
                 [Groq Llama 3.1]
                       │ (429 / 5xx / Timeout)
                       ▼
                 [DeepSeek Chat]
                       │ (Unconfigured / Down)
                       ▼
         [Deterministic Heuristic Fallback]
```
- Telemetry monitors calls per provider, fallback events, and status codes.
- Structured output enforced via Pydantic schema validation.

---

## 11. Context Overflow (413) & Rate Limit (429) Handling

### HTTP 413 & Context Token Overflow:
- `html_cleaner.py` strips extraneous boilerplate.
- Token estimator (`estimate_tokens()`) verifies payload budget against `MAX_INPUT_CHARS`.
- If an API triggers HTTP 413, `reduce_payload(content, factor=0.5)` dynamically halves the content window and retries before escalating to secondary providers.

### HTTP 429 & Rate Limit Mitigation:
- Exponential backoff: $t = \min(t_{\max}, t_{\text{base}} \times 2^{\text{attempt}}) \times \text{uniform}(0.5, 1.5)$.
- Upstream `Retry-After` headers are parsed and respected as mandatory sleep intervals.
- `ConcurrencyManager` bounds active in-flight requests to prevent bursting provider rate limits.

---

## 12. Anti-Hallucination Governance

The assignment mandates strict disqualification penalties for hallucinated data. Our countermeasures:
1. **Deterministic-First Extraction**: Structured endpoints (arXiv IDs, RSS publication dates, GitHub API stars) are extracted deterministically without involving LLMs.
2. **Strict Schema Constraints**: Enums (`PricingModelEnum.FREE`, `FREEMIUM`, `PAID`, `ENTERPRISE`) reject speculative values.
3. **Null-on-Missing Policy**: Missing fields default to `None` / `null`; LLM prompts forbid fabrication.
4. **Mandatory Provenance**: Every record contains an immutable `source.url` and `collectedAt` timestamp.
5. **Auditing Snippets**: Unstructured extractions retain a bounded `< 500` character evidence excerpt for auditability.

---

## 13. Deterministic 24-Hour Freshness Tracking

Freshness validation follows a deterministic priority hierarchy:
1. RSS/Atom `pubDate` / `published`
2. JSON-LD / schema.org `datePublished`
3. OpenGraph `og:published_time`
4. HTML5 `<time datetime>`
5. Deterministic relative parser ("2 hours ago", "yesterday")

### Validation Rule:
`published_date >= (now - 24 hours)` and `published_date <= (now + 15 minutes)`. Stale records are strictly rejected.

---

## 14. Deterministic Entity Resolution & Mapping Log

Raw venture strings are resolved via `EntityResolver`:
1. **Unicode NFKD Normalization**: Decomposes accents and diacritics.
2. **Corporate Suffix Stripping**: Removes `Inc`, `LLC`, `Corp`, `Ltd`, `PBC`, `GmbH`, `AG`, `SAS`, `Labs`, `Technologies`.
3. **Exact Alias Matching**: Checks against 50+ canonical AI companies (e.g. OpenAI, Anthropic, Mistral AI, Google DeepMind, Hugging Face).
4. **Conservative Fuzzy Matching**: RapidFuzz `token_sort_ratio`. Thresholds:
   - $\ge 88.0\%$: Automatic canonicalization (`FUZZY_RAPIDFUZZ`)
   - $75.0\% - 87.9\%$: Flagged for human review
   - $< 75.0\%$: Retained as separate normalized entity to prevent false merges
5. **Entity Mapping Log**: All mappings are persisted to `entity_mappings` and exported to CSV/Sheets.

---

## 15. GitHub Dynamic Star Tracking

- `GitHubClient` extracts `owner/repo` from paper URLs.
- Queries GitHub API `/repos/{owner}/{repo}` to retrieve live `stargazers_count`.
- Employs an in-memory cache to prevent duplicate queries.
- Throttles requests gracefully when unauthenticated rate limits (60/hr) are approached.

---

## 16. Google Sheets & CSV Mirror Output

Produces 6 canonical output tabs:
1. `Startups` (>= 1,000 rows)
2. `Products` (>= 1,000 rows)
3. `Research Papers` (>= 1,000 rows, including GitHub stars)
4. `Jobs` (Verified <= 24h fresh)
5. `News` (Verified <= 24h fresh)
6. `Entity Mapping Log` (Raw vs. Canonical names)

If Google Service Account credentials are not provided, outputs are automatically written to `data/sheets_export/` as CSV files.

---

## 17. Testing Suite & Quality Verification

Run the test suite:
```bash
python -m pytest -v tests/
```

### Coverage (29 automated unit tests):
- `test_date_parser.py`: ISO parsing, RFC-2822, relative date parsing ("2 hours ago", "yesterday"), UTC normalization.
- `test_freshness.py`: Strict 24h filter verification, stale rejection, clock drift tolerance.
- `test_entity_resolution.py`: Normalization, exact alias matching, RapidFuzz scoring, false merge prevention.
- `test_chunking.py`: Token estimation, semantic paragraph splitting, 413 payload halving, HTML cleaner.
- `test_retry.py`: Exponential backoff math, jitter bounds, Retry-After parsing, async retry loop.
- `test_schemas.py`: Validation of all 5 Pydantic entity schemas and `schemaVersion` constraints.
- `test_crawler_concurrency.py`: Bounded semaphore concurrency, deduplication sets, URL canonicalization.

---

## 18. Storage Breakdown & Diagnostic Audit

Run the storage diagnostic tool:
```bash
python scripts/check_disk_usage.py
```

### Diagnostic Output:
```
============================================================
         LOCAL PROJECT DISK USAGE REPORT
============================================================
Project Directory    : C:\NEW\PROGRAMMING\PROJECTS\demo-task
Total Project Size   : 3.0 MB
Database Directory   : 2.43 MB
Temp Storage         : 0.0 MB
Cache Storage        : 0.0 MB
System Free Space    : 112.65 GB
------------------------------------------------------------
Compliance Check     : PASSED (< 1 GB HARD CEILING SATISFIED)
============================================================
```

---

## 19. Anti-Bot Navigation Strategy

1. **Official & Public APIs First**: Leverages stable REST endpoints (GitHub, Hugging Face, ArXiv, RemoteOK).
2. **Public Structured Feeds**: Utilizes RSS/Atom XML feeds with standard headers.
3. **Respectful Request Rates**: Throttles concurrency (`MAX_CONCURRENCY=15`) with connection reuse.
4. **No Unauthorized Bypasses**: Strictly avoids CAPTCHA cracking or illicit circumvention.
5. **Ephemeral Playwright Mode**: For JavaScript-heavy portals, Playwright contexts are short-lived, destroying browser state upon completion without profile bloat.

---

## 20. Known Limitations & Production Roadmap

1. **Unauthenticated GitHub Rate Limit**: Without `GITHUB_TOKEN`, GitHub limits requests to 60/hr. Configure `GITHUB_TOKEN` in `.env` for 5,000/hr.
2. **VentureBeat Anti-Bot (429)**: VentureBeat occasionally rate-limits RSS aggregators; our 5 other news feeds provide seamless failover.
3. **Distributed Scale-Out**: For 500k+ records, deploy Apache Kafka partitioning, distributed Celery worker pods on Kubernetes, and Citus-sharded PostgreSQL as documented in `architecture.pdf`.
