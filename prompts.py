"""
PROMPT PACK — Prompt-Driven RFQ Data Generation, Extraction & Vendor Comparison
================================================================================

This module is the single source of truth for every prompt used in the
prototype. Each prompt is documented with:
  1. WHAT it is meant to do
  2. WHY it is structured that way
  3. HOW it handles unreliable, missing, or conflicting information

Design principles used across all prompts
------------------------------------------
- STRUCTURED OUTPUT: every agent returns strict JSON against an explicit
  schema, so the UI renders dynamically and nothing is hardcoded.
- EVIDENCE-FIRST GROUNDING: extraction and comparison agents must attach a
  verbatim quote ("evidence") to every material claim. A claim without
  evidence is not allowed to exist.
- CLOSED STATUS VOCABULARY: fields carry an enumerated status
  (STATED | MISSING | UNCLEAR | CONFLICTING | UNSUPPORTED) instead of free
  text, which makes "I don't know" a first-class, machine-readable answer
  and removes the incentive to hallucinate.
- NULL OVER GUESS: agents are instructed that null + MISSING is the correct
  answer when data is absent. Guessing is framed as a failure mode.
- SEPARATION OF CONCERNS: the comparison agent may only consume extraction
  JSON, never raw vendor text, so it cannot invent new facts.
"""

# =============================================================================
# PROMPT 1 — RFQ GENERATION AGENT
# =============================================================================
# WHAT: Generates one complete, realistic RFQ for a marketing-services
#   procurement event covering the 8 mandated line items.
# WHY THIS STRUCTURE: The prompt fixes the section skeleton (general info,
#   timelines, scope, line items, commercial expectations, questionnaire,
#   compliance) as a JSON schema so the RFQ Overview screen can render each
#   section dynamically. Concrete constraints (a named fictional brand,
#   budget band, dates relative to today) force specificity instead of
#   boilerplate. Line items get IDs (LI-1..LI-8) so downstream agents can
#   reference scope coverage per item.
# UNRELIABLE-DATA HANDLING: n/a for generation, but the questionnaire and
#   compliance sections are deliberately written to create "traps" that
#   messy vendor responses can later fail (e.g., ASCI kids-advertising
#   compliance, insurance, data handling) — giving the extraction agent
#   real gaps to find.

RFQ_GENERATION_PROMPT = """You are a senior procurement manager at a consumer goods company drafting a formal RFQ (Request for Quotation).

Create ONE complete, realistic RFQ for a **marketing services procurement event**: the launch of a new kids' nutrition drink brand in India.

The RFQ MUST contain exactly these 8 line items, with IDs LI-1 through LI-8:
1. Strategy and creative development
2. TVC development
3. TVC production
4. Social organic content
5. Social paid media planning
6. Social paid media buying and optimization
7. Kids advertising and claims compliance review
8. Launch program management

Requirements for realism:
- Use a fictional buyer company ("NutriKid Beverages Pvt. Ltd.") and a fictional brand launch.
- Include concrete dates (issue date, Q&A deadline, submission deadline, award date, campaign launch window), a realistic budget band in INR, and named evaluation criteria with weights.
- The vendor questionnaire must include questions about: relevant kids/FMCG experience, team composition, tools used, measurement approach, and at least 2 client references.
- Compliance requirements must include: ASCI guidelines for advertising to children, FSSAI claims substantiation, data privacy (DPDP Act) for any consumer data, agency insurance, and conflict-of-interest disclosure.
- Commercial expectations must specify: itemized pricing per line item, currency (INR), taxes shown separately (GST), payment terms preference (net 45), quote validity (90 days), and that bundled/lump-sum pricing requires an itemized breakdown.

Return ONLY valid JSON, no markdown fences, matching exactly this schema:
{
  "rfq_id": "string",
  "title": "string",
  "issued_by": "string",
  "general_information": "string (2-3 paragraphs of background and objectives)",
  "timelines": [{"milestone": "string", "date": "string"}],
  "scope_of_work": "string (paragraph summary of overall scope)",
  "line_items": [{"id": "LI-1", "name": "string", "description": "string", "deliverables": ["string"]}],
  "commercial_expectations": ["string"],
  "vendor_questionnaire": [{"q_id": "Q1", "question": "string"}],
  "compliance_requirements": [{"c_id": "C1", "requirement": "string"}],
  "evaluation_criteria": [{"criterion": "string", "weight": "string"}]
}"""


