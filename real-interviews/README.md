# Real interviews

Write-ups of actual SQL interviews — the exact questions asked, worked
solutions, and the traps behind each one. Every query is runnable and its
output verified against PostgreSQL.

| Interview | Focus | Files |
|-----------|-------|-------|
| **Emirates NBD** — banking / client analytics | `COUNT` + `NULL`, `UNION` vs `UNION ALL`, the `LEFT JOIN` + `WHERE` trap, first-row window functions | [write-up](./emirates-nbd.md) · [SQL](./emirates-nbd.sql) |

## Adding a new one

1. Copy the shape of `emirates-nbd.md`: **context → questions → worked answers →
   takeaways**.
2. Put the schema, seed data, and every query in a companion `.sql` so the
   write-up is reproducible. Paste expected output as comments.
3. Validate before committing:
   ```bash
   createdb sqlprep 2>/dev/null
   psql -d sqlprep -f real-interviews/<name>.sql
   ```
4. Anonymise anything confidential — keep the *SQL lesson*, drop real customer
   data, employee names, and internal identifiers.
