# Emirates NBD — SQL interview (banking / client analytics)

> Real interview, ~1 hour. Whiteboard-style: predict query output, then write
> queries against a small customer / account / P&L schema. Reproduced here from
> memory. Runnable fixtures + verified output: [`emirates-nbd.sql`](./emirates-nbd.sql).

The whole session is built on three ideas interviewers love because a shaky
candidate gets them wrong: **how `COUNT` treats `NULL`**, **`UNION` vs
`UNION ALL`**, and **what a `WHERE` filter does to a `LEFT JOIN`**. Get those
three right and you clear most banking SQL screens.

---

## Round 1 — "What does this return?"

### Q1. `COUNT` and `NULL`

```
t_count
 id | amount
----+--------
  1 |    100
  2 |   NULL
  3 |    100
```

What do these return?

```sql
SELECT COUNT(*), COUNT(amount), COUNT(DISTINCT amount) FROM t_count;
```

| `COUNT(*)` | `COUNT(amount)` | `COUNT(DISTINCT amount)` |
|:----------:|:---------------:|:------------------------:|
| **3**      | **2**           | **1**                    |

- `COUNT(*)` counts **rows** — 3.
- `COUNT(amount)` counts **non-NULL values** of the column — the NULL in row 2 is skipped, so 2.
- `COUNT(DISTINCT amount)` counts **distinct non-NULL values** — only `100`, so 1.

**The trap:** the interviewer offered `3,3,2` and `3,error,error` as options.
Both are wrong. `COUNT(col)` never errors on NULL — it just ignores it. The
answer is **`3, 2, 1`**. Every aggregate except `COUNT(*)` ignores NULLs
(`SUM`, `AVG`, `MIN`, `MAX` too) — and `AVG` divides by the non-NULL count, not
the row count.

### Q2. `UNION` vs `UNION ALL`

```
A = {1, 2, 3}      B = {3, 4, 5}
```

| Operator    | Result            | Why |
|-------------|-------------------|-----|
| `UNION`     | `1, 2, 3, 4, 5`   | de-duplicates the combined set — the shared `3` appears once |
| `UNION ALL` | `1, 2, 3, 3, 4, 5`| keeps everything — the `3` appears twice |

`UNION` has to sort/hash to remove duplicates, so it costs more. **When you know
the inputs are disjoint (or you want the duplicates), use `UNION ALL`** — it is
cheaper and it is the correct default in ETL where you are concatenating
partitions.

---

## Round 2 — customer / account / P&L

```
customer                account                                pnl
 c_id | customer_name    acct_id | c_id | product | balance     c_id | month | revenue | cost | pnl
------+--------------    --------+------+---------+---------    ------+-------+---------+------+-----
 C1   | ABC              A1      | C1   | CASA    |   50000     C1   | Jan   |    1000 |  300 | 700
 C2   | XYZ              A2      | C1   | LOAN    |   20000     C1   | Feb   |    1200 |  400 | 800
 C3   | PQR              A3      | C2   | CASA    |   30000     C2   | Jan   |     800 |  500 | 300
```

Note the shape of the data — it drives every answer below:
- **C1** has two P&L rows (Jan, Feb).
- **C2** has one (Jan).
- **C3** has **no** P&L row at all. Keeping C3 in the result is the whole game.

### Q3a. Every customer with their P&L value

```sql
SELECT c.c_id, p.pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id;
```

| c_id | pnl  |
|------|------|
| C1   | 700  |
| C1   | 800  |
| C2   | 300  |
| C3   | NULL |

`LEFT JOIN` keeps all three customers. C1 fans out to two rows (one per P&L
month); C3 has no match so its `pnl` is `NULL`. An `INNER JOIN` here would
silently drop C3.

### Q3b. Total P&L per customer

```sql
SELECT c.c_id, SUM(p.pnl) AS total_pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id
GROUP BY c.c_id;
```

| c_id | total_pnl |
|------|-----------|
| C1   | 1500      |
| C2   | 300       |
| C3   | NULL      |

C1 collapses back to one row: `700 + 800 = 1500`. C3 stays with `SUM(NULL) =
NULL` (use `COALESCE(SUM(p.pnl), 0)` if you want `0`).