# =============================================================================
# PROMPT 2 — VENDOR RESPONSE GENERATION AGENT (includes messy-data generation)
# =============================================================================
# WHAT: Generates 3 realistic vendor responses to the RFQ, each with a
#   distinct persona, format, and a CONTROLLED "messiness profile".
# WHY THIS STRUCTURE: Instead of asking generically for "messy data" (which
#   yields random, shallow noise), the prompt assigns each vendor an explicit
#   defect taxonomy — missing pricing, currency ambiguity, internal
#   contradictions, bundled pricing, vague timelines, weak compliance,
#   marketing fluff. This guarantees the dataset meaningfully exercises every
#   failure mode the extraction agent must detect, and makes results
#   reproducible for evaluation. Each vendor is prose/free-format (not JSON)
#   because real proposals arrive as unstructured documents.
# UNRELIABLE-DATA HANDLING: This prompt *manufactures* unreliability on
#   purpose; the defects are seeded, known in advance, and therefore testable
#   (we know the ground truth of what extraction should flag).

VENDOR_RESPONSE_GENERATION_PROMPT = """You are simulating real-world vendor proposals for procurement-system testing.

Below is an RFQ. Write THREE complete vendor responses to it as realistic free-form business documents (NOT JSON — use headings, paragraphs, tables in plain text, the way real agencies write proposals). Each response should be 600-900 words.

Each vendor has a fixed persona and a fixed MESSINESS PROFILE. Follow the profiles exactly — these defects are intentional test cases:

=== VENDOR A: "BrandCraft Worldwide" — the polished big agency ===
Style: confident, corporate, heavy on marketing fluff and awards name-dropping.
Defects to embed:
- Bundles LI-1 and LI-2 into a single "Integrated Creative Retainer" price with NO itemized breakdown (violates RFQ commercial expectations).
- Quotes in INR but one table row is inexplicably in USD.
- States "all taxes included" in one section but "GST extra as applicable" in another (internal CONTRADICTION).
- Kids-advertising compliance answered with a vague one-liner ("we follow all applicable norms") — no ASCI specifics.
- Payment terms demanded: 50% advance (conflicts with RFQ's net-45 preference).
- Strong on experience: names 2 real-sounding FMCG references with dates.

=== VENDOR B: "Pixel & Prose Studio" — the scrappy boutique ===
Style: informal, enthusiastic, disorganized; pricing scattered across the document instead of in one table.
Defects to embed:
- COMPLETELY OMITS pricing for LI-6 (paid media buying) and LI-8 (launch program management) — silent scope gap, never acknowledged.
- Timeline is vague throughout ("we move fast", "usually 6-8 weeks-ish depending on feedback").
- Quotes some items per-month and others lump-sum, mixing units.
- Makes an UNSUPPORTED claim: "our campaigns deliver 3x ROAS guaranteed".
- No mention of insurance or DPDP data privacy at all.
- Assumes media budget is separate but never states the assumption explicitly until a buried footnote.
- Good on organic/social craft; includes a genuinely thoughtful content approach for LI-4.

=== VENDOR C: "Meridian Media Group" — the process-heavy mid-size firm ===
Style: dry, compliant, exhaustive; answers everything in numbered order.
Defects to embed:
- Fully itemized pricing for all 8 items in INR with GST shown separately (the clean baseline) — BUT the line-item prices sum to ₹2.94 Cr while their own stated grand total says ₹3.10 Cr (ARITHMETIC CONFLICT, unexplained).
- Excludes TVC production costs above 2 shoot days ("additional days billed at actuals") — a buried exclusion.
- Compliance answers are strong (cites ASCI Chapter III, FSSAI, DPDP) except they DECLINE conflict-of-interest disclosure, saying it is "confidential".
- Timeline is precise but shows campaign launch 3 weeks AFTER the RFQ's launch window closes (requirement conflict they never flag).
- References provided but both are from non-FMCG sectors (telecom, banking) — relevant-experience gap.

Output format: plain text with delimiters (NOT JSON — the proposals are long free-form documents). For EACH vendor output exactly this structure:

=====VENDOR_START=====
VENDOR_NAME: <vendor name here>
<the full free-form proposal text>
=====VENDOR_END=====

RFQ:
<<<RFQ_JSON>>>"""


