# 03 — Aggregation & grouping

`GROUP BY`, `HAVING`, and the aggregate functions. Load
[`schema.sql`](./schema.sql) first.

Mental model of the pipeline:
`FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT`.
`WHERE` filters **rows before** grouping; `HAVING` filters **groups after**.

---

**1. Headcount per department — show departments with zero too.**

<details><summary>Solution</summary>

```sql
SELECT d.dept_name, COUNT(e.emp_id) AS n_emp
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id
GROUP BY d.dept_id, d.dept_name
ORDER BY n_emp DESC, d.dept_name;
```

| dept_name | n_emp |
|-----------|-------|
| Engineering | 4 |
| Sales | 3 |
| Finance | 2 |
| Marketing | 2 |
| Research | 0 |

Count `e.emp_id` (a column), **not** `COUNT(*)`. With the `LEFT JOIN`, Research
produces one all-NULL row; `COUNT(*)` would count that row as **1**, while
`COUNT(e.emp_id)` correctly counts non-NULL employees → **0**.
</details>

**2. Departments whose average salary exceeds 90,000.**

<details><summary>Solution</summary>

```sql
SELECT d.dept_name, ROUND(AVG(e.salary), 2) AS avg_sal
FROM departments d
JOIN employees e ON e.dept_id = d.dept_id
GROUP BY d.dept_name
HAVING AVG(e.salary) > 90000
ORDER BY avg_sal DESC;
```

| dept_name | avg_sal |
|-----------|---------|
| Engineering | 117500.00 |

The filter is on an **aggregate**, so it must live in `HAVING`, not `WHERE`. You
can repeat the expression in `HAVING`; you cannot reference the `avg_sal` alias
there in most engines (the SELECT list is evaluated after HAVING).
</details>

**3. Completed revenue by customer city.**

<details><summary>Solution</summary>

```sql
SELECT c.city, SUM(o.amount) AS revenue
FROM customers c
JOIN orders o ON o.cust_id = c.cust_id
WHERE o.status = 'completed'
GROUP BY c.city
ORDER BY revenue DESC;
```

| city | revenue |
|------|---------|
| Dubai | 3350 |
| Abu Dhabi | 1000 |
| Sharjah | 250 |

`status = 'completed'` is a **row** filter → `WHERE`, before grouping. (Here an
`INNER JOIN` is intended: we only want cities that actually have completed
revenue.)
</details>

**4. Departments where someone earns more than 100,000.**

<details><summary>Solution</summary>

```sql
SELECT d.dept_name, MAX(e.salary) AS max_sal
FROM departments d
JOIN employees e ON e.dept_id = d.dept_id
GROUP BY d.dept_name
HAVING MAX(e.salary) > 100000
ORDER BY max_sal DESC;
```

| dept_name | max_sal |
|-----------|---------|
| Engineering | 150000 |
| Finance | 110000 |
</details>

**5. How many distinct customers ordered each month?**

<details><summary>Solution</summary>

```sql
SELECT to_char(order_date, 'YYYY-MM') AS ym,
       COUNT(DISTINCT cust_id)        AS n_customers
FROM orders
GROUP BY 1
ORDER BY 1;
```

| ym | n_customers |
|----|-------------|
| 2023-01 | 1 |
| 2023-02 | 2 |
| 2023-03 | 2 |
| 2023-04 | 1 |
| 2023-05 | 3 |

`COUNT(DISTINCT cust_id)` counts unique customers, not orders — the standard
"active users" metric. `GROUP BY 1` groups by the first select expression (handy
for a computed bucket); some teams prefer spelling the expression out for
clarity.
</details>

---

**Gotchas.** Every non-aggregated column in `SELECT` must appear in `GROUP BY`
(Postgres/most engines enforce this; MySQL historically let it slide and returned
arbitrary values — don't rely on that). And remember all aggregates except
`COUNT(*)` skip `NULL`, so `AVG` divides by the count of non-NULLs, not by the
number of rows.

Next: [04 — Subqueries & CTEs](./04-subqueries-and-ctes.md)
