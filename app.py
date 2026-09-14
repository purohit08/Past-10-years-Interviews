"""
RFQ Copilot — Prompt-Driven RFQ Generation, Extraction & Vendor Comparison
===========================================================================
Run:  streamlit run app.py
Env:  ANTHROPIC_API_KEY must be set (or entered in the sidebar).

Screens:
  1. RFQ Overview        — generate & view the RFQ (RFQ Generation Agent)
  2. Vendor Upload/Input — paste/upload responses, or generate messy test data
  3. Extraction Review   — evidence-backed extraction with flags per vendor
  4. Vendor Comparison   — dimension-by-dimension comparison + attention points
  5. Prompt Trace        — full prompt pack + live input→prompt→output traces

All AI outputs are produced dynamically from the inputs at runtime.
Nothing is hardcoded.
"""

import json
import os
import re
from datetime import datetime

import streamlit as st

import prompts as P

# ---------------------------------------------------------------------------
# Page config & light styling
# ---------------------------------------------------------------------------
st.set_page_config(page_title="RFQ Copilot", page_icon="📋", layout="wide")

st.markdown(
    """
    <style>
      .status-badge {display:inline-block;padding:2px 10px;border-radius:10px;
                     font-size:0.78rem;font-weight:600;margin-right:6px;}
      .s-STATED      {background:#e6f4ea;color:#1e7e34;}
      .s-MISSING     {background:#fdecea;color:#c0392b;}
      .s-UNCLEAR     {background:#fff8e1;color:#b8860b;}
      .s-CONFLICTING {background:#fde2e2;color:#8e2424;border:1px solid #e57373;}
      .s-UNSUPPORTED {background:#ede7f6;color:#5e35b1;}
      .evidence {border-left:3px solid #90a4ae;background:#f5f7f8;padding:6px 10px;
                 font-style:italic;font-size:0.85rem;color:#37474f;margin:4px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

STATUS_ICON = {
    "STATED": "✅", "MISSING": "🔴", "UNCLEAR": "🟡",
    "CONFLICTING": "⚠️", "UNSUPPORTED": "🟣",
    "COVERED": "✅", "PARTIAL": "🟠", "NOT_COVERED": "🔴",
    "STRONG": "🟢", "ADEQUATE": "🟡", "WEAK": "🟠", "CANNOT_ASSESS": "⚪",
}


def badge(status: str) -> str:
    s = (status or "UNCLEAR").upper()
    icon = STATUS_ICON.get(s, "•")
    return f'<span class="status-badge s-{s}">{icon} {s}</span>'


def evidence_block(text):
    if not text:
        return ""
    return f'<div class="evidence">“{text}”</div>'


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
def init_state():
    defaults = {
        "rfq": None,            # parsed RFQ dict
        "vendors": [],          # [{name, text, source, guard}]
        "extractions": {},      # vendor_name -> extraction dict
        "comparison": None,     # comparison dict
        "clarifications": {},   # vendor_name -> {subject, email_body}
        "traces": [],           # [{agent, input_preview, prompt, raw_output, parsed, ts}]
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_state()


# ---------------------------------------------------------------------------
# Claude API helper with trace logging
# ---------------------------------------------------------------------------
def get_client():
    key = os.environ.get("ANTHROPIC_API_KEY") or st.session_state.get("api_key")
    if not key:
        return None
    try:
        import anthropic
        return anthropic.Anthropic(api_key=key)
    except Exception as e:
        st.error(f"Could not initialize Anthropic client: {e}")
        return None


MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def call_claude(agent_name: str, prompt: str, input_preview: str,
                max_tokens: int = 8000, temperature: float = 0.2):
    """Call Claude, log a full trace, return raw text (or None on failure)."""
    client = get_client()
    if client is None:
        st.error("No API key. Enter your ANTHROPIC_API_KEY in the sidebar.")
        return None
    try:
        with st.spinner(f"Running {agent_name}…"):
            resp = client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
        raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
        if getattr(resp, "stop_reason", None) == "max_tokens":
            st.warning(f"{agent_name}: output hit the token limit and was cut off — "
                       "result may be incomplete. Try again or reduce input size.")
    except Exception as e:
        st.error(f"{agent_name} failed: {e}")
        return None

    st.session_state.traces.append({
        "agent": agent_name,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input_preview": input_preview[:1500],
        "prompt": prompt,
        "raw_output": raw,
    })
    return raw


def parse_json(raw: str):
    """Robustly parse model output into JSON (strip fences, find outer braces)."""
    if raw is None:
        return None
    txt = raw.strip()
    txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt, flags=re.MULTILINE).strip()
    try:
        return json.loads(txt, strict=False)  # strict=False tolerates raw newlines in strings
    except json.JSONDecodeError:
        start, end = txt.find("{"), txt.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(txt[start:end + 1], strict=False)
            except json.JSONDecodeError:
                pass
    st.warning("Model returned non-JSON output; raw text shown in Prompt Trace.")
    return None


# ---------------------------------------------------------------------------
# File reading (Part C: upload support for txt/md/json/pdf/docx)
# ---------------------------------------------------------------------------
def read_uploaded_file(f) -> str:
    name = f.name.lower()
    data = f.read()
    if name.endswith((".txt", ".md", ".json")):
        return data.decode("utf-8", errors="replace")
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            st.error(f"PDF parsing failed: {e}")
            return ""
    if name.endswith(".docx"):
        try:
            import io
            from docx import Document
            doc = Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            st.error(f"DOCX parsing failed: {e}")
            return ""
    st.error("Unsupported file type. Use txt, md, json, pdf, or docx.")
    return ""


# ---------------------------------------------------------------------------
# Agent runners
# ---------------------------------------------------------------------------
def run_rfq_generation():
    raw = call_claude("RFQ Generation Agent", P.RFQ_GENERATION_PROMPT,
                      "Scenario: kids' nutrition drink launch — marketing services RFQ")
    parsed = parse_json(raw)
    if parsed:
        st.session_state.rfq = parsed
        # New RFQ invalidates downstream artifacts
        st.session_state.extractions = {}
        st.session_state.comparison = None
        st.session_state.clarifications = {}


def run_vendor_generation():
    rfq_json = json.dumps(st.session_state.rfq, indent=2)
    prompt = P.VENDOR_RESPONSE_GENERATION_PROMPT.replace("<<<RFQ_JSON>>>", rfq_json)
    raw = call_claude("Vendor Response Generation Agent", prompt,
                      f"RFQ: {st.session_state.rfq.get('title', '')}", max_tokens=16000,
                      temperature=0.7)
    if not raw:
        return
    blocks = re.findall(
        r"=====VENDOR_START=====\s*(.*?)\s*=====VENDOR_END=====",
        raw, flags=re.DOTALL)
    if not blocks:
        st.warning("Could not parse vendor blocks; raw output is in Prompt Trace.")
        return
    added = 0
    for block in blocks:
        m = re.match(r"VENDOR_NAME:\s*(.+)", block)
        name = m.group(1).strip() if m else f"Vendor {len(st.session_state.vendors)+1}"
        text = block[m.end():].strip() if m else block.strip()
        if not text:
            continue
        st.session_state.vendors.append({
            "name": name,
            "text": text,
            "source": "generated",
            "guard": {"verdict": "VENDOR_RESPONSE", "confidence": "HIGH",
                      "reason": "Generated by the Vendor Response Generation Agent."},
        })
        added += 1
    st.success(f"Generated {added} vendor responses.")


def run_exception_guard(doc_text: str) -> dict:
    title = (st.session_state.rfq or {}).get("title", "Marketing services RFQ")
    prompt = (P.EXCEPTION_GUARD_PROMPT
              .replace("<<<RFQ_TITLE>>>", title)
              .replace("<<<DOC_TEXT>>>", doc_text[:4000]))
    raw = call_claude("Exception Guard", prompt, doc_text[:300], max_tokens=500)
    return parse_json(raw) or {"verdict": "PARTIAL_SUSPECT", "confidence": "LOW",
                               "reason": "Guard did not return valid JSON.",
                               "detected_vendor_name": None}


def run_extraction(vendor: dict):
    rfq_json = json.dumps(st.session_state.rfq, indent=2)
    prompt = (P.EXTRACTION_AGENT_PROMPT
              .replace("<<<RFQ_JSON>>>", rfq_json)
              .replace("<<<VENDOR_TEXT>>>", vendor["text"]))
    raw = call_claude(f"Extraction Agent [{vendor['name']}]", prompt,
                      vendor["text"][:600], max_tokens=8000)
    parsed = parse_json(raw)
    if parsed:
        st.session_state.extractions[vendor["name"]] = parsed
        st.session_state.comparison = None  # extraction changed → comparison stale


def run_comparison():
    ext_json = json.dumps(st.session_state.extractions, indent=2)
    prompt = P.COMPARISON_AGENT_PROMPT.replace("<<<EXTRACTIONS_JSON>>>", ext_json)
    raw = call_claude("Comparison Agent", prompt,
                      f"{len(st.session_state.extractions)} extractions",
                      max_tokens=16000)
    parsed = parse_json(raw)
    if parsed:
        st.session_state.comparison = parsed


def run_clarification(vendor_name: str):
    ext = st.session_state.extractions.get(vendor_name)
    prompt = P.CLARIFICATION_AGENT_PROMPT.replace(
        "<<<EXTRACTION_JSON>>>", json.dumps(ext, indent=2))
    raw = call_claude(f"Clarification Agent [{vendor_name}]", prompt,
                      f"Flags for {vendor_name}", max_tokens=3000)
    parsed = parse_json(raw)
    if parsed:
        st.session_state.clarifications[vendor_name] = parsed


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📋 RFQ Copilot")
    st.caption("Prompt-driven RFQ evaluation for procurement buyers")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.session_state.api_key = st.text_input(
            "Anthropic API key", type="password",
            help="Set ANTHROPIC_API_KEY env var to skip this.")

    screen = st.radio("Screens", [
        "1 · RFQ Overview",
        "2 · Vendor Upload / Input",
        "3 · Extraction Review",
        "4 · Vendor Comparison",
        "5 · Prompt Trace / Prompt Pack",
    ])

    st.divider()
    # Buyer-first status summary — what the buyer should see at a glance
    n_v = len(st.session_state.vendors)
    n_e = len(st.session_state.extractions)
    high_flags = sum(
        1 for e in st.session_state.extractions.values()
        for f in e.get("flags", []) if f.get("severity") == "HIGH")
    st.metric("Vendor responses", n_v)
    st.metric("Extracted", f"{n_e}/{n_v}" if n_v else "0")
    st.metric("High-severity flags", high_flags)


# ===========================================================================
# SCREEN 1 — RFQ OVERVIEW
# ===========================================================================
if screen.startswith("1"):
    st.header("RFQ Overview")
    st.caption("What this procurement event is about, and what vendors must respond to.")

    if st.button("🪄 Generate RFQ" if not st.session_state.rfq else "🔄 Regenerate RFQ",
                 type="primary"):
        run_rfq_generation()

    rfq = st.session_state.rfq
    if not rfq:
        st.info("No RFQ yet. Click **Generate RFQ** — the RFQ Generation Agent will "
                "create a realistic marketing-services RFQ with 8 line items.")
    else:
        st.subheader(rfq.get("title", "RFQ"))
        st.caption(f"{rfq.get('rfq_id','')} · Issued by {rfq.get('issued_by','')}")

        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown("#### Background & objectives")
            st.write(rfq.get("general_information", ""))
            st.markdown("#### Scope of work")
            st.write(rfq.get("scope_of_work", ""))
        with c2:
            st.markdown("#### Timelines")
            for t in rfq.get("timelines", []):
                st.markdown(f"- **{t.get('milestone')}** — {t.get('date')}")
            st.markdown("#### Evaluation criteria")
            for e in rfq.get("evaluation_criteria", []):
                st.markdown(f"- {e.get('criterion')} — **{e.get('weight')}**")

        st.markdown("#### Line items (LI-1 … LI-8)")
        for li in rfq.get("line_items", []):
            with st.expander(f"{li.get('id')} · {li.get('name')}"):
                st.write(li.get("description", ""))
                if li.get("deliverables"):
                    st.markdown("**Deliverables:** " + "; ".join(li["deliverables"]))

        t1, t2, t3 = st.tabs(["Commercial expectations", "Vendor questionnaire",
                              "Compliance requirements"])
        with t1:
            for c in rfq.get("commercial_expectations", []):
                st.markdown(f"- {c}")
        with t2:
            for q in rfq.get("vendor_questionnaire", []):
                st.markdown(f"- **{q.get('q_id')}** {q.get('question')}")
        with t3:
            for c in rfq.get("compliance_requirements", []):
                st.markdown(f"- **{c.get('c_id')}** {c.get('requirement')}")


# ===========================================================================
# SCREEN 2 — VENDOR UPLOAD / INPUT
# ===========================================================================
elif screen.startswith("2"):
    st.header("Vendor Upload / Input")
    st.caption("Upload, paste, or generate vendor responses. Every input is validated "
               "by the Exception Guard, then processed dynamically — nothing is hardcoded.")

    if not st.session_state.rfq:
        st.warning("Generate the RFQ first (Screen 1) so responses can be judged "
                   "against real requirements.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### 🎲 Generate messy test data")
            st.caption("Vendor Response Generation Agent: 3 personas with seeded, "
                       "known defect profiles (missing pricing, contradictions, "
                       "bundled pricing, vague timelines…).")
            if st.button("Generate 3 vendor responses", type="primary"):
                run_vendor_generation()

        with c2:
            st.markdown("#### 📤 Upload or paste a response")
            up = st.file_uploader("File (txt · md · json · pdf · docx)",
                                  type=["txt", "md", "json", "pdf", "docx"])
            pasted = st.text_area("…or paste response text", height=140)
            vname = st.text_input("Vendor name (optional — guard will try to detect)")
            if st.button("Add vendor response"):
                text = read_uploaded_file(up) if up else (pasted or "").strip()
                if not text:
                    st.error("No content provided.")
                else:
                    guard = run_exception_guard(text)
                    verdict = guard.get("verdict")
                    name = (vname.strip() or guard.get("detected_vendor_name")
                            or f"Vendor {len(st.session_state.vendors)+1}")
                    if verdict == "VENDOR_RESPONSE" or verdict == "PARTIAL_SUSPECT":
                        st.session_state.vendors.append(
                            {"name": name, "text": text,
                             "source": up.name if up else "pasted", "guard": guard})
                        if verdict == "PARTIAL_SUSPECT":
                            st.warning(f"Accepted with a warning: {guard.get('reason')}")
                        else:
                            st.success(f"Added **{name}** ({guard.get('reason')})")
                    else:
                        st.error(f"Rejected — {verdict}: {guard.get('reason')} "
                                 "You can rename/fix the file and retry.")

        st.divider()
        st.markdown("#### Loaded vendor responses")
        if not st.session_state.vendors:
            st.info("No vendor responses yet. Generate test data or upload one.")
        for i, v in enumerate(st.session_state.vendors):
            g = v.get("guard", {})
            with st.expander(f"🏢 {v['name']}  ·  source: {v['source']}  ·  "
                             f"guard: {g.get('verdict','—')}"):
                st.caption(g.get("reason", ""))
                st.text_area("Response text", v["text"], height=240,
                             key=f"vt_{i}", disabled=True)
                if st.button("Remove", key=f"rm_{i}"):
                    removed = st.session_state.vendors.pop(i)
                    st.session_state.extractions.pop(removed["name"], None)
                    st.session_state.comparison = None
                    st.rerun()


# ===========================================================================
# SCREEN 3 — EXTRACTION REVIEW
# ===========================================================================
elif screen.startswith("3"):
    st.header("Extraction Review")
    st.caption("Evidence-backed extraction per vendor. Anything the vendor did not "
               "actually say is flagged — never guessed.")

    if not st.session_state.vendors:
        st.warning("Add vendor responses first (Screen 2).")
    else:
        cols = st.columns([2, 1])
        with cols[0]:
            pending = [v for v in st.session_state.vendors
                       if v["name"] not in st.session_state.extractions]
            if st.button(f"▶️ Run extraction ({len(pending)} pending)",
                         type="primary", disabled=not pending):
                for v in pending:
                    run_extraction(v)
                st.rerun()
        with cols[1]:
            if st.button("↻ Re-extract all"):
                for v in st.session_state.vendors:
                    run_extraction(v)
                st.rerun()

        if not st.session_state.extractions:
            st.info("Run extraction to see structured, evidence-backed results.")
        else:
            tabs = st.tabs(list(st.session_state.extractions.keys()))
            for tab, (vname, ext) in zip(tabs, st.session_state.extractions.items()):
                with tab:
                    st.markdown(f"**Summary:** {ext.get('summary','')}")

                    # --- Flags first: what the buyer must see before anything ---
                    flags = ext.get("flags", [])
                    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
                    flags = sorted(flags, key=lambda f: order.get(f.get("severity"), 3))
                    st.markdown(f"#### 🚩 Flags ({len(flags)})")
                    for f in flags:
                        sev = f.get("severity", "LOW")
                        icon = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}.get(sev, "⚪")
                        st.markdown(
                            f"{icon} **{sev} · {f.get('type')}** — {f.get('description')}"
                            + evidence_block(f.get("evidence")),
                            unsafe_allow_html=True)

                    st.markdown("#### 📦 Line-item coverage vs RFQ")
                    for li in ext.get("line_item_coverage", []):
                        cov = li.get("coverage", "UNCLEAR")
                        st.markdown(
                            f"{badge(cov)} **{li.get('rfq_item_id')} "
                            f"{li.get('rfq_item_name')}** · price: "
                            f"`{li.get('price') or '—'}` — {li.get('notes','')}"
                            + evidence_block(li.get("evidence")),
                            unsafe_allow_html=True)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### 💰 Pricing")
                        pr = ext.get("pricing", {})
                        st.markdown(
                            badge(pr.get("status")) +
                            f" Total: `{pr.get('grand_total') or '—'}` · "
                            f"Currency: `{pr.get('currency') or '—'}` · "
                            f"Taxes: {pr.get('taxes') or '—'}<br>"
                            f"Structure: {pr.get('pricing_structure','—')}"
                            + evidence_block(pr.get("evidence")),
                            unsafe_allow_html=True)
                        for iss in pr.get("issues", []):
                            st.markdown(f"- ⚠️ {iss}")

                        st.markdown("#### 📜 Commercial terms")
                        ct = ext.get("commercial_terms", {})
                        for label in ("payment_terms", "validity"):
                            fld = ct.get(label, {}) or {}
                            st.markdown(
                                badge(fld.get("status")) +
                                f" **{label.replace('_',' ').title()}:** "
                                f"{fld.get('value') or '—'}"
                                + evidence_block(fld.get("evidence")),
                                unsafe_allow_html=True)
                        if ct.get("assumptions"):
                            st.markdown("**Assumptions:** " + "; ".join(ct["assumptions"]))
                        if ct.get("exclusions"):
                            st.markdown("**Exclusions:** " + "; ".join(ct["exclusions"]))

                    with c2:
                        st.markdown("#### 🗓 Timeline")
                        tl = ext.get("timeline", {})
                        st.markdown(
                            badge(tl.get("status")) +
                            f" {tl.get('summary') or '—'}<br>"
                            f"Meets RFQ window: **{tl.get('meets_rfq_window','UNCLEAR')}**"
                            + evidence_block(tl.get("evidence")),
                            unsafe_allow_html=True)

                        st.markdown("#### 🧑‍💼 Experience")
                        ex = ext.get("experience", {})
                        st.markdown(
                            badge(ex.get("status")) +
                            f" Relevance: **{ex.get('relevance_to_rfq','—')}** — "
                            f"{ex.get('summary') or '—'}"
                            + evidence_block(ex.get("evidence")),
                            unsafe_allow_html=True)

                        st.markdown("#### ✅ Compliance")
                        for c in ext.get("compliance", []):
                            st.markdown(
                                badge(c.get("status")) +
                                f" **{c.get('requirement')}** — "
                                f"{c.get('vendor_position') or '—'}"
                                + evidence_block(c.get("evidence")),
                                unsafe_allow_html=True)

                    st.markdown("#### ❓ Clarification questions")
                    for q in ext.get("clarification_questions", []):
                        st.markdown(f"- {q}")

                    if st.button(f"✉️ Draft clarification email for {vname}",
                                 key=f"cl_{vname}"):
                        run_clarification(vname)
                    if vname in st.session_state.clarifications:
                        cl = st.session_state.clarifications[vname]
                        st.markdown(f"**Subject:** {cl.get('subject')}")
                        st.text_area("Email draft", cl.get("email_body", ""),
                                     height=260, key=f"em_{vname}")


# ===========================================================================
# SCREEN 4 — VENDOR COMPARISON
# ===========================================================================
elif screen.startswith("4"):
    st.header("Vendor Comparison")
    st.caption("Dimension-by-dimension, grounded only in extracted evidence. "
               "No fabricated overall score — what can't be compared is said out loud.")

    if len(st.session_state.extractions) < 2:
        st.warning("Extract at least 2 vendors first (Screen 3).")
    else:
        if st.button("⚖️ Run comparison" if not st.session_state.comparison
                     else "↻ Re-run comparison", type="primary"):
            run_comparison()

        comp = st.session_state.comparison
        if comp:
            # 1) Comparability gate — the first thing a buyer should see
            st.markdown("#### 1 · Are these vendors even comparable yet?")
            ccols = st.columns(len(comp.get("comparability", [])) or 1)
            for col, c in zip(ccols, comp.get("comparability", [])):
                with col:
                    ok = c.get("verdict") == "COMPARABLE"
                    (st.success if ok else st.error)(
                        f"**{c.get('vendor_name')}**\n\n"
                        f"{'✅ COMPARABLE' if ok else '⛔ NOT YET COMPARABLE'}")
                    for r in c.get("reasons", []):
                        st.caption(f"• {r}")

            # 2) Buyer attention points
            st.markdown("#### 2 · Buyer attention points (by decision impact)")
            for p in comp.get("buyer_attention_points", []):
                st.markdown(f"**{p.get('priority')}.** {p.get('point')}  "
                            f"— _affects: {', '.join(p.get('affected_vendors', []))}_")

            # 3) Dimension matrix
            st.markdown("#### 3 · Dimension-by-dimension comparison")
            for d in comp.get("dimensions", []):
                with st.expander(f"📐 {d.get('dimension')}", expanded=False):
                    for a in d.get("assessment", []):
                        st.markdown(
                            badge(a.get("rating")) +
                            f" **{a.get('vendor_name')}** — {a.get('rationale')}"
                            + evidence_block(a.get("evidence")),
                            unsafe_allow_html=True)
                    for nc in d.get("not_comparable", []):
                        st.markdown(f"- ⚪ *Cannot compare:* {nc}")

            st.markdown("#### 4 · Key differences")
            for k in comp.get("key_differences", []):
                st.markdown(f"- {k}")

            st.markdown("#### 5 · Clarifications needed before award")
            for c in comp.get("clarifications_needed", []):
                st.markdown(f"**{c.get('vendor_name')}**")
                for q in c.get("questions", []):
                    st.markdown(f"  - {q}")

            st.markdown("#### 6 · Suggested next steps")
            for s in comp.get("suggested_next_steps", []):
                st.markdown(f"- {s}")


# ===========================================================================
# SCREEN 5 — PROMPT TRACE / PROMPT PACK
# ===========================================================================
else:
    st.header("Prompt Trace / Prompt Pack")

    t1, t2 = st.tabs(["🧾 Live prompt traces", "📚 Prompt Pack"])

    with t1:
        st.caption("Every agent call in this session: input → prompt → model output. "
                   "Export for the submission's Prompt Trace deliverable.")
        if not st.session_state.traces:
            st.info("No traces yet — run any agent.")
        else:
            st.download_button(
                "⬇️ Download all traces (JSON)",
                json.dumps(st.session_state.traces, indent=2),
                file_name="prompt_traces.json", mime="application/json")
            for i, tr in enumerate(reversed(st.session_state.traces)):
                with st.expander(f"{tr['agent']} · {tr['ts']}"):
                    st.markdown("**Input (preview)**")
                    st.code(tr["input_preview"] or "—")
                    st.markdown("**Prompt sent**")
                    st.code(tr["prompt"][:6000])
                    st.markdown("**Model output (raw)**")
                    st.code(tr["raw_output"][:6000])

    with t2:
        st.caption("The full prompt pack with design rationales lives in prompts.py; "
                   "shown here for review.")
        packs = [
            ("1 · RFQ Generation", P.RFQ_GENERATION_PROMPT),
            ("2 · Vendor Response + Messy Data Generation", P.VENDOR_RESPONSE_GENERATION_PROMPT),
            ("3 · UI/UX Generation", P.UI_UX_GENERATION_PROMPT),
            ("4 · Extraction Agent", P.EXTRACTION_AGENT_PROMPT),
            ("5 · Comparison Agent", P.COMPARISON_AGENT_PROMPT),
            ("6 · Clarification / Exception Handling", P.CLARIFICATION_AGENT_PROMPT),
            ("7 · Exception Guard (input validation)", P.EXCEPTION_GUARD_PROMPT),
        ]
        for name, text in packs:
            with st.expander(name):
                st.code(text)
