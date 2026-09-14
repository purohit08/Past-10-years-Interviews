"""
Meta / Facebook Data Engineer -- Python coding warm-up (CoderPad style).

Four short problems from the prep sheet, each with a clean solution and the
original asserts. Run it directly to check every solution:

    python3 python_coding.py

If nothing prints and the process exits 0, all asserts passed.
Familiarity expected: loops, lists, dicts -- no external libraries.
"""


# ---------------------------------------------------------------------------
# 1. Return the elements on odd positions (0-based) in a list.
#    [0,1,2,3,4,5] -> [1,3,5]   (indices 1,3,5)
# ---------------------------------------------------------------------------
def odd_positions(values):
    # slice start=1, step=2 -> indices 1,3,5,...
    return values[1::2]


# ---------------------------------------------------------------------------
# 2. Return the cumulative (running) sum of a list.
#    [1,1,1] -> [1,2,3]
# ---------------------------------------------------------------------------
def cumulative_sum(values):
    output, running = [], 0
    for x in values:
        running += x
        output.append(running)
    return output


# ---------------------------------------------------------------------------
# 3. Take a non-negative number and return the list of its digits.
#    123 -> [1,2,3]
# ---------------------------------------------------------------------------
def digits(n):
    return [int(ch) for ch in str(n)]


# ---------------------------------------------------------------------------
# 4. "Centered" average: mean of the values ignoring exactly one copy of the
#    smallest and one copy of the largest value; use integer division.
#    Array length is >= 3.
# ---------------------------------------------------------------------------
def centered_average(values):
    return (sum(values) - min(values) - max(values)) // (len(values) - 2)


if __name__ == "__main__":
    assert odd_positions([0, 1, 2, 3, 4, 5]) == [1, 3, 5]
    assert odd_positions([1, -1, 2, -2]) == [-1, -2]

    assert cumulative_sum([1, 1, 1]) == [1, 2, 3]
    assert cumulative_sum([1, -1, 3]) == [1, 0, 3]

    assert digits(123) == [1, 2, 3]
    assert digits(400) == [4, 0, 0]

    assert centered_average([1, 2, 3, 4, 100]) == 3
    assert centered_average([1, 1, 5, 5, 10, 8, 7]) == 5
    assert centered_average([-10, -4, -2, -4, -2, 0]) == -3

    print("all asserts passed")
