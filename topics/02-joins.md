# 02 — Joins

`INNER` / `LEFT` joins, self-joins, and anti-joins. Load
[`schema.sql`](./schema.sql) first. The schema is seeded so joins actually bite:
**Niaj** has no department, **Research** has no employees, and **NoOrders Co**
never places an order.

---

**1. Every employee with their department name — including the unassigned one.**

<details><summary>Solution</summary>

```sql
SELECT e.emp_name, d.dept_name
FROM employees e
LEFT JOIN departments d ON e.dept_id = d.dept_id
ORDER BY e.emp_id;
```

Tail of the result:

| emp_name | dept_name |
|----------|-----------|
| … | … |
| Mallory | Engineering |
| Niaj | *NULL* |

`LEFT JOIN` keeps Niaj with a `NULL` department. An `INNER JOIN` would silently
drop him — the single most common cause of "my row totals don't add up."
</details>

**2. Departments with no employees.**

<details><summary>Solution</summary>

```sql
SELECT d.dept_name
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id
WHERE e.emp_id IS NULL;
```

| dept_name |
|-----------|
| Research |

The **anti-join** pattern: `LEFT JOIN` then keep only rows where the right side
is `NULL`. Filter on a **non-nullable** right column (a primary key like
`emp_id`) so "no match" is the only way to get `NULL`. Equivalent with
`NOT EXISTS`:

```sql
SELECT d.dept_name
FROM departments d
WHERE NOT EXISTS (SELECT 1 FROM employees e WHERE e.dept_id = d.dept_id);
```
</details>

**3. Each employee alongside their manager's name (self-join).**

<details><summary>Solution</summary>

```sql
SELECT e.emp_name AS employee, m.emp_name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.emp_id
ORDER BY e.emp_id;
```

| employee | manager |
|----------|---------|
| Alice | *NULL* |
| Bob | Alice |
| Eve | Dave |
| Judy | Ivan |
| … | … |

Join a table to **itself** with two aliases. `LEFT JOIN` keeps Alice (the top
of the tree, `manager_id IS NULL`); an `INNER JOIN` would drop her.
</details>

**4. Every customer with their total *completed* spend (0 if none).**

<details><summary>Solution</summary>

```sql
SELECT c.cust_name,
       COALESCE(SUM(o.amount) FILTER (WHERE o.status = 'completed'), 0) AS completed_spend
FROM customers c
LEFT JOIN orders o ON o.cust_id = c.cust_id
GROUP BY c.cust_id, c.cust_name
ORDER BY c.cust_id;
```

| cust_name | completed_spend |
|-----------|-----------------|
| ABC Corp | 1600 |
| XYZ Ltd | 1750 |
| PQR Inc | 1000 |
| LMN LLC | 250 |
| NoOrders Co | 0 |

Two things make this correct: `LEFT JOIN` keeps NoOrders Co, and `COALESCE`
turns its `SUM(NULL)` into `0`. The `FILTER (WHERE ...)` clause restricts the
aggregate to completed orders **without** dropping the customer — putting
`status = 'completed'` in a `WHERE` would evict NoOrders Co (the LEFT-JOIN trap,
see [06](./06-nulls-sets-and-gotchas.md)). Portable form:
`SUM(CASE WHEN o.status='completed' THEN o.amount ELSE 0 END)`.
</details>

**5. Customers who never placed an order.**

<details><summary>Solution</summary>

```sql
SELECT c.cust_name
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.cust_id = c.cust_id);
```

| cust_name |
|-----------|
| NoOrders Co |

`NOT EXISTS` is the safe anti-join — unlike `NOT IN`, it behaves correctly even
if the sub-query can produce `NULL`s (see
[06](./06-nulls-sets-and-gotchas.md)).
</details>

---

### Join cheatsheet

| Goal | Pattern |
|------|---------|
| Only matching rows | `INNER JOIN` |
| All left rows, matched or not | `LEFT JOIN` |
| Left rows with **no** match | `LEFT JOIN … WHERE right.pk IS NULL`, or `NOT EXISTS` |
| Filter the right side but keep all left rows | condition in **`ON`**, not `WHERE` |
| Rows related within one table | self-join (two aliases) |

Next: [03 — Aggregation & grouping](./03-aggregation-and-grouping.md)
