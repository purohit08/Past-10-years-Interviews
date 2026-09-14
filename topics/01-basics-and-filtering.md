# 01 — Basics & filtering

`SELECT`, `WHERE`, `DISTINCT`, `ORDER BY`, `LIMIT`. Load the shared schema
first: `psql -d sqlprep -f topics/schema.sql` (tables described in
[`schema.sql`](./schema.sql)). Try each question, then expand the solution.

---

**1. List the distinct cities customers are in, alphabetically.**

<details><summary>Solution</summary>

```sql
SELECT DISTINCT city
FROM customers
ORDER BY city;
```

| city |
|------|
| Abu Dhabi |
| Dubai |
| Sharjah |

`DISTINCT` applies to the whole select list, not just the first column.
</details>

**2. Employees earning more than 100,000 — name and salary, highest first.**

<details><summary>Solution</summary>

```sql
SELECT emp_name, salary
FROM employees
WHERE salary > 100000
ORDER BY salary DESC, emp_name;
```

| emp_name | salary |
|----------|--------|
| Alice | 150000 |
| Bob | 120000 |
| Carol | 120000 |

Add `emp_name` as a tie-breaker so equal salaries have a deterministic order —
otherwise Bob/Carol could come back in any order.
</details>

**3. Orders placed in February 2023.**

<details><summary>Solution</summary>

```sql
SELECT order_id, order_date, amount
FROM orders
WHERE order_date >= DATE '2023-02-01'
  AND order_date <  DATE '2023-03-01'
ORDER BY order_id;
```

| order_id | order_date | amount |
|----------|------------|--------|
| 1 | 2023-02-01 | 500 |
| 2 | 2023-02-15 | 300 |
| 4 | 2023-02-20 | 1000 |

Prefer a **half-open range** (`>= start AND < next-month`) over
`EXTRACT(MONTH ...) = 2` or `TO_CHAR(...)='...'`. Wrapping the column in a
function blocks the index and (with `EXTRACT(MONTH)`) would wrongly match
February of *every* year. A "sargable" predicate on the bare column stays
index-friendly.
</details>

**4. The three highest-paid employees.**

<details><summary>Solution</summary>

```sql
SELECT emp_name, salary
FROM employees
ORDER BY salary DESC, emp_name
LIMIT 3;
```

| emp_name | salary |
|----------|--------|
| Alice | 150000 |
| Bob | 120000 |
| Carol | 120000 |

`LIMIT` runs *after* `ORDER BY`. Careful: this returns three **rows**, not the
three highest **distinct** salaries (Bob and Carol tie at 120000). "Top-N
distinct values" or "top-N per group" is a window-function job — see
[05](./05-window-functions.md). (`LIMIT` is Postgres/MySQL/SQLite; SQL Server
uses `SELECT TOP 3`, Oracle `FETCH FIRST 3 ROWS ONLY`.)
</details>

**5. Employees not yet assigned to a department.**

<details><summary>Solution</summary>

```sql
SELECT emp_name
FROM employees
WHERE dept_id IS NULL;
```

| emp_name |
|----------|
| Niaj |

Use `IS NULL` / `IS NOT NULL`. `dept_id = NULL` is never true — a comparison
with `NULL` yields `unknown`, which `WHERE` treats as not-true. This NULL logic
is the source of most SQL surprises; see [06](./06-nulls-sets-and-gotchas.md).
</details>

---
Next: [02 — Joins](./02-joins.md)
