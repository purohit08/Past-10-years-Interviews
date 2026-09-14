# RFQ Copilot — Prompt-Driven RFQ Generation, Extraction & Vendor Comparison

A working AI prototype for a marketing-services procurement workflow:

**RFQ Generation → Vendor Response Input/Upload → Exception Guard → Extraction Agent → Comparison Agent → Buyer-Facing UI**

All outputs are generated dynamically by Claude from the actual inputs at runtime. Nothing is hardcoded.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...                  # Windows: set ANTHROPIC_API_KEY=...
streamlit run app.py
```

Optional: `export ANTHROPIC_MODEL=claude-sonnet-4-5` (default). If the env var key is not set, the sidebar accepts the key directly.

## Sample flow (matches the demo video)

1. **Screen 1 — RFQ Overview**: click *Generate RFQ*. The RFQ Generation Agent creates a realistic marketing-services RFQ (kids' nutrition drink launch, 8 line items LI-1…LI-8, timelines, commercial expectations, questionnaire, compliance).
2. **Screen 2 — Vendor Upload/Input**: click *Generate 3 vendor responses* for seeded messy test data (3 personas with known defect profiles), and/or upload/paste your own (txt, md, json, pdf, docx). Every input passes an **Exception Guard** that rejects wrong documents (invoices, NDAs, the RFQ itself) with a reason.
3. **Screen 3 — Extraction Review**: run extraction. Each vendor gets an evidence-backed structured extraction — flags first (severity-sorted), then line-item coverage vs the RFQ, pricing, commercial terms, timeline, compliance, experience, and ready-to-send clarification questions. One click drafts a clarification email per vendor.
4. **Screen 4 — Vendor Comparison**: the Comparison Agent consumes ONLY the extraction JSON (never raw text), first answers "are these vendors comparable yet?", then compares dimension-by-dimension with evidence, listing explicitly what CANNOT be compared and why. No fabricated overall score.
5. **Screen 5 — Prompt Trace / Prompt Pack**: every agent call is logged as input → prompt → model output, downloadable as JSON; the full prompt pack is browsable.

## Architecture

```
app.py        Streamlit UI + agent runners + trace logger (5 screens)
prompts.py    PROMPT PACK — 7 prompts, each documented with:
              what it does · why it is structured that way ·
              how it handles missing/unclear/conflicting data
```

Agents (all prompt-driven Claude calls):
1. RFQ Generation Agent
2. Vendor Response Generation Agent (includes controlled messy-data generation)
3. UI/UX Generation Agent (its output guided this app's screen design)
4. Extraction Agent
5. Comparison Agent
6. Clarification / Exception-handling Agent
7. Exception Guard (input validation)

## Hallucination control (design summary)

- **Evidence-first**: every material extracted value must carry a verbatim quote; no quote → no claim.
- **Closed status vocabulary**: STATED / MISSING / UNCLEAR / CONFLICTING / UNSUPPORTED makes "I don't know" a first-class answer.
- **Null over guess**: absence returns null + MISSING by rule.
- **Contradictions preserved**: both statements quoted; the agent never picks a side.
- **Input isolation**: the comparison agent never sees raw vendor text, so it cannot introduce ungrounded facts.
- **Comparability gate**: vendors with material gaps are marked NOT YET COMPARABLE instead of being force-ranked.

## Assumptions

- One RFQ per session; multi-RFQ management is out of scope for the prototype.
- PDF/DOCX parsing is text-layer only (no OCR) — the assignment states full OCR is not mandatory.
- Session state is in-memory (Streamlit session); persistence is a noted future improvement.
- Temperature 0.2 for extraction/comparison (consistency), 0.7 for vendor data generation (variety).

## Requirements

- Python 3.10+
- Anthropic API key
- Packages in `requirements.txt` (streamlit, anthropic, pypdf, python-docx)