### Q3c. P&L for the month of January — *for every customer* ⚠️

The obvious answer is wrong:

```sql
-- ❌ drops C3
SELECT c.c_id, SUM(p.pnl) AS jan_pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id
WHERE p.month = 'Jan'
GROUP BY c.c_id;
```

| c_id | jan_pnl |
|------|---------|
| C1   | 700     |
| C2   | 300     |

**C3 disappeared.** C3's `LEFT JOIN` produced a row with `p.month = NULL`, and
`NULL = 'Jan'` is **not true**, so `WHERE` filters it out. A `WHERE` condition
on the *right* table of a `LEFT JOIN` quietly turns it into an `INNER JOIN`.

The fix is to move the filter into the `ON` clause, so it constrains the match
without discarding unmatched left rows:

```sql
-- ✅ keeps C3
SELECT c.c_id, SUM(p.pnl) AS jan_pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id AND p.month = 'Jan'
GROUP BY c.c_id;
```

| c_id | jan_pnl |
|------|---------|
| C1   | 700     |
| C2   | 300     |
| C3   | NULL    |

**Rule of thumb:** filtering the *left* table → `WHERE` is fine. Filtering the
*right* table but you still want all left rows → put it in `ON`. (If you do want
an inner join, the `WHERE` version is correct and clearer — know which you mean.)

### Q3d. Each customer's first month of P&L (window function)

The interviewer's own answer had a subtle bug worth understanding:

```sql
-- ❌ naive: ranks by the month *string*
WITH cte AS (
    SELECT c.c_id, p.pnl,
           RANK() OVER (PARTITION BY c.c_id ORDER BY p.month) AS rn
    FROM customer c
    LEFT JOIN pnl p ON c.c_id = p.c_id
)
SELECT c_id, pnl FROM cte WHERE rn = 1;
```

`ORDER BY p.month` sorts the **text** `'Jan'`, `'Feb'` — and `'Feb' < 'Jan'`
alphabetically. So for C1 the row ranked `1` is **February (800)**, not the
first calendar month. Two bugs in one:

1. **Ordering a month *name* is alphabetical, not chronological.** Store a real
   date or a month number, or map the name (`to_date(p.month,'Mon')`).
2. **`RANK` vs `ROW_NUMBER`.** With a tie, `RANK` returns *every* tied row at
   `rn = 1` (you would get duplicates); `ROW_NUMBER` guarantees exactly one.
   For "the single first row per group," reach for `ROW_NUMBER`.

```sql
-- ✅ order by a real month value, one row per customer
WITH cte AS (
    SELECT c.c_id, p.month, p.pnl,
           ROW_NUMBER() OVER (PARTITION BY c.c_id
                              ORDER BY to_date(p.month,'Mon')) AS rn
    FROM customer c
    LEFT JOIN pnl p ON c.c_id = p.c_id
)
SELECT c_id, month, pnl FROM cte WHERE rn = 1;
```

| c_id | month | pnl  |
|------|-------|------|
| C1   | Jan   | 700  |
| C2   | Jan   | 300  |
| C3   | NULL  | NULL |

---

## Takeaways

| # | Lesson |
|---|--------|
| 1 | `COUNT(*)` counts rows; `COUNT(col)` and every other aggregate ignore `NULL`. `COUNT(DISTINCT col)` de-dupes non-NULLs. |
| 2 | `UNION` de-duplicates (and sorts/hashes to do it); `UNION ALL` keeps duplicates and is cheaper — the right default when inputs are disjoint. |
| 3 | A `WHERE` on the right table of a `LEFT JOIN` turns it into an `INNER JOIN`. Put the filter in `ON` to keep unmatched left rows. |
| 4 | Never sort by a month *name* and expect calendar order — convert to a date/number. |
| 5 | "First/top row per group" → `ROW_NUMBER`, not `RANK` (RANK duplicates on ties). |

Related drills: [`../topics/06-nulls-sets-and-gotchas.md`](../topics/06-nulls-sets-and-gotchas.md)
and [`../topics/05-window-functions.md`](../topics/05-window-functions.md).
