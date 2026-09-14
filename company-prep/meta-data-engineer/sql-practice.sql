-- =============================================================================
-- Meta / Facebook Data Engineer -- SQL phone-screen practice ("Salesperson" set)
-- Dialect: PostgreSQL.  Run:  psql -d sqlprep -f sql-practice.sql
--
-- The prompt sheet says "Given the tables above ...". Those tables are the
-- canonical dataset that ships with this well-known question set; it is
-- reproduced here so the questions are runnable and the answers verifiable.
-- =============================================================================

DROP TABLE IF EXISTS orders, customer, salesperson CASCADE;

CREATE TABLE salesperson (
    id     INT PRIMARY KEY,
    name   TEXT,
    age    INT,
    salary INT
);
INSERT INTO salesperson (id, name, age, salary) VALUES
    (1,  'Abe',   61, 140000),
    (2,  'Bob',   34,  44000),
    (5,  'Chris', 34,  40000),
    (7,  'Dan',   41,  52000),
    (8,  'Ken',   57, 115000),
    (11, 'Joe',   38,  38000);

CREATE TABLE customer (
    id            INT PRIMARY KEY,
    name          TEXT,
    city          TEXT,
    industry_type CHAR(1)
);
INSERT INTO customer (id, name, city, industry_type) VALUES
    (4, 'Samsonic', 'pleasant', 'J'),
    (6, 'Panasung', 'oaktown',  'J'),
    (7, 'Samony',   'jackson',  'B'),
    (9, 'Orange',   'Jackson',  'B');

CREATE TABLE orders (
    number         INT PRIMARY KEY,
    order_date     DATE,
    cust_id        INT REFERENCES customer(id),
    salesperson_id INT REFERENCES salesperson(id),
    amount         INT
);
INSERT INTO orders (number, order_date, cust_id, salesperson_id, amount) VALUES
    (10, DATE '1996-08-02', 4, 2,  540),
    (20, DATE '1999-01-30', 4, 8, 1800),
    (30, DATE '1995-07-14', 9, 1,  460),
    (40, DATE '1998-01-29', 7, 2, 2400),
    (50, DATE '1998-02-03', 6, 7,  600),
    (60, DATE '1998-03-02', 6, 7,  720),
    (70, DATE '1998-05-06', 9, 7,  150);

\pset footer off

\echo '--- (a) salespeople who HAVE an order with Samsonic ---'
SELECT DISTINCT s.name
FROM salesperson s
JOIN orders   o ON o.salesperson_id = s.id
JOIN customer c ON c.id = o.cust_id
WHERE c.name = 'Samsonic'
ORDER BY s.name;

\echo '--- (b) salespeople who do NOT have any order with Samsonic (anti-join) ---'
SELECT s.name
FROM salesperson s
WHERE NOT EXISTS (
    SELECT 1
    FROM orders o
    JOIN customer c ON c.id = o.cust_id
    WHERE o.salesperson_id = s.id AND c.name = 'Samsonic'
)
ORDER BY s.name;

\echo '--- (c) salespeople with 2 or more orders ---'
SELECT s.name, COUNT(*) AS n_orders
FROM salesperson s
JOIN orders o ON o.salesperson_id = s.id
GROUP BY s.id, s.name
HAVING COUNT(*) >= 2
ORDER BY n_orders DESC, s.name;

\echo '--- (d) name + age of salespeople earning >= 100000 ---'
SELECT name, age
FROM salesperson
WHERE salary >= 100000
ORDER BY salary DESC;

\echo '--- (e) salespeople who sold more than 1400 total ---'
SELECT s.name, SUM(o.amount) AS total_sold
FROM salesperson s
JOIN orders o ON o.salesperson_id = s.id
GROUP BY s.id, s.name
HAVING SUM(o.amount) > 1400
ORDER BY total_sold DESC;

\echo '--- (f) earliest and latest order made to Samony ---'
SELECT MIN(o.order_date) AS earliest, MAX(o.order_date) AS latest
FROM orders o
JOIN customer c ON c.id = o.cust_id
WHERE c.name = 'Samony';
