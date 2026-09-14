# Puffy Lux PDP — A/B Test Conversion Analysis

Data-analyst case study: analyzing an A/B test on the **Puffy Lux mattress
product page (PDP)** — Arm A (control) vs Arm B (redesigned hero + buy box) —
from raw clickstream events and order line items, to a defensible
recommendation.

The written analysis and all supporting code live in the notebook:
**[`Priyabrata_Puffy_Data_Analyst.ipynb`](./Priyabrata_Puffy_Data_Analyst.ipynb)**
(exported to [`Priyabrata_Puffy_Data_Analyst_report.pdf`](./Priyabrata_Puffy_Data_Analyst_report.pdf)).

## What's in the notebook

1. **Executive summary**
2. **Method & data preparation** — arm assignment from `ab_experiment_init`,
   traffic-quality filtering, dedup
3. **Sanity checks** — sample-ratio mismatch (SRM) test and overall conversion
4. **a. The funnel** — Arm A vs Arm B, step by step
5. **b. The read** — what the funnel is telling us
6. **c. Behavioral changes** — and the likely mechanism
7. **d. Recommendation** — evidence-backed next steps
8. **Process & AI usage** + **AI-Delta Log**

## Data

| File | Included | Notes |
|------|----------|-------|
| `data/ab_hero_v4_order_line_items.csv` | ✅ | one row per product per order — `order_id, product_name, variant, quantity, value` (377 rows) |
| `ab_hero_v4_events.csv` | ❌ not included | the clickstream events file the notebook also reads; add it under `data/` (or the notebook's working dir) to reproduce end-to-end |

The dataset is **synthetic** — it mimics real clickstream behavior for
assessment purposes and does not represent actual business metrics.

## Run it

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas scipy matplotlib jupyter
# place ab_hero_v4_events.csv next to the order-line-items CSV, then:
jupyter notebook Priyabrata_Puffy_Data_Analyst.ipynb
```

> The original case-study brief is a third-party hiring document and is **not**
> included in this repository.
