# 05 — Window functions

The single most tested topic in analyst interviews. A window function computes
across a set of rows **related to the current row** without collapsing them the
way `GROUP BY` does. Load [`schema.sql`](./schema.sql) first.

```
<fn>() OVER (PARTITION BY <group> ORDER BY <sort> [frame])
```

- `PARTITION BY` — restart the calculation per group (optional).
- `ORDER BY` — order within the partition (required for ranking, `LAG`, running totals).
- Ranks: `ROW_NUMBER` (always unique), `RANK` (gaps after ties: 1,2,2,4), `DENSE_RANK` (no gaps: 1,2,2,3).

---

**1. Rank employees by salary within each department — three ways.**

<details><summary>Solution</summary>

```sql
SELECT emp_name, dept_id, salary,
       RANK()       OVER (PARTITION BY dept_id ORDER BY salary DESC)            AS rnk,
       DENSE_RANK() OVER (PARTITION BY dept_id ORDER BY salary DESC)            AS drnk,
       ROW_NUMBER() OVER (PARTITION BY dept_id ORDER BY salary DESC, emp_id)    AS rn
FROM employees
WHERE dept_id IS NOT NULL
ORDER BY dept_id, salary DESC, emp_id;
```

Engineering (note Bob & Carol tie at 120000):

| emp_name | salary | rnk | drnk | rn |
|----------|--------|:---:|:----:|:--:|
| Alice | 150000 | 1 | 1 | 1 |
| Bob | 120000 | 2 | 2 | 2 |
| Carol | 120000 | 2 | 2 | 3 |
| Mallory | 80000 | **4** | **3** | 4 |

On the tie, `RANK` jumps to 4, `DENSE_RANK` stays contiguous at 3, and
`ROW_NUMBER` gives every row a distinct number (add a tie-breaker to `ORDER BY`
to make it deterministic).
</details>

**2. The 2nd-highest salary overall.**

<details><summary>Solution</summary>

```sql
WITH r AS (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS dr
    FROM employees
)
SELECT DISTINCT salary FROM r WHERE dr = 2;
```

| salary |
|--------|
| 120000 |

Use `DENSE_RANK` for "N-th distinct value" (`RANK` would skip a rank whenever a
value ties). Swap `2` for any N; add `PARTITION BY dept_id` for "2nd-highest per
department."
</details>

**3. Running total of completed revenue per customer, by date.**

<details><summary>Solution</summary>

```sql
SELECT cust_id, order_date, amount,
       SUM(amount) OVER (PARTITION BY cust_id ORDER BY order_date
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total
FROM orders
WHERE status = 'completed'
ORDER BY cust_id, order_date;
```

Customer 1:

| cust_id | order_date | amount | running_total |
|:-------:|------------|-------:|--------------:|
| 1 | 2023-02-01 | 500 | 500 |
| 1 | 2023-02-15 | 300 | 800 |
| 1 | 2023-05-12 | 800 | 1600 |

The frame `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` is the running-total
frame. Know the default: with `ORDER BY` and no explicit frame, the window is
`RANGE … CURRENT ROW`, which **includes all peer rows tied on the sort key** —
so on duplicate dates a `RANGE` running total lumps the ties together. Spell out
`ROWS` when you want strict row-by-row accumulation.
</details>

**4. Month-over-month change in completed revenue (`LAG`).**

<details><summary>Solution</summary>

```sql
WITH m AS (
    SELECT date_trunc('month', order_date)::date AS mth, SUM(amount) AS rev
    FROM orders WHERE status = 'completed'
    GROUP BY 1
)
SELECT mth, rev,
       rev - LAG(rev) OVER (ORDER BY mth) AS mom_change
FROM m
ORDER BY mth;
```

| mth | rev | mom_change |
|-----|----:|-----------:|
| 2023-01-01 | 400 | *NULL* |
| 2023-02-01 | 1800 | 1400 |
| 2023-03-01 | 250 | -1550 |
| 2023-04-01 | 750 | 500 |
| 2023-05-01 | 1400 | 650 |

`LAG(rev)` reads the previous row's value; the first row has no predecessor so
it is `NULL` (pass `LAG(rev, 1, 0)` to default it to 0). `LEAD` looks forward.
For % change: `100.0 * (rev - LAG(rev) OVER (ORDER BY mth)) / LAG(rev) OVER (ORDER BY mth)`.
</details>

**5. The first order for each customer.**

<details><summary>Solution</summary>

```sql
SELECT cust_id, order_date, amount
FROM (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY order_date, order_id) AS rn
    FROM orders o
) t
WHERE rn = 1
ORDER BY cust_id;
```

| cust_id | order_date | amount |
|:-------:|------------|-------:|
| 1 | 2023-02-01 | 500 |
| 2 | 2023-02-20 | 1000 |
| 3 | 2023-01-25 | 400 |
| 4 | 2023-03-20 | 250 |

You can't put a window function in `WHERE` (windows are computed after
`WHERE`), so compute `rn` in a subquery/CTE and filter it in the outer query.
`ROW_NUMBER` (not `RANK`) guarantees exactly one row per customer.
</details>

**6. The top 2 orders by amount for each customer.**

<details><summary>Solution</summary>

```sql
SELECT cust_id, order_id, amount
FROM (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY cust_id ORDER BY amount DESC, order_id) AS rn
    FROM orders o
) t
WHERE rn <= 2
ORDER BY cust_id, amount DESC;
```

| cust_id | order_id | amount |
|:-------:|:--------:|-------:|
| 1 | 9 | 800 |
| 1 | 1 | 500 |
| 2 | 4 | 1000 |
| 2 | 5 | 750 |
| 3 | 7 | 600 |
| 3 | 6 | 400 |

The **top-N-per-group** template — the most common window-function interview
ask. Use `RANK`/`DENSE_RANK` instead of `ROW_NUMBER` if ties should *both* be
kept.
</details>

---

**Interview reflexes.** "Latest/first row per group," "top-N per group,"
"running total," "compare to previous period," "rank within group," and "share
of group total" (`x / SUM(x) OVER (PARTITION BY …)`) are all windows. Whenever
you hear "per each … within …," reach for `OVER (PARTITION BY …)`.

Next: [06 — NULLs, sets & gotchas](./06-nulls-sets-and-gotchas.md)
