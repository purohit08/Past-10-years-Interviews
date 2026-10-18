# Amazon — matches played, won and lost (classic SQL problem)

> A well-known Amazon SQL screen question, often called the **ICC World Cup**
> problem. Small table, one twist: a team can appear in *either* of two
> columns. Runnable fixtures + verified output: [`matches-won-lost.sql`](./matches-won-lost.sql).

---

## The question

Given a table of matches, return each team's **matches played**, **wins** and
**losses**.

```
icc_world_cup
 team_1 | team_2 | winner
--------+--------+--------
 India  | SL     | India
 SL     | Aus    | Aus
 SA     | Eng    | Eng
 Eng    | NZ     | NZ
 Aus    | India  | India
```

**Expected output**

| team_name | matches_played | no_of_wins | no_of_losses |
|-----------|:--------------:|:----------:|:------------:|
| India     | 2 | 2 | 0 |
| Aus       | 2 | 1 | 1 |
| Eng       | 2 | 1 | 1 |
| NZ        | 1 | 1 | 0 |
| SA        | 1 | 0 | 1 |
| SL        | 2 | 0 | 2 |

---

## The idea

`GROUP BY team_1` only sees half the appearances. Turn the **wide** table
(one row per match) into a **long** one (one row per team per match) by
stacking `team_1` and `team_2`, flag whether that team won, then aggregate.

## Solution — `UNION ALL` + aggregate

```sql
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
```

### The trap: `UNION` instead of `UNION ALL`

`UNION` de-duplicates the stacked rows. India's two wins are two identical
`('India', 1)` rows, so they collapse into one — and so do SL's two
`('SL', 0)` losses. Both teams end up showing **1 match played**. No error,
just a wrong answer. When you are stacking rows that must all be counted,
`UNION ALL` is the only correct choice (and it's cheaper — no sort/hash).

## Alternative — join a team list to the matches

Build a distinct team list (here `UNION` *is* correct — you want each team once),
then join every match the team appears in:

```sql
WITH teams AS (
    SELECT team_1 AS team_name FROM icc_world_cup
    UNION
    SELECT team_2 FROM icc_world_cup
)
SELECT t.team_name,
       COUNT(*)                                                 AS matches_played,
       SUM(CASE WHEN m.winner = t.team_name THEN 1 ELSE 0 END)  AS no_of_wins,
       SUM(CASE WHEN m.winner <> t.team_name THEN 1 ELSE 0 END) AS no_of_losses
FROM teams t
JOIN icc_world_cup m
  ON t.team_name IN (m.team_1, m.team_2)
GROUP BY t.team_name
ORDER BY no_of_wins DESC, t.team_name;
```

Same output. Worth knowing, but the `UNION ALL` version is the one
interviewers expect — it scans the table twice instead of doing an `OR`-style join.

---

## Follow-up: draws and points

A common next question: *"Some matches are draws (`winner = 'Draw'`). Add a
draws column and a points table — 2 for a win, 1 for a draw."* Losses can no
longer be `played - wins`.

```sql
WITH all_teams AS (
    SELECT team_1 AS team_name, winner, team_1 = winner AS is_win FROM icc_world_cup_draws
    UNION ALL
    SELECT team_2,              winner, team_2 = winner          FROM icc_world_cup_draws
)
SELECT team_name,
       COUNT(*)                                                AS matches_played,
       COUNT(*) FILTER (WHERE is_win)                          AS no_of_wins,
       COUNT(*) FILTER (WHERE winner = 'Draw')                 AS no_of_draws,
       COUNT(*) FILTER (WHERE NOT is_win AND winner <> 'Draw') AS no_of_losses,
       2 * COUNT(*) FILTER (WHERE is_win)
         + COUNT(*) FILTER (WHERE winner = 'Draw')             AS points
FROM all_teams
GROUP BY team_name
ORDER BY points DESC, team_name;
```

With one extra match `SA vs NZ → Draw`:

| team_name | played | wins | draws | losses | points |
|-----------|:------:|:----:|:-----:|:------:|:------:|
| India | 2 | 2 | 0 | 0 | 4 |
| NZ    | 2 | 1 | 1 | 0 | 3 |
| Aus   | 2 | 1 | 0 | 1 | 2 |
| Eng   | 2 | 1 | 0 | 1 | 2 |
| SA    | 2 | 0 | 1 | 1 | 1 |
| SL    | 2 | 0 | 0 | 2 | 0 |

> **Dialect note:** `FILTER (WHERE …)` is PostgreSQL. On SQL Server / MySQL /
> Oracle use `SUM(CASE WHEN … THEN 1 ELSE 0 END)` instead. If draws are stored
> as `winner IS NULL`, compare with `IS NULL` — `winner = 'Draw'` and
> `winner <> team` both evaluate to NULL (not true) for a NULL winner.

---

## Takeaways

- **Wide → long** with `UNION ALL` is the core move whenever an entity can sit in
  more than one column (home/away team, sender/receiver, caller/callee).
- **`UNION ALL`, not `UNION`**, when every stacked row must be counted.
- Derive losses as `played - wins` only when there are exactly two outcomes;
  once draws appear, count each outcome explicitly.
