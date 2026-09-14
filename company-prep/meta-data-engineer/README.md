# Meta / Facebook — Data Engineer (Analytics)

Prep notes for the Data Engineer, Analytics loop, distilled from the role
overview and JD. The interview leans on **SQL** and a light **Python** coding
warm-up, plus data-modeling discussion.

- **SQL practice** → [`sql-practice.md`](./sql-practice.md) · runnable [`sql-practice.sql`](./sql-practice.sql)
- **Python coding** → [`python-coding.md`](./python-coding.md) · runnable [`python_coding.py`](./python_coding.py)

## What the role actually does

The Analytics DE team makes data *actionable* for product teams. Day to day:

- Design **scalable data models** for very large (multi-petabyte) systems.
- Define **standardized metrics and dimensions** so teams measure things the same way.
- Build and own **production ETL pipelines** and **core data sets** (e.g. user-dimension / activity tables).
- Own **data quality** — timeliness, completeness, accuracy, no duplication.
- Build **dashboards** and self-serve data products for PMs and analysts.

Tech stack referenced (useful for vocabulary, not memorization): a Hadoop-based
warehouse with **Hive** and **Presto** as SQL interfaces, **Vertica** for
columnar extracts/aggregations, some **Oracle**, **Scuba** for real-time
analysis, **Scribe** for moving data between systems, an in-house Python ETL
framework (**DataSwarm**), and an internal BI tool (**UniDash**), alongside
Tableau / MicroStrategy.

## What to prepare (from the JD)

| Area | Prepare |
|------|---------|
| **SQL** | joins, aggregation, window functions, and the NULL / `LEFT JOIN` gotchas — the whole [`../../topics/`](../../topics/) set |
| **ETL & modeling** | star/snowflake schemas, fact vs dimension, slowly-changing dimensions, idempotent/backfillable pipelines, partitioning |
| **Big-data systems** | how a MapReduce / MPP engine (Hive, Presto, Spark) executes a query; partition pruning; skew |
| **Python / Java** | loops, lists, dicts/hashmaps — small algorithmic warm-ups (see the Python set) |
| **Data quality & SLAs** | freshness/completeness checks, defining and owning an SLA for a data set |
| **Product sense** | acquisition / retention / engagement metrics, and translating a product question into a data set |

## How to use this folder

1. Try the SQL questions cold against the shipped dataset:
   `psql -d sqlprep -f sql-practice.sql` and cover the answers.
2. Solve the Python problems in a plain editor (interviews use a shared pad):
   `python3 python_coding.py` should print `all asserts passed`.
3. For each SQL answer, be ready to *explain the plan* — which join, why, what it
   costs at scale.

> Source: the candidate's own prep materials. Paraphrased to the parts useful for
> studying; company boilerplate omitted.
