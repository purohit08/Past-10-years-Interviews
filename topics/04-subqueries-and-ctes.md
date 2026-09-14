# 04 — Subqueries & CTEs

Scalar, correlated, and derived-table subqueries, plus `WITH` (Common Table
Expressions). Load [`schema.sql`](./schema.sql) first.

- **Scalar subquery** — returns one value, usable anywhere a value is: `WHERE salary > (SELECT AVG(salary) …)`.
- **Correlated subquery** — references the outer row, so it re-evaluates per row.
- **CTE (`WITH`)** — a named subquery that reads top-to-bottom; the modern way to keep complex SQL legible.

---

**1. Employees paid above the company average.**

<details><summary>Solution</summary>

```sql
SELECT emp_name, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees)
ORDER BY salary DESC, emp_name;
```

| emp_name | salary |
|----------|--------|
| Alice | 150000 |
| Bob | 120000 |
| Carol | 120000 |
| Ivan | 110000 |
| Grace | 95000 |

The company average is ~92,917 (see [06](./06-nulls-sets-and-gotchas.md) for why
`AVG` uses non-NULL salaries). The scalar subquery runs once.
</details>

**2. Employees paid above *their own department's* average (correlated).**

<details><summary>Solution</summary>

```sql
SELECT e.emp_name, e.salary
FROM employees e
WHERE e.salary > (
    SELECT AVG(e2.salary)
    FROM employees e2
    WHERE e2.dept_id = e.dept_id      -- correlation to the outer row
)
ORDER BY e.dept_id, e.salary DESC;
```

| emp_name | salary |
|----------|--------|
| Alice | 150000 |
| Bob | 120000 |
| Carol | 120000 |
| Dave | 90000 |
| Grace | 95000 |
| Ivan | 110000 |

The inner query is re-evaluated for each outer employee, against *that
employee's* department. The window-function equivalent —
`AVG(salary) OVER (PARTITION BY dept_id)` — is usually faster because it scans
once; see [05](./05-window-functions.md).
</details>

**3. Customers who spent more than the average customer (CTE).**

<details><summary>Solution</summary>

```sql
WITH spend AS (
    SELECT c.cust_id, c.cust_name,
           COALESCE(SUM(o.amount) FILTER (WHERE o.status = 'completed'), 0) AS total
    FROM customers c
    LEFT JOIN orders o ON o.cust_id = c.cust_id
    GROUP BY c.cust_id, c.cust_name
)
SELECT cust_name, total
FROM spend
WHERE total > (SELECT AVG(total) FROM spend)   -- avg = 920 (no-order customer counts as 0)
ORDER BY total DESC;
```

| cust_name | total |
|-----------|-------|
| XYZ Ltd | 1750 |
| ABC Corp | 1600 |
| PQR Inc | 1000 |

Compute `spend` **once**, then reference it twice — once for the rows, once for
the benchmark. Watch the denominator: including NoOrders Co (0) makes the
average 920; excluding zero-spend customers would make it 1150 and change the
answer. State which you mean.
</details>

**4. The second-highest salary (classic).**

<details><summary>Solution</summary>

```sql
SELECT MAX(salary) AS second_highest
FROM employees
WHERE salary < (SELECT MAX(salary) FROM employees);
```

| second_highest |
|----------------|
| 120000 |

"The biggest that isn't the biggest." Robust to ties for #1 and returns `NULL`
(not an error) if there is no second value. The window-function version,
`DENSE_RANK() OVER (ORDER BY salary DESC) = 2`, generalises to *N*-th and
per-group — see [05](./05-window-functions.md).
</details>

**5. Department with the highest total payroll (CTE + `ORDER BY … LIMIT`).**

<details><summary>Solution</summary>

```sql
WITH payroll AS (
    SELECT d.dept_name, SUM(e.salary) AS total_payroll
    FROM departments d
    JOIN employees e ON e.dept_id = d.dept_id
    GROUP BY d.dept_name
)
SELECT dept_name, total_payroll
FROM payroll
ORDER BY total_payroll DESC
LIMIT 1;
```

| dept_name | total_payroll |
|-----------|---------------|
| Engineering | 470000 |

`LIMIT 1` returns one department even on a tie. If you need *all* departments
tied for the max, rank with a window function and keep `rnk = 1` instead.
</details>

---

**CTE vs subquery.** They express the same thing; CTEs win on readability and
let you reference the same result multiple times (as in Q3/Q5). Recursive CTEs
(`WITH RECURSIVE`) walk hierarchies — an org chart from the `employees`
self-reference, say. In older Postgres a CTE was an optimisation fence (always
materialised); since PG12 simple CTEs can be inlined, so it is no longer a
performance foot-gun.

Next: [05 — Window functions](./05-window-functions.md)
