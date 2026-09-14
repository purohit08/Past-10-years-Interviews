# Meta / Facebook DE — Python coding warm-up

Four short problems from the prep sheet (CoderPad-style: write the function, hit
Run, asserts must pass). Only loops / lists / dicts are needed — no libraries.
Runnable solutions with the original asserts: [`python_coding.py`](./python_coding.py)
(`python3 python_coding.py` → `all asserts passed`).

---

**1. Return the elements at odd positions (0-based).** `[0,1,2,3,4,5] → [1,3,5]`

<details><summary>Solution</summary>

```python
def odd_positions(values):
    return values[1::2]      # start at index 1, step 2
```

Slice notation `[start:stop:step]` is the idiomatic one-liner. Longhand if asked
to avoid slicing: `[v for i, v in enumerate(values) if i % 2 == 1]`. O(n) time.
</details>

**2. Return the cumulative (running) sum.** `[1,1,1] → [1,2,3]`, `[1,-1,3] → [1,0,3]`

<details><summary>Solution</summary>

```python
def cumulative_sum(values):
    output, running = [], 0
    for x in values:
        running += x
        output.append(running)
    return output
```

Carry a running accumulator — don't re-sum a prefix each step (that would be
O(n²)). This is O(n). (`itertools.accumulate` does it in the stdlib, but the
point is to show the loop.)
</details>

**3. Turn a non-negative number into a list of its digits.** `123 → [1,2,3]`, `400 → [4,0,0]`

<details><summary>Solution</summary>

```python
def digits(n):
    return [int(ch) for ch in str(n)]
```

String route is cleanest and preserves leading-internal zeros (400 → 4,0,0).
Arithmetic route (`n % 10`, `n //= 10`) works too but yields digits in reverse —
remember to reverse, and to special-case `0`. Clarify whether negatives are in
scope.
</details>

**4. "Centered" average — mean ignoring one min and one max, integer division.**
Length ≥ 3. `[1,2,3,4,100] → 3`

<details><summary>Solution</summary>

```python
def centered_average(values):
    return (sum(values) - min(values) - max(values)) // (len(values) - 2)
```

Subtract exactly one smallest and one largest, then divide by the remaining
count. Verified: `[1,2,3,4,100]→3`, `[1,1,5,5,10,8,7]→5`, `[-10,-4,-2,-4,-2,0]→-3`.
Two edge cases interviewers probe: duplicate min/max (remove **one** copy, which
subtracting a single `min`/`max` does correctly), and Python's floor division on
negatives (`//` rounds toward −∞) — fine here, but say it out loud.
</details>

---

**Talking points that score:** state the time/space complexity, name the edge
cases (empty input, negatives, single element, duplicates), and prefer a clear
loop over a clever one-liner when the interviewer wants to see your reasoning.