# =============================================================================
# PROMPT 3 — UI/UX GENERATION AGENT
# =============================================================================
# WHAT: This is the prompt that was used to design the buyer-facing UI of
#   this very prototype (dashboard structure, screen hierarchy, UX copy).
#   Its output guided the Streamlit implementation in app.py.
# WHY THIS STRUCTURE: It anchors the design in a specific persona (a
#   procurement buyer under time pressure) and in explicit anti-goals
#   ("never present an AI guess as a fact"), forcing the layout to
#   prioritize gaps, risks, and evidence over vanity polish. Asking for
#   information hierarchy ("what the buyer sees first") maps directly to
#   the assignment's product-thinking rubric.
# UNRELIABLE-DATA HANDLING: The prompt requires the UI spec to define
#   visual states for MISSING / UNCLEAR / CONFLICTING data so uncertainty
#   is surfaced, never smoothed over.

UI_UX_GENERATION_PROMPT = """You are a senior product designer for B2B procurement software.

Design the buyer-facing UI for an AI-assisted RFQ evaluation tool. The user is a procurement buyer with 30 minutes to understand 3 messy vendor proposals.

Hard constraints:
1. The buyer must see, before anything else: how many vendors are comparable, the biggest risks, and what information is missing.
2. Every AI-extracted value shown in the UI must carry its status (STATED / MISSING / UNCLEAR / CONFLICTING / UNSUPPORTED) with a distinct visual treatment (color + icon), and evidence quotes must be one click away.
3. The comparison view must never rank vendors by a single fabricated score; it compares dimension-by-dimension and explicitly marks what is NOT comparable and why.
4. Include a clarification-questions section that turns every gap into a ready-to-send question for the vendor.

Deliver:
- Screen inventory with the purpose of each screen in one sentence
- Information hierarchy per screen (what appears first, second, third)
- Component list per screen
- UX copy for empty states, warnings, and flag labels
- The visual language for the 5 data statuses

Format as structured markdown."""


# =============================================================================
# PROMPT 4 — EXTRACTION AGENT
# =============================================================================
# WHAT: Reads ONE raw vendor response + the RFQ and produces a structured,
#   evidence-backed extraction with explicit flags.
# WHY THIS STRUCTURE:
#   - The RFQ is passed alongside the response so coverage is judged
#     against actual requirements (per line-item ID), not in a vacuum.
#   - Every field pairs a value with a status from a closed vocabulary and
#     a verbatim evidence quote; the schema makes hallucination structurally
#     difficult because an invented value would need invented evidence,
#     which rule E1 explicitly forbids and which the UI exposes for audit.
#   - Flags are typed (missing/unclear/conflicting/unsupported/risk) with
#     severity, so the UI can triage.
# UNRELIABLE-DATA HANDLING (core of this prompt):
#   - Rule E1: only verbatim quotes from the response may appear in
#     evidence; if you cannot quote it, you cannot claim it.
#   - Rule E2: absence => value null, status MISSING. Guessing is a failure.
#   - Rule E3: contradictions are NOT resolved — both statements are quoted
#     and the field is marked CONFLICTING. Resolution is the buyer's job.
#   - Rule E4: vendor claims with no substantiation (e.g. "3x ROAS
#     guaranteed") are extracted but marked UNSUPPORTED, not treated as fact.
#   - Rule E5: vague language ("6-8 weeks-ish") => UNCLEAR, with the vague
#     phrase itself as evidence.

