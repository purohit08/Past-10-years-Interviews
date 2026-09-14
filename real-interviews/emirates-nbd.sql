-- =============================================================================
-- Emirates NBD -- SQL interview (banking / client analytics)
-- Runnable companion to emirates-nbd.md.  Dialect: PostgreSQL.
--   createdb sqlprep && psql -d sqlprep -f real-interviews/emirates-nbd.sql
-- Expected outputs are shown as comments after each query.
-- =============================================================================

DROP TABLE IF EXISTS t_count, customer, account, pnl CASCADE;

-- ---- Q1 fixture: counting with NULLs ---------------------------------------
CREATE TABLE t_count (id INT, amount INT);
INSERT INTO t_count VALUES (1, 100), (2, NULL), (3, 100);

-- ---- Q3 fixtures: customer / account / pnl ---------------------------------
CREATE TABLE customer (c_id TEXT, customer_name TEXT);
INSERT INTO customer VALUES ('C1','ABC'), ('C2','XYZ'), ('C3','PQR');

CREATE TABLE account (acct_id TEXT, c_id TEXT, product TEXT, balance NUMERIC);
INSERT INTO account VALUES
    ('A1','C1','CASA',50000), ('A2','C1','LOAN',20000), ('A3','C2','CASA',30000);

CREATE TABLE pnl (c_id TEXT, month TEXT, revenue NUMERIC, cost NUMERIC, pnl NUMERIC);
INSERT INTO pnl VALUES
    ('C1','Jan',1000,300,700), ('C1','Feb',1200,400,800), ('C2','Jan',800,500,300);

\pset footer off

-- Q1 -------------------------------------------------------------------------
\echo 'Q1: COUNT(*) vs COUNT(amount) vs COUNT(DISTINCT amount)'
SELECT COUNT(*)                 AS count_star,           -- 3  (all rows)
       COUNT(amount)            AS count_amount,         -- 2  (NULL not counted)
       COUNT(DISTINCT amount)   AS count_distinct_amount -- 1  (only value 100)
FROM t_count;

-- Q2 -------------------------------------------------------------------------
\echo 'Q2: UNION removes the duplicate 3; UNION ALL keeps it'
SELECT x FROM (VALUES (1),(2),(3)) a(x)
UNION
SELECT x FROM (VALUES (3),(4),(5)) b(x)
ORDER BY x;                                              -- 1,2,3,4,5

SELECT x FROM (VALUES (1),(2),(3)) a(x)
UNION ALL
SELECT x FROM (VALUES (3),(4),(5)) b(x)
ORDER BY x;                                              -- 1,2,3,3,4,5

-- Q3a ------------------------------------------------------------------------
\echo 'Q3a: every customer with each pnl row (LEFT JOIN keeps C3 as NULL)'
SELECT c.c_id, p.pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id
ORDER BY c.c_id, p.month;
-- C1|800  C1|700  C2|300  C3|(null)

-- Q3b ------------------------------------------------------------------------
\echo 'Q3b: total pnl per customer'
SELECT c.c_id, SUM(p.pnl) AS total_pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id
GROUP BY c.c_id
ORDER BY c.c_id;
-- C1|1500  C2|300  C3|(null)

-- Q3c ------------------------------------------------------------------------
\echo 'Q3c WRONG: WHERE p.month = ''Jan'' silently drops C3 (turns LEFT into INNER)'
SELECT c.c_id, SUM(p.pnl) AS jan_pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id
WHERE p.month = 'Jan'
GROUP BY c.c_id
ORDER BY c.c_id;
-- C1|700  C2|300           <-- C3 is gone

\echo 'Q3c RIGHT: move the filter into the ON clause to keep every customer'
SELECT c.c_id, SUM(p.pnl) AS jan_pnl
FROM customer c
LEFT JOIN pnl p ON c.c_id = p.c_id AND p.month = 'Jan'
GROUP BY c.c_id
ORDER BY c.c_id;
-- C1|700  C2|300  C3|(null)

-- Q3d ------------------------------------------------------------------------
\echo 'Q3d NAIVE: ORDER BY month (text) sorts Feb before Jan -- picks the wrong row!'
WITH cte AS (
    SELECT c.c_id, p.month, p.pnl,
           RANK() OVER (PARTITION BY c.c_id ORDER BY p.month) AS rn
    FROM customer c
    LEFT JOIN pnl p ON c.c_id = p.c_id
)
SELECT c_id, month, pnl, rn FROM cte ORDER BY c_id, rn;
-- C1|Feb|800|1  C1|Jan|700|2  C2|Jan|300|1  C3|(null)|(null)|1

\echo 'Q3d FIXED: order by a real month value; ROW_NUMBER avoids tie duplicates'
WITH cte AS (
    SELECT c.c_id, p.month, p.pnl,
           ROW_NUMBER() OVER (PARTITION BY c.c_id ORDER BY to_date(p.month,'Mon')) AS rn
    FROM customer c
    LEFT JOIN pnl p ON c.c_id = p.c_id
)
SELECT c_id, month, pnl FROM cte WHERE rn = 1 ORDER BY c_id;
-- C1|Jan|700  C2|Jan|300  C3|(null)|(null)
