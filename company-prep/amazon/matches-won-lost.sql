-- =============================================================================
-- Amazon -- classic SQL problem: matches played / won / lost per team
-- Runnable companion to matches-won-lost.md.  Dialect: PostgreSQL.
--   createdb sqlprep && psql -d sqlprep -f company-prep/amazon/matches-won-lost.sql
-- Expected outputs are shown as comments after each query.
-- =============================================================================

DROP TABLE IF EXISTS icc_world_cup, icc_world_cup_draws CASCADE;

CREATE TABLE icc_world_cup (team_1 TEXT, team_2 TEXT, winner TEXT);
INSERT INTO icc_world_cup VALUES
    ('India', 'SL',    'India'),
    ('SL',    'Aus',   'Aus'),
    ('SA',    'Eng',   'Eng'),
    ('Eng',   'NZ',    'NZ'),
    ('Aus',   'India', 'India');

\pset footer off

-- Q1 -------------------------------------------------------------------------
\echo 'Q1: matches played, won and lost per team (UNION ALL approach)'
WITH all_teams AS (
    SELECT team_1 AS team_name,
           CASE WHEN team_1 = winner THEN 1 ELSE 0 END AS win_flag
    FROM icc_world_cup
    UNION ALL
    SELECT team_2 AS team_name,
           CASE WHEN team_2 = winner THEN 1 ELSE 0 END AS win_flag
    FROM icc_world_cup
)
SELECT team_name,
       COUNT(*)                 AS matches_played,
       SUM(win_flag)            AS no_of_wins,
       COUNT(*) - SUM(win_flag) AS no_of_losses
FROM all_teams
GROUP BY team_name
ORDER BY no_of_wins DESC, team_name;
--  team_name | matches_played | no_of_wins | no_of_losses
-- -----------+----------------+------------+--------------
--  India     |              2 |          2 |            0
--  Aus       |              2 |          1 |            1
--  Eng       |              2 |          1 |            1
--  NZ        |              1 |          1 |            0
--  SA        |              1 |          0 |            1
--  SL        |              2 |          0 |            2

-- Q1 trap --------------------------------------------------------------------
\echo 'Q1 trap: UNION (not ALL) silently drops matches'
WITH all_teams AS (
    SELECT team_1 AS team_name,
           CASE WHEN team_1 = winner THEN 1 ELSE 0 END AS win_flag
    FROM icc_world_cup
    UNION                                   -- <-- de-duplicates rows!
    SELECT team_2 AS team_name,
           CASE WHEN team_2 = winner THEN 1 ELSE 0 END AS win_flag
    FROM icc_world_cup
)
SELECT team_name, COUNT(*) AS matches_played, SUM(win_flag) AS no_of_wins
FROM all_teams
GROUP BY team_name
ORDER BY team_name;
-- India's two wins collapse into one ('India',1) row, SL's two losses into one
-- ('SL',0) row -- so India and SL both show matches_played = 1. Wrong.
--  team_name | matches_played | no_of_wins
-- -----------+----------------+------------
--  Aus       |              2 |          1
--  Eng       |              2 |          1
--  India     |              1 |          1
--  NZ        |              1 |          1
--  SA        |              1 |          0
--  SL        |              1 |          0

-- Q2 -------------------------------------------------------------------------
\echo 'Q2: alternative -- join a distinct team list to the matches'
WITH teams AS (
    SELECT team_1 AS team_name FROM icc_world_cup
    UNION                                   -- distinct team list: UNION is right here
    SELECT team_2 FROM icc_world_cup
)
SELECT t.team_name,
       COUNT(*)                                          AS matches_played,
       SUM(CASE WHEN m.winner = t.team_name THEN 1 ELSE 0 END) AS no_of_wins,
       SUM(CASE WHEN m.winner <> t.team_name THEN 1 ELSE 0 END) AS no_of_losses
FROM teams t
JOIN icc_world_cup m
  ON t.team_name IN (m.team_1, m.team_2)
GROUP BY t.team_name
ORDER BY no_of_wins DESC, t.team_name;
-- Same output as Q1.

-- Q3 -------------------------------------------------------------------------
\echo 'Q3 follow-up: draws (winner = ''Draw'') and points (2 win, 1 draw)'
CREATE TABLE icc_world_cup_draws (team_1 TEXT, team_2 TEXT, winner TEXT);
INSERT INTO icc_world_cup_draws
SELECT * FROM icc_world_cup
UNION ALL
SELECT 'SA', 'NZ', 'Draw';

WITH all_teams AS (
    SELECT team_1 AS team_name, winner, team_1 = winner AS is_win FROM icc_world_cup_draws
    UNION ALL
    SELECT team_2,              winner, team_2 = winner          FROM icc_world_cup_draws
)
SELECT team_name,
       COUNT(*)                                       AS matches_played,
       COUNT(*) FILTER (WHERE is_win)                 AS no_of_wins,
       COUNT(*) FILTER (WHERE winner = 'Draw')        AS no_of_draws,
       COUNT(*) FILTER (WHERE NOT is_win AND winner <> 'Draw') AS no_of_losses,
       2 * COUNT(*) FILTER (WHERE is_win)
         + COUNT(*) FILTER (WHERE winner = 'Draw')    AS points
FROM all_teams
GROUP BY team_name
ORDER BY points DESC, team_name;
--  team_name | matches_played | no_of_wins | no_of_draws | no_of_losses | points
-- -----------+----------------+------------+-------------+--------------+--------
--  India     |              2 |          2 |           0 |            0 |      4
--  NZ        |              2 |          1 |           1 |            0 |      3
--  Aus       |              2 |          1 |           0 |            1 |      2
--  Eng       |              2 |          1 |           0 |            1 |      2
--  SA        |              2 |          0 |           1 |            1 |      1
--  SL        |              2 |          0 |           0 |            2 |      0
