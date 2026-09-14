# SQL interview cheatsheet

One page of the things that come up in almost every data-analyst SQL interview.

## Logical execution order

You *write* `SELECT` first, but the engine *runs* it roughly last:

```
FROM / JOIN  →  WHERE  →  GROUP BY  →  HAVING  →  SELECT  →  DISTINCT  →  ORDER BY  →  LIMIT
```

Consequences interviewers test:
- **`WHERE` filters rows; `HAVING` filters groups.** Aggregates can't appear in `WHERE`.
- **SELECT aliases aren't visible** to `WHERE`/`GROUP BY`/`HAVING` (they're computed later) — but *are* visible to `ORDER BY`.
- **Window functions run after `WHERE`/`GROUP BY`**, so you can't filter on them directly — wrap in a subquery/CTE and filter outside.

## NULL logic — the #1 source of wrong answers

| Thing | Behavior |
|-------|----------|
| `x = NULL` | never true — it's `unknown`. Use `IS NULL` / `IS NOT NULL`. |
| `COUNT(*)` | counts rows (NULLs included) |
| `COUNT(col)`, `SUM`, `AVG`, `MIN`, `MAX` | **ignore NULLs**. `AVG` divides by the non-NULL count. |
| `SUM` of empty/all-NULL set | `NULL`, not 0 → `COALESCE(SUM(x), 0)` |
| `NOT IN (… NULL …)` | returns **no rows** → use `NOT EXISTS` |
| `a <> b` | drops NULLs on either side — anti-joins need `NOT EXISTS` or `IS DISTINCT FROM` |

## Joins

| Want | Do |
|------|----|
| Only matches | `INNER JOIN` |
| All left rows | `LEFT JOIN` |
| Left rows with **no** match (anti-join) | `LEFT JOIN … WHERE r.pk IS NULL`, or `NOT EXISTS` |
| Keep all left rows but filter the right side | put the condition in **`ON`**, not `WHERE` |
| Related rows in one table (manager, prev row) | self-join |

> **The classic trap:** a `WHERE` predicate on the *right* table of a `LEFT
> JOIN` turns it into an `INNER JOIN` and silently drops unmatched left rows.
> Move it to `ON`. (See [Emirates NBD Q3c](./real-interviews/emirates-nbd.md).)

## Ranking functions

Salaries `100, 90, 90, 80`:

| Function | Result | Use for |
|----------|--------|---------|
| `ROW_NUMBER()` | 1, 2, 3, 4 | exactly one row per group ("the latest/first") |
| `RANK()` | 1, 2, 2, 4 | standings with gaps after ties |
| `DENSE_RANK()` | 1, 2, 2, 3 | "N-th distinct value" (2nd-highest salary) |

```sql
<fn>() OVER (PARTITION BY grp ORDER BY sortcol [ROWS BETWEEN … ])
```

## Patterns to have in your fingers

```sql
-- N-th highest (per group): DENSE_RANK, keep = N
SELECT * FROM (
  SELECT e.*, DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC) dr
  FROM employees e) t WHERE dr = 2;

-- Latest / top-N row per group: ROW_NUMBER, keep <= N
SELECT * FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY order_date DESC) rn
  FROM orders o) t WHERE rn <= 1;

-- Running total
SUM(amount) OVER (PARTITION BY cust_id ORDER BY order_date
                  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)

-- Period-over-period
rev - LAG(rev) OVER (ORDER BY month)          -- prior period delta

-- Share of group total
1.0 * amount / SUM(amount) OVER (PARTITION BY cust_id)

-- Group with condition, keeping every group
COUNT(*) FILTER (WHERE status = 'completed')  -- or SUM(CASE WHEN … THEN 1 ELSE 0 END)

-- Dedup / concatenate
UNION       -- removes duplicates (costs a sort/hash)
UNION ALL   -- keeps duplicates (cheaper — default when inputs are disjoint)
```

## Performance one-liners (say these out loud)

- Keep predicates **sargable** — filter the bare column (`d >= '2023-02-01' AND d < '2023-03-01'`), don't wrap it in a function.
- `EXISTS` / `NOT EXISTS` usually beat `IN` / `NOT IN` on large, nullable sets — and are NULL-safe.
- A window function scans once; a correlated subquery re-runs per row — prefer the window for per-group stats.
- `COUNT(DISTINCT …)` and `UNION` (vs `UNION ALL`) both pay for de-duplication.

## Dialect quick-notes

| Need | PostgreSQL | SQL Server | Oracle | MySQL |
|------|-----------|-----------|--------|-------|
| Limit rows | `LIMIT n` | `TOP n` / `OFFSET…FETCH` | `FETCH FIRST n ROWS ONLY` | `LIMIT n` |
| NULL fallback | `COALESCE` | `COALESCE`/`ISNULL` | `COALESCE`/`NVL` | `COALESCE`/`IFNULL` |
| String concat | `\|\|` / `concat()` | `+` / `CONCAT` | `\|\|` | `CONCAT` |
| Current date | `CURRENT_DATE` | `CAST(GETDATE() AS date)` | `TRUNC(SYSDATE)` | `CURDATE()` |