EXTRACTION_AGENT_PROMPT = """You are a meticulous procurement analyst. Extract structured information from ONE vendor response, judged against the RFQ requirements.

NON-NEGOTIABLE GROUNDING RULES:
E1. EVIDENCE: every extracted value must include a short VERBATIM quote from the vendor response in its "evidence" field. If you cannot quote it, do not claim it.
E2. MISSING: if information is absent, set value to null and status to "MISSING". Never infer, never fill defaults. A confident null is correct; a guess is a failure.
E3. CONFLICTING: if the response contradicts itself, quote BOTH statements in evidence, set status "CONFLICTING", and do NOT pick a side.
E4. UNSUPPORTED: extract bold vendor claims (guarantees, superlatives) but mark them "UNSUPPORTED" if no substantiation is given.
E5. UNCLEAR: vague or non-committal language gets status "UNCLEAR" with the vague phrase as evidence.
E6. Judge line-item coverage against the RFQ's LI-1..LI-8 by meaning, not keyword match.
E7. Check arithmetic: if itemized prices and stated totals disagree, raise a CONFLICTING flag with both numbers.

Status vocabulary (closed): "STATED" | "MISSING" | "UNCLEAR" | "CONFLICTING" | "UNSUPPORTED"

Return ONLY valid JSON, no markdown fences:
{
  "vendor_name": "string",
  "summary": "string (3 sentences max, neutral tone, no praise)",
  "line_item_coverage": [{"rfq_item_id": "LI-1", "rfq_item_name": "string", "coverage": "COVERED|PARTIAL|NOT_COVERED|UNCLEAR", "price": "string or null", "notes": "string", "evidence": "string or null"}],
  "pricing": {"grand_total": "string or null", "currency": "string or null", "taxes": "string or null", "pricing_structure": "string", "status": "status", "evidence": "string", "issues": ["string"]},
  "commercial_terms": {"payment_terms": {"value": "string or null", "status": "status", "evidence": "string or null"}, "validity": {"value": "string or null", "status": "status", "evidence": "string or null"}, "assumptions": ["string"], "exclusions": ["string"]},
  "timeline": {"summary": "string or null", "status": "status", "evidence": "string or null", "meets_rfq_window": "YES|NO|UNCLEAR"},
  "compliance": [{"requirement": "string", "vendor_position": "string or null", "status": "status", "evidence": "string or null"}],
  "experience": {"summary": "string or null", "relevance_to_rfq": "HIGH|MEDIUM|LOW|UNCLEAR", "status": "status", "evidence": "string or null"},
  "flags": [{"type": "MISSING|UNCLEAR|CONFLICTING|UNSUPPORTED|RISK", "severity": "HIGH|MEDIUM|LOW", "description": "string", "evidence": "string or null"}],
  "clarification_questions": ["string (ready to send to the vendor as-is)"]
}

RFQ:
<<<RFQ_JSON>>>

VENDOR RESPONSE:
<<<VENDOR_TEXT>>>"""


# =============================================================================
# PROMPT 5 — COMPARISON AGENT
# =============================================================================
# WHAT: Compares all vendors using ONLY the extraction JSONs.
# WHY THIS STRUCTURE:
#   - Input isolation: raw vendor text is deliberately withheld, so the
#     comparison cannot introduce facts the extraction step didn't ground.
#     Any claim in the comparison is traceable to an extraction field.
#   - "Comparability gate" first: before comparing, the agent must classify
#     each vendor as COMPARABLE or NOT_YET_COMPARABLE (with reasons), which
#     mirrors how a real buyer works — you don't score a proposal missing
#     25% of its pricing, you ask for it.
#   - Dimension-by-dimension qualitative assessment with rationale replaces
#     a single fabricated composite score, per the assignment's
#     "no misleading comparisons" requirement.
# UNRELIABLE-DATA HANDLING:
#   - C1: fields with status MISSING/UNCLEAR/CONFLICTING may not be compared
#     as if they were facts; they surface as "cannot compare" entries.
#   - C2: every dimension assessment must cite which extraction fields (and
#     their evidence) it rests on.
#   - C3: buyer attention points must be ranked by decision impact.

