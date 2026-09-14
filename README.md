# Data Analyst Interview Questions

A working collection of **data-analyst / data-engineer interview questions** —
real interviews, company-specific prep, and practice drills organized by topic.
Every SQL query and Python snippet here is **runnable and its output verified**
against PostgreSQL 16 / Python 3, so the answers are correct, not just
plausible.

## What's inside

### 📼 Real interviews — [`real-interviews/`](./real-interviews/)
Actual interviews, reconstructed with the exact questions, worked answers, and
the trap behind each one.

- **[Emirates NBD](./real-interviews/emirates-nbd.md)** (banking / client analytics) —
  `COUNT` + `NULL`, `UNION` vs `UNION ALL`, the `LEFT JOIN` + `WHERE` trap, and
  first-row window functions. Runnable: [`emirates-nbd.sql`](./real-interviews/emirates-nbd.sql).

### 🏢 Company prep — [`company-prep/`](./company-prep/)
Materials targeted at a specific company's loop.

- **[Meta / Facebook — Data Engineer](./company-prep/meta-data-engineer/)** —
  role overview + JD study notes, the "Salesperson" [SQL set](./company-prep/meta-data-engineer/sql-practice.md)
  (6 questions), and a [Python coding warm-up](./company-prep/meta-data-engineer/python-coding.md) (4 problems).

### 📚 Practice by topic — [`topics/`](./topics/)
Original drills against one shared [`schema.sql`](./topics/schema.sql), each with
try-it-yourself answers and verified output.

| # | Topic | Covers |
|---|-------|--------|
| 01 | [Basics & filtering](./topics/01-basics-and-filtering.md) | `SELECT`, `WHERE`, `DISTINCT`, `ORDER BY`, `LIMIT`, sargable predicates |
| 02 | [Joins](./topics/02-joins.md) | inner/left, self-join, anti-join, `ON` vs `WHERE` |
| 03 | [Aggregation & grouping](./topics/03-aggregation-and-grouping.md) | `GROUP BY`, `HAVING`, `COUNT`/`SUM`/`AVG`, zero-groups |
| 04 | [Subqueries & CTEs](./topics/04-subqueries-and-ctes.md) | scalar, correlated, `WITH`, Nth-highest |
| 05 | [Window functions](./topics/05-window-functions.md) | `ROW_NUMBER`/`RANK`/`DENSE_RANK`, running totals, `LAG`/`LEAD`, top-N per group |
| 06 | [NULLs, sets & gotchas](./topics/06-nulls-sets-and-gotchas.md) | NULL logic, `NOT IN` trap, `UNION` vs `UNION ALL`, the join traps |

### ⚡ [CHEATSHEET.md](./CHEATSHEET.md)
One-page reference: clause execution order, the ranking functions, and the
traps that cost people offers.

## Run the examples

Everything targets PostgreSQL (dialect notes call out where SQL Server / Oracle /
MySQL differ). With any Postgres handy:

```bash
createdb sqlprep

# topic drills — load the shared schema, then read along
psql -d sqlprep -f topics/schema.sql

# a self-contained interview (schema + data + queries + expected output)
psql -d sqlprep -f real-interviews/emirates-nbd.sql

# company SQL set
psql -d sqlprep -f company-prep/meta-data-engineer/sql-practice.sql

# python warm-up
python3 company-prep/meta-data-engineer/python_coding.py
```

No local Postgres? Paste any `.sql` into [db-fiddle.com](https://www.db-fiddle.com/)
or [sqliteonline.com](https://sqliteonline.com/) (pick PostgreSQL).

## Contributing more questions

Interview questions are the currency here. To add one:

1. Put it in the right place — `real-interviews/` (something you were actually
   asked), `company-prep/<company>/`, or the matching `topics/` file.
2. Make it **runnable and verified**: ship the schema + query in `.sql`, run it,
   and paste the real output. See [`real-interviews/README.md`](./real-interviews/README.md).
3. **Anonymise** anything confidential — keep the lesson, drop real names, IDs,
   and proprietary data.
