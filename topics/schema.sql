-- =============================================================================
-- Shared practice schema for the topic question sets in ../topics/*.md
-- Dialect: PostgreSQL (also runs on most engines with tiny tweaks).
--
-- Load it into a scratch database and try the questions yourself:
--   createdb sqlprep
--   psql -d sqlprep -f topics/schema.sql
--
-- The data is deliberately small so you can verify results by hand, but it is
-- seeded with the things interviewers probe: tie values (for RANK vs
-- DENSE_RANK vs ROW_NUMBER), a manager self-reference, rows with NULLs, a
-- department with no employees and a customer with no orders (for LEFT JOIN /
-- anti-join questions), and a login table with gaps (for "consecutive days").
-- =============================================================================

DROP TABLE IF EXISTS logins, events, orders, customers, employees, departments CASCADE;

CREATE TABLE departments (
    dept_id   INT PRIMARY KEY,
    dept_name TEXT NOT NULL
);

CREATE TABLE employees (
    emp_id     INT PRIMARY KEY,
    emp_name   TEXT NOT NULL,
    dept_id    INT REFERENCES departments(dept_id),  -- NULL = not yet assigned
    manager_id INT REFERENCES employees(emp_id),      -- NULL = top of the tree
    hire_date  DATE NOT NULL,
    salary     NUMERIC(10,2) NOT NULL
);

CREATE TABLE customers (
    cust_id     INT PRIMARY KEY,
    cust_name   TEXT NOT NULL,
    city        TEXT,
    signup_date DATE NOT NULL
);

CREATE TABLE orders (
    order_id   INT PRIMARY KEY,
    cust_id    INT REFERENCES customers(cust_id),
    order_date DATE NOT NULL,
    amount     NUMERIC(10,2) NOT NULL,
    status     TEXT NOT NULL          -- completed | cancelled | pending
);

CREATE TABLE events (
    event_id   INT PRIMARY KEY,
    cust_id    INT REFERENCES customers(cust_id),
    event_type TEXT NOT NULL,         -- view | cart | purchase
    event_ts   TIMESTAMP NOT NULL
);

CREATE TABLE logins (
    user_id    INT NOT NULL,
    login_date DATE NOT NULL,
    PRIMARY KEY (user_id, login_date)
);

-- ---- departments (Research has no employees on purpose) --------------------
INSERT INTO departments (dept_id, dept_name) VALUES
    (1, 'Engineering'),
    (2, 'Sales'),
    (3, 'Marketing'),
    (4, 'Finance'),
    (5, 'Research');

-- ---- employees -------------------------------------------------------------
-- Salaries include ties (Bob/Carol = 120000, Eve/Frank = 85000) and Niaj has
-- no department (dept_id NULL).
INSERT INTO employees (emp_id, emp_name, dept_id, manager_id, hire_date, salary) VALUES
    (1,  'Alice',   1, NULL, DATE '2015-03-01', 150000),
    (2,  'Bob',     1, 1,    DATE '2016-07-15', 120000),
    (3,  'Carol',   1, 1,    DATE '2018-01-20', 120000),
    (4,  'Dave',    2, 1,    DATE '2017-05-10', 90000),
    (5,  'Eve',     2, 4,    DATE '2019-09-01', 85000),
    (6,  'Frank',   2, 4,    DATE '2020-02-11', 85000),
    (7,  'Grace',   3, 1,    DATE '2016-11-30', 95000),
    (8,  'Heidi',   3, 7,    DATE '2021-06-01', 70000),
    (9,  'Ivan',    4, 1,    DATE '2015-08-22', 110000),
    (10, 'Judy',    4, 9,    DATE '2022-03-15', 60000),
    (11, 'Mallory', 1, 2,    DATE '2023-01-10', 80000),
    (12, 'Niaj', NULL, NULL, DATE '2023-04-01', 50000);

-- ---- customers (NoOrders Co never orders) ----------------------------------
INSERT INTO customers (cust_id, cust_name, city, signup_date) VALUES
    (1, 'ABC Corp',    'Dubai',     DATE '2023-01-05'),
    (2, 'XYZ Ltd',     'Dubai',     DATE '2023-02-10'),
    (3, 'PQR Inc',     'Abu Dhabi', DATE '2023-01-20'),
    (4, 'LMN LLC',     'Sharjah',   DATE '2023-03-15'),
    (5, 'NoOrders Co', 'Dubai',     DATE '2023-04-01');

-- ---- orders ----------------------------------------------------------------
INSERT INTO orders (order_id, cust_id, order_date, amount, status) VALUES
    (1,  1, DATE '2023-02-01', 500,  'completed'),
    (2,  1, DATE '2023-02-15', 300,  'completed'),
    (3,  1, DATE '2023-03-05', 200,  'cancelled'),
    (4,  2, DATE '2023-02-20', 1000, 'completed'),
    (5,  2, DATE '2023-04-10', 750,  'completed'),
    (6,  3, DATE '2023-01-25', 400,  'completed'),
    (7,  3, DATE '2023-05-01', 600,  'completed'),
    (8,  4, DATE '2023-03-20', 250,  'completed'),
    (9,  1, DATE '2023-05-12', 800,  'completed'),
    (10, 2, DATE '2023-05-30', 450,  'pending');

-- ---- events (a tiny view -> cart -> purchase funnel) -----------------------
INSERT INTO events (event_id, cust_id, event_type, event_ts) VALUES
    (1, 1, 'view',     TIMESTAMP '2023-05-01 09:00'),
    (2, 1, 'cart',     TIMESTAMP '2023-05-01 09:05'),
    (3, 1, 'purchase', TIMESTAMP '2023-05-01 09:10'),
    (4, 2, 'view',     TIMESTAMP '2023-05-01 10:00'),
    (5, 2, 'cart',     TIMESTAMP '2023-05-01 10:03'),
    (6, 3, 'view',     TIMESTAMP '2023-05-02 11:00'),
    (7, 4, 'view',     TIMESTAMP '2023-05-02 12:00'),
    (8, 4, 'cart',     TIMESTAMP '2023-05-02 12:04'),
    (9, 4, 'purchase', TIMESTAMP '2023-05-02 12:20');

-- ---- logins (gaps on purpose, for "consecutive days") ----------------------
-- user 1: Jun 1,2,3 then gap, 5,6 then gap, 9   (longest streak = 3)
-- user 2: Jun 1 then gap, 3,4,5                  (longest streak = 3)
INSERT INTO logins (user_id, login_date) VALUES
    (1, DATE '2023-06-01'), (1, DATE '2023-06-02'), (1, DATE '2023-06-03'),
    (1, DATE '2023-06-05'), (1, DATE '2023-06-06'),
    (1, DATE '2023-06-09'),
    (2, DATE '2023-06-01'),
    (2, DATE '2023-06-03'), (2, DATE '2023-06-04'), (2, DATE '2023-06-05');