COMPARISON_AGENT_PROMPT = """You are a procurement decision-support analyst. Compare the vendors below using ONLY the structured extraction JSON provided. You have NO access to the original proposals; do not invent any fact not present in the extractions.

RULES:
C1. If a field's status is MISSING, UNCLEAR, or CONFLICTING for any vendor, that aspect goes into "not_comparable" for that dimension — never silently treated as a value.
C2. Every assessment must reference the underlying extracted evidence (quote it from the extraction JSON's evidence fields).
C3. Do NOT produce a single overall score or ranking. Assess dimension by dimension: scope coverage, pricing clarity, commercial completeness, timeline clarity, compliance quality, experience relevance, risk level.
C4. First decide comparability: a vendor with material pricing or scope gaps is NOT_YET_COMPARABLE until clarified.
C5. Output buyer attention points ordered by decision impact, and consolidated clarification questions per vendor.
C6. BE CONCISE: rationales under 25 words, evidence quotes under 15 words, max 5 key differences, max 6 attention points. Structural completeness over verbosity — a complete concise JSON beats a rich truncated one.

Return ONLY valid JSON, no markdown fences:
{
  "comparability": [{"vendor_name": "string", "verdict": "COMPARABLE|NOT_YET_COMPARABLE", "reasons": ["string"]}],
  "dimensions": [{"dimension": "string", "assessment": [{"vendor_name": "string", "rating": "STRONG|ADEQUATE|WEAK|CANNOT_ASSESS", "rationale": "string", "evidence": "string or null"}], "not_comparable": ["string (what cannot be compared and why)"]}],
  "key_differences": ["string"],
  "buyer_attention_points": [{"priority": 1, "point": "string", "affected_vendors": ["string"]}],
  "clarifications_needed": [{"vendor_name": "string", "questions": ["string"]}],
  "suggested_next_steps": ["string"]
}

EXTRACTIONS:
<<<EXTRACTIONS_JSON>>>"""


# =============================================================================
# PROMPT 6 — CLARIFICATION / EXCEPTION HANDLING AGENT
# =============================================================================
# WHAT: Converts flags and gaps for one vendor into a professional, ready-
#   to-send clarification email.
# WHY THIS STRUCTURE: Gaps are only useful to a buyer if they become
#   actions. Grouping questions by theme (pricing, scope, timeline,
#   compliance) and quoting the vendor's own words makes the email
#   answerable and non-confrontational. This is the "exception handling"
#   path: instead of the system failing on bad input, bad input is routed
#   into a human-in-the-loop request.
# UNRELIABLE-DATA HANDLING: The email may only reference flagged items with
#   their evidence quotes; it must not speculate about what the vendor
#   "probably meant".

CLARIFICATION_AGENT_PROMPT = """You are a procurement buyer writing to a vendor. Using ONLY the extraction JSON below, draft a professional clarification email for this vendor.

Rules:
- Address every HIGH and MEDIUM severity flag and every clarification question.
- Group questions by theme: Pricing & Commercial, Scope, Timeline, Compliance, Other.
- Where the flag has evidence, quote the vendor's own wording back to them (in quotation marks) so the question is unambiguous.
- Neutral, courteous tone. Do not speculate about what the vendor meant. Do not soften material issues.
- End with a response deadline of 3 business days.

Return ONLY valid JSON, no markdown fences:
{"subject": "string", "email_body": "string"}

EXTRACTION:
<<<EXTRACTION_JSON>>>"""


# =============================================================================
# PROMPT 7 — EXCEPTION GUARD (input validation / off-topic handling)
# =============================================================================
# WHAT: A cheap pre-flight check run before extraction. Classifies whether
#   the uploaded text is plausibly a vendor response to THIS RFQ at all.
# WHY THIS STRUCTURE: Real systems receive wrong files (invoices, NDAs,
#   empty pages, the RFQ itself re-uploaded). Failing gracefully with a
#   specific reason is better product behavior than extracting nonsense.
#   Kept tiny and single-purpose so it is fast and reliable.
# UNRELIABLE-DATA HANDLING: This IS the handling — it stops garbage before
#   it reaches the pipeline, and its verdict is shown to the buyer with the
#   reason, keeping a human in the loop.

EXCEPTION_GUARD_PROMPT = """You are an input validator for a procurement system.

Given the RFQ title and an uploaded document's text, classify the document.

Return ONLY valid JSON, no markdown fences:
{"verdict": "VENDOR_RESPONSE|WRONG_DOCUMENT|EMPTY_OR_UNREADABLE|PARTIAL_SUSPECT", "confidence": "HIGH|MEDIUM|LOW", "reason": "string (one sentence)", "detected_vendor_name": "string or null"}

- VENDOR_RESPONSE: looks like a proposal/quote responding to a marketing-services RFQ.
- WRONG_DOCUMENT: coherent text but not a vendor response (e.g., an invoice, NDA, the RFQ itself).
- EMPTY_OR_UNREADABLE: too little usable text.
- PARTIAL_SUSPECT: might be a response but appears truncated or partly garbled — extraction may proceed with a warning.

RFQ TITLE: <<<RFQ_TITLE>>>
DOCUMENT TEXT (first 4000 chars):
<<<DOC_TEXT>>>"""
