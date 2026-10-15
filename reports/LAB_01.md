# Assignment 1 report · Four ways to triage an issue

Every number here also goes in `reports/LAB_01.json`, which the checker reads
(format: `checks/FORMATS.md`, section 7). Give each number its run count. Mark
any vendor figure you cite with its source type and date.

## Part 0 · The recorded trace
Model calls, tool calls, prompt tokens and the cached share, first and last
prompt size, cumulative over first. One sentence on what the growth means.

**Answer:**
The recording has 21 model calls and 23 tool calls, and 399,123 prompt tokens
in all, of which 388,338 (0.973) were cache reads. The first call's prompt was
13,445 tokens and the last call's was 24,188, so cumulative prompt tokens were
29.69 times the first prompt (`eval/part0.py`).

Over 21 model calls the prompt grew from 13,445 to 24,188 tokens, but because
every step re-sends the whole history, the 399,123 prompt tokens cumulatively
read were 29.69 times the first prompt, 97.3% of them cache reads, so cost
grows faster than the step count and a step limit is a money limit.

## Part A · Your loop's bounds
Your three bounds and why. Your worst case: *F*, *A*, *N*, and the cumulative
prompt tokens at your turn limit.

**Answer:**
The loop (`agent/loop.py`) checks all three bounds in code before every model
call and calls `trace.end` exactly once. The values are in `agent/bounds.yaml`:

| Bound | Value | Why |
|---|---|---|
| `max_steps` | 10 | The task needs about 5 to 7 calls (read, two or three searches, post); 10 leaves headroom without letting a looping model run on. |
| `max_tokens` | 40,000 | Above the 24,000-token worst case at 10 steps, so the step limit binds first; far below the 400,000 harness ceiling. |
| `wall_clock_s` | 180 | Ten calls at 2 to 4 s is about 40 s; the rest covers free-tier rate-limit waits, which count toward latency. |

**Worst case, estimated before any run.** *F* ≈ 600 prompt tokens (system
prompt about 350, the three tool definitions about 190, the first message about
15, plus vendor overhead). *A* ≈ 400 tokens added per step (a tool call of about
40 plus a result of up to about 350 for `search_repo`). With *N* = 10, the
`cumulative_prompt_tokens` at the limit are N·F + A·N(N−1)/2 = 6,000 + 18,000 =
**24,000**. After Part B this estimate is replaced by values measured on the 60
evaluation agent runs.

`make bounds-smoke` (the scripted never-stopping model, free): both dev issues
made exactly 10 model calls and ended on `turn_limit`. The token budget did not
bind, because it sits above the worst case.

## Part B · Results
The table for all three ways: passes out of 60, per issue out of 10, the spread
(lowest and highest sweep), issues solved in every run, tokens, p50 and p95
latency, cost, tool calls.

**Answer:**

## Part C · The decision
1. Find the diamond, for each way.
2. Your multipliers, and two differences from the vendor's 4×.
3. *f*, the blended cost, and the comparison with all-agent and all-workflow;
   then the slide's version, with *c*, *m* and *f* against the direct call.
4. Path entropy.
5. The four gates, one line of evidence each, and your verdict: agent,
   workflow or hybrid. If hybrid, where the line sits.
6. Your predictions: each one in `reports/PREDICTIONS_01.md` that missed, what
   you believed, and which trace shows why it was wrong.
7. The seven-layer audit: how many layers are empty (`ARCHITECTURE.md`).

## Part D · The hybrid
Your hand-off rule, and the Part B traces that led you to it (written before you
measure). Its row beside the three ways (the same columns as Part B's table), how many of
its runs handed the issue to the agent, and its measured cost per run beside your
blended cost from Part C, item 3. Does it change your Part C verdict? Which of
the four would you ship, and why?

**Answer:**


## Assistance
Which AI tool, what it wrote, what you checked.

**Answer:**
I used Claude Code as a coding assistant. It helped me write the python code inside eval, agent, and the ways folder based on my approval and directions. I checked its code by running make test, make bounds-smoke, make check-01, and manual testing / checking with terminal. 