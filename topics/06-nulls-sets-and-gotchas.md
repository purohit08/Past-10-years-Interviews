# 06 — NULLs, sets & gotchas

The bugs interviewers *want* you to hit. Load [`schema.sql`](./schema.sql) first.
The employees table helps here: `dept_id` has one `NULL` (Niaj), and
`manager_id` is `NULL` for the two people at the top of the tree.

---

**1. `COUNT(*)` vs `COUNT(col)` vs `COUNT(DISTINCT col)`.**

<details><summary>Solution</summary>

```sql
SELECT COUNT(*)                 AS c_star,           -- 12 rows
       COUNT(dept_id)           AS c_dept,           -- 11 (Niaj's NULL skipped)
       COUNT(DISTINCT dept_id)  AS c_distinct_dept   -- 4 distinct departments
FROM employees;
```

| c_star | c_dept | c_distinct_dept |
|:------:|:------:|:---------------:|
| 12 | 11 | 4 |

`COUNT(*)` counts rows; `COUNT(col)` ignores `NULL`; `COUNT(DISTINCT col)` counts
distinct non-NULLs. Same lesson as the [Emirates NBD Q1](../real-interviews/emirates-nbd.md).
</details>

**2. The `NOT IN` + `NULL` trap.**

<details><summary>Solution</summary>

"Find employees who manage nobody." A natural first attempt:

```sql
-- ❌ returns ZERO rows
SELECT emp_name
FROM employees
WHERE emp_id NOT IN (SELECT manager_id FROM employees);
```

| emp_name |
|----------|
| *(empty)* |

`manager_id` contains `NULL`s, so the list is `{1, 4, 7, 9, 2, NULL, …}`.
`x NOT IN (…, NULL)` becomes `x <> NULL` somewhere, which is `unknown` — so **no
row ever qualifies**. `NOT EXISTS` (or `NOT IN` with a `WHERE … IS NOT NULL`
guard) fixes it:

```sql
-- ✅
SELECT e.emp_name
FROM employees e
WHERE NOT EXISTS (SELECT 1 FROM employees s WHERE s.manager_id = e.emp_id)
ORDER BY e.emp_id;
```

| emp_name |
|----------|
| Carol |
| Eve |
| Frank |
| Heidi |
| Judy |
| Mallory |
| Niaj |

**Reflex:** prefer `NOT EXISTS` for anti-joins — it is `NULL`-safe. `IN` /
`EXISTS` (the positive forms) don't have this problem.
</details>

**3. `UNION` vs `UNION ALL`.**

<details><summary>Solution</summary>

```sql
SELECT 1 AS x UNION     SELECT 2 UNION     SELECT 2;   -- 1, 2      (de-duplicated)
SELECT 1 AS x UNION ALL SELECT 2 UNION ALL SELECT 2;   -- 1, 2, 2   (kept)
```

`UNION` removes duplicates (and pays to sort/hash for it); `UNION ALL` keeps them
and is cheaper. Default to `UNION ALL` unless you specifically need de-duping.
Both require each side to have the same number of columns with compatible types.
Same lesson as [Emirates NBD Q2](../real-interviews/emirates-nbd.md).
</details>

**4. The `LEFT JOIN` + `WHERE` trap (the classic).**

<details><summary>Solution</summary>

Filtering the *right* table of a `LEFT JOIN` in `WHERE` silently turns it into an
`INNER JOIN`, dropping the unmatched left rows:

```sql
-- ❌ loses Research (0 employees) and any dept whose employees are all excluded
SELECT d.dept_name, COUNT(e.emp_id) AS engineers
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id
WHERE e.salary > 100000            -- NULL > 100000 is false → Research vanishes
GROUP BY d.dept_name;

-- ✅ push the predicate into ON to keep every department
SELECT d.dept_name, COUNT(e.emp_id) AS high_earners
FROM departments d
LEFT JOIN employees e ON e.dept_id = d.dept_id AND e.salary > 100000
GROUP BY d.dept_name
ORDER BY high_earners DESC, d.dept_name;
```

| dept_name | high_earners |
|-----------|:------------:|
| Engineering | 1 |
| Finance | 1 |
| Marketing | 0 |
| Research | 0 |
| Sales | 0 |

Full worked version in [Emirates NBD Q3c](../real-interviews/emirates-nbd.md).
Rule: **condition on the left/outer table → `WHERE`; condition on the right/inner
table when you still want all left rows → `ON`.**
</details>

**5. `AVG` ignores `NULL` — mind the denominator.**

<details><summary>Solution</summary>

```sql
SELECT COUNT(*)        AS rows_total,       -- 12
       COUNT(dept_id)  AS non_null_dept,    -- 11
       AVG(salary)     AS avg_salary        -- 92916.67
FROM employees;
```

| rows_total | non_null_dept | avg_salary |
|:----------:|:-------------:|:----------:|
| 12 | 11 | 92916.67 |

`AVG(col)` = `SUM(col) / COUNT(col)` over **non-NULL** values. If a `NULL` really
means "zero" for your metric, coalesce first — `AVG(COALESCE(col, 0))` — or the
average is computed over fewer rows than you think. Same for `SUM`: it skips
`NULL`, and `SUM` over an all-NULL/empty set is `NULL`, not `0`.
</details>

---

### Gotcha checklist

| Symptom | Cause | Fix |
|---------|-------|-----|
| Rows mysteriously missing | `WHERE` on right side of `LEFT JOIN` | move filter to `ON` |
| `NOT IN` returns nothing | `NULL` in the sub-query list | use `NOT EXISTS` |
| Counts too high with `LEFT JOIN` | `COUNT(*)` counts the all-NULL row | `COUNT(<right col>)` |
| Average "off" | `AVG` skips `NULL`s | `COALESCE` first if NULL means 0 |
| `x = NULL` matches nothing | `NULL` isn't equal to anything | `IS NULL` / `IS NOT NULL` |
| Dedupe you didn't want | `UNION` | `UNION ALL` |
| "First row" has duplicates | `RANK` on ties | `ROW_NUMBER` |
| Month order looks wrong | sorting a month **name** as text | order by a real date/number |

Back to the [topic index](../README.md#practice-by-topic).
