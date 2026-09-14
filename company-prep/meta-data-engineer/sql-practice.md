# Meta / Facebook DE — SQL practice ("Salesperson" set)

Six questions from the DE phone-screen prep sheet. The prompt says *"Given the
tables above…"*; those tables are the canonical dataset that ships with this
well-known set, reproduced here so everything runs. Load it and try the
questions cold: `psql -d sqlprep -f sql-practice.sql` (see
[`sql-practice.sql`](./sql-practice.sql)). Outputs below are verified.

### The data

**salesperson**

| id | name | age | salary |
|---:|------|----:|-------:|
| 1 | Abe | 61 | 140000 |
| 2 | Bob | 34 | 44000 |
| 5 | Chris | 34 | 40000 |
| 7 | Dan | 41 | 52000 |
| 8 | Ken | 57 | 115000 |
| 11 | Joe | 38 | 38000 |

**customer**

| id | name | city | industry_type |
|---:|------|------|:-------------:|
| 4 | Samsonic | pleasant | J |
| 6 | Panasung | oaktown | J |
| 7 | Samony | jackson | B |
| 9 | Orange | Jackson | B |

**orders**

| number | order_date | cust_id | salesperson_id | amount |
|-------:|------------|:-------:|:--------------:|-------:|
| 10 | 1996-08-02 | 4 | 2 | 540 |
| 20 | 1999-01-30 | 4 | 8 | 1800 |
| 30 | 1995-07-14 | 9 | 1 | 460 |
| 40 | 1998-01-29 | 7 | 2 | 2400 |
| 50 | 1998-02-03 | 6 | 7 | 600 |
| 60 | 1998-03-02 | 6 | 7 | 720 |
| 70 | 1998-05-06 | 9 | 7 | 150 |

---

**(a) Names of all salespeople who have an order with Samsonic.**

<details><summary>Solution</summary>

```sql
SELECT DISTINCT s.name
FROM salesperson s
JOIN orders   o ON o.salesperson_id = s.id
JOIN customer c ON c.id = o.cust_id
WHERE c.name = 'Samsonic'
ORDER BY s.name;
```

| name | | Samsonic (id 4) was sold to on orders 10 (Bob) and 20 (Ken). |
|------|-|---|
| Bob  | | `DISTINCT` guards against a salesperson having *multiple* Samsonic orders. |
| Ken  | | |
</details>

**(b) Names of all salespeople who do NOT have any order with Samsonic.**

<details><summary>Solution</summary>

```sql
SELECT s.name
FROM salesperson s
WHERE NOT EXISTS (
    SELECT 1 FROM orders o
    JOIN customer c ON c.id = o.cust_id
    WHERE o.salesperson_id = s.id AND c.name = 'Samsonic'
)
ORDER BY s.name;
```

| name |
|------|
| Abe |
| Chris |
| Dan |
| Joe |

The **anti-join**. `NOT EXISTS` is the safe choice — a `NOT IN (SELECT
salesperson_id …)` would break if that column could be `NULL`
([why](../../topics/06-nulls-sets-and-gotchas.md)).
</details>

**(c) Names of salespeople with 2 or more orders.**

<details><summary>Solution</summary>

```sql
SELECT s.name, COUNT(*) AS n_orders
FROM salesperson s
JOIN orders o ON o.salesperson_id = s.id
GROUP BY s.id, s.name
HAVING COUNT(*) >= 2
ORDER BY n_orders DESC, s.name;
```

| name | n_orders |
|------|:--------:|
| Dan | 3 |
| Bob | 2 |

Count-then-filter-groups → `HAVING`. Group by `s.id` (the key) and carry
`s.name` along.
</details>

**(d) Names and ages of salespeople with a salary of 100,000 or more.**

<details><summary>Solution</summary>

```sql
SELECT name, age
FROM salesperson
WHERE salary >= 100000
ORDER BY salary DESC;
```

| name | age |
|------|:---:|
| Abe | 61 |
| Ken | 57 |
</details>

**(e) Which salespeople sold more than 1400 in total?**

<details><summary>Solution</summary>

```sql
SELECT s.name, SUM(o.amount) AS total_sold
FROM salesperson s
JOIN orders o ON o.salesperson_id = s.id
GROUP BY s.id, s.name
HAVING SUM(o.amount) > 1400
ORDER BY total_sold DESC;
```

| name | total_sold |
|------|-----------:|
| Bob | 2940 |
| Ken | 1800 |
| Dan | 1470 |

Filter on the aggregate `SUM(...)` in `HAVING`. Dan just clears the bar
(600+720+150 = 1470).
</details>

**(f) When was the earliest and latest order made to Samony?**

<details><summary>Solution</summary>

```sql
SELECT MIN(o.order_date) AS earliest, MAX(o.order_date) AS latest
FROM orders o
JOIN customer c ON c.id = o.cust_id
WHERE c.name = 'Samony';
```

| earliest | latest |
|----------|--------|
| 1998-01-29 | 1998-01-29 |

Samony (id 7) has exactly one order, so earliest = latest — a fine chance to note
that `MIN`/`MAX` handle a single-row (or empty → `NULL`) group without error.
</details>

---

**Patterns exercised:** many-to-many join across three tables (a), anti-join
(b), `GROUP BY … HAVING COUNT` (c), simple filter/projection (d),
`GROUP BY … HAVING SUM` (e), `MIN`/`MAX` (f). More reps by topic in
[`../../topics/`](../../topics/).
