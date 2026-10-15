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

**Worst case, measured on the 60 evaluation agent runs.** *F* = 526 (the mean
`prompt_tokens` of the first call) and *A* ≈ 137 (the mean increase in
`prompt_tokens` from one call to the next, rounded). With *N* = 10 this gives
N·F + A·N(N−1)/2 = 5,260 + 6,165 = **11,425** (`worst_case` in
`LAB_01.json`). The estimate was too high, mostly in *A* (400 against 137),
because the tool results were shorter than the 350 tokens I allowed for. Both
are far below the 40,000 token bound, so the step limit still binds first.

`make bounds-smoke` (the scripted never-stopping model, free): both dev issues
made exactly 10 model calls and ended on `turn_limit`. The token budget did not
bind, because it sits above the worst case.

## Part B · Results
The table for all three ways: passes out of 60, per issue out of 10, the spread
(lowest and highest sweep), issues solved in every run, tokens, p50 and p95
latency, cost, tool calls.

**Answer:**
Each way ran the six evaluation issues ten times (60 runs) on `gemini-3.5-flash-lite`.
Success is decided by `eval/check_triage.py`: exactly one comment on the issue
with the run's id, and its label and file both match the answer.

| | Direct | Workflow | Agent |
|---|---|---|---|
| Passes (of 60) | 37 | 23 | 29 |
| 4201 (of 10) | 7 | 10 | 10 |
| 4202 | 10 | 0 | 0 |
| 4203 | 10 | 3 | 10 |
| 4204 | 0 | 0 | 0 |
| 4205 | 10 | 10 | 9 |
| 4206 | 0 | 0 | 0 |
| Lowest / highest sweep (of 6) | 3 / 4 | 2 / 3 | 2 / 3 |
| Issues solved in all 10 runs | 3 | 2 | 2 |
| Mean prompt tokens per run | 1,144 | 995 | 6,506 |
| Mean output tokens per run | 12 | 16 | 127 |
| Mean cached tokens per run | 0 | 0 | 0 |
| p50 latency | 0.73 s | 2.60 s | 19.5 s |
| p95 latency | 2.1 s | 47.4 s | 72.8 s |
| Mean cost per run | $0.00037 | $0.00034 | $0.00227 |
| Tool calls, mean (max) | 2.0 (2) | 4.8 (5) | 5.9 (10) |

Cached tokens were 0 on every call for all three ways, so the prompt tokens
above are all uncached. Gemini caches repeated prompts automatically, but these
prompts (at most 2,199 tokens) were too short to be cached; a test with a
5,505-token prompt showed 3,468 cached tokens on the repeat. Costs are priced from `pricing.yaml` (read 2026-10-14).

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

**Answer:**

**1. The diamond.** In all three ways nobody approves anything. The comment goes
straight to the tracker, so none of them is a chatbot or a copilot. What changes
from one way to the next is who decides what happens next, and who decides the
run is over.

With the direct call, it's just a script. My code reads the issue, asks the
model once and posts the comment. There's no next step to choose, and my code
ends it (all 60 runs `completed`). The model only writes the label and the file.

The workflow is still my code's call. I fixed the order myself: read the issue,
get search terms, search, choose, post. The model fills in two of those steps,
the search terms and the label and file, but it never picks what comes next, and
my code ends it (all 60 `completed`). I also cap it at three searches.

The agent is where the model takes over. It picks the next tool each time and
posts the comment itself. It decides when to stop too, and it did in 44 of the
60 runs (`model_stopped`). In the other 16 my code had to cut it off at the
`turn_limit`, and none of those 16 passed.

So the agent really has two diamonds. The limits in `agent/loop.py` (steps,
tokens and time) are checked by my code before every call, so my code decides
the latest point a run can end. Inside those limits, the model decides what to
call and when it's done.

**2. My multipliers.** Over 60 runs each, the agent used 6,633 tokens per run
(6,506 prompt plus 127 output) and the direct call used 1,156 (1,144 plus 12).
That makes the agent **5.74×** the direct call. The lecture says about 4×
(slide 30, Anthropic-reported, one team on its own workload, 2025), so mine is
higher. Two things are different about my measurement:

- *The thing I divide by.* My baseline is a single call with no tools, one short
  prompt and a 12-token answer, which is about as cheap as a call can be. A
  smaller baseline makes the ratio bigger. I don't know what "chat
  interactions" means for the lecture's figure, so I can't say how much of the
  gap this explains.
- *The workload and the model.* Mine is one small task on one cheap model, with
  a hard limit of 10 steps. The agent's runs were pulled in both directions by
  that: 16 of 60 kept searching until they hit the limit, which pushes the
  average up, while the other 44 stopped after only a few calls. The lecture's
  number comes from one team's own work, which could be longer or shorter than
  this.

For cost, the agent's mean is $0.00227 per run and the workflow's is $0.00034,
so **m = 6.71**. That is higher than the 5.74 token ratio because output tokens
cost more than input tokens (2.50 against 0.30 dollars per million), and the
agent writes about 127 output tokens a run against the workflow's 16.

**3. Where the agent earns it.** The workflow solved fewer than five of ten runs
on four issues, and the agent did better on only one of them, 4203 (10 of 10
against 3). So **f = 1/6 = 0.17**. With c = $0.00034 and m = 6.71, the blended
cost is c × [(1 − f) + f × m] = **$0.00066** a run. That is about twice the
workflow alone ($0.00034) and under a third of sending everything to the agent
($0.00227).

I use the workflow as c here, not the slide's "one plain call", because the
workflow is what I'd ship if the agent lost.

The slide's version uses the direct call as c: c = $0.00037, m = 6.08 and
**f = 0**, because the agent never beats the direct call on an issue. The
blended cost is then just $0.00037. The agent costs $0.0019 more per run and
passes 8 fewer runs out of 60 (29 against 37, about 0.13 fewer per run), so
there are no extra correct triages to put a price on.

Gate 4 should use the direct-call version. The direct call beat the workflow
(37 against 23 passes) for about the same cost, so it is what I would ship
instead of the agent.

**4. Path entropy.** The agent's 60 runs used **9 distinct tool sequences**, and
the three most common cover 38 runs, **63%**. Every sequence has the same shape:
`read_issue`, then `search_repo` some number of times, then `post_comment` (or
no post at all). The model never picked a different tool or a different order.
The only thing that changed was how many times it searched.

So the part that isn't earning its cost is the choosing of tools: a workflow
could write that order down. What the agent does add is searching again. That
paid off on 4203, where it searched three times and passed 10 of 10 (the
workflow passed 3 of 10). But 20 of the 60 runs searched five times or more and
none of them passed. Those 20 runs cost $0.078 of the agent's $0.136 total, 58%
of the money, and they averaged $0.0039 a run against $0.0014 for the other 40.

**5. The four gates.**

- **Does the task vary from case to case?** Only a little. The label and file
  differ by issue, but all 60 agent runs followed the same shape, read, search,
  post. What varied was how many searches it took to find the file, from one to
  nine.
- **Can I limit the damage of a mistake?** Yes. The worst a run can do is post
  one wrong comment, and the loop stops it at 10 steps, a worst case of 11,425
  prompt tokens.
- **Will I catch it in time?** Partly. A wrong comment can be deleted, but
  nothing here checks it as it is posted. In the agent's runs 31 of 60 failed,
  and 16 of those posted nothing at all, so nobody would have been told.
- **Is it worth the multiplier?** No. The agent costs 6.7 times the workflow
  and 5.7 times the direct call in tokens, and it passed fewer runs than the
  direct call (29 against 37).

**Verdict: workflow.** The agent fails gate 4, and gate 1 only partly supports it: the task barely varies
(every run followed read, search, post), and for 6.7 times the workflow's cost it
passed only 6 more runs out of 60. The hybrid did not fix that (see Part D). The
workflow is cheap ($0.00034 a run), has a fixed length (at most 5 tool calls) and
ends on its own, and its failures traced back to two choices I could change in
code: a search that hit the translation file, and my "say none" rule. The
direct call scored higher here, but only because of the repo summary; see Part D.

**6. My missed predictions.** All three pass counts missed. I expected more
structure and more freedom to help, and the opposite happened: the plain direct
call came out best (37), ahead of the agent (29) and the workflow (23). I think
that says more about this test than about the designs. The direct call gets the
repo summary, a short hand-written map of the code that names the right file for
four of the five file issues (4201, 4202, 4203 and 4206), so it was handed most
of the answers. That is why it won, and I would not call it a fair winner. It
never checks anything: on 4204 and 4206 it was confidently wrong in 10 of 10
runs, and nothing in its run could have told it so. It also only works while the
whole repo fits in a short summary (this one has 61 files). I'd treat it as a
useful baseline, not a design I'd trust on a larger codebase.

- **Direct: I said about 25, it got 37.** I thought it could only name a file
  when the summary points to it clearly, and I underrated how often it does:
  `src/exportUtils.ts` for 4202 and `src/ingest/parser.ts` for 4203 were posted 10
  of 10 times (`direct-4202-s01-7d5934`). I also expected it to lose points on
  exact file names, after the capital-letter slip in my dev run, and that did not
  come back: its wrong answers were other files, like `email.ts` and `auth.ts` on
  4201. Its two zeros were 4204 and 4206, so I named 4204 as the hardest right,
  but it tied with 4206. On 4204 the summary only lists the folder `src/util/`,
  so it guessed `src/notifications/rollup.ts`. On 4206 it trusted the file the
  issue names.
- **Workflow: I said about 40, it got 23.** I thought real search hits would
  beat guessing from a summary. Instead the search led it astray. On 4203 the
  quoted "Malformed row" text appears only in `src/i18n/en.json`, the translation
  file, so the workflow found no parser and my own "say file: none rather than
  guessing" rule made it post `none` in 6 of 10 runs (`workflow-4203-s01-976c36`).
  4204 went the same way: its searches for "summary", "email" and "timezone"
  never reached the right file, and it posted `none` in 9 of 10 runs
  (`workflow-4204-s01-787bc4`). On 4202 its search for "tsv" returned nothing, so
  it posted the folder `src/export/` (`workflow-4202-s01-26b9b3`). I was right
  that 4204 was hard, but three issues tied at zero.
- **Agent: I said about 50, it got 29.** I thought being able to search again
  would rescue it on the ambiguous issues, and I overrated that. It worked on
  4203: after the "Malformed row" hit in the translation file it searched
  `errors.rowShape` and then `parser.ts` and got 10 of 10 (`agent-4203-s01-6b42c6`).
  On 4202, 4204 and 4206 it went 0 of 10. I also expected it to stop too early on
  a plausible file, and the opposite happened: 16 of 60 runs never stopped and hit
  the turn limit. I named 4206 as the hardest, and it was, but it tied with 4202
  and 4204 at zero. The issue names `src/export/csv.ts` itself, and 6 runs posted
  it, but the bug is in `src/ingest/dedupe.ts`. In one run it made seven searches,
  nearly all on csv and export, before posting that file
  (`agent-4206-s01-475063`).

**7. The seven-layer audit.** Zero of the seven layers are empty (full table with
file and line references in `ARCHITECTURE.md`). Model, tools and observability
are present. Harness, memory and state, control and policy, and evaluation are
partial: nothing trims the history, nothing survives past one run, nothing
checks a second post or asks a person first, and the evaluation only runs before
release. The slide expects four missing from a first build. Mine is better on
observability and evaluation, which exist in code, but memory and state and
control and policy are only partial, so they are the nearest to what the slide
expects. The one policy that is really empty is "post only one comment", because
only the prompt holds it.

## Part D · The hybrid
Your hand-off rule, and the Part B traces that led you to it (written before you
measure). Its row beside the three ways (the same columns as Part B's table), how many of
its runs handed the issue to the agent, and its measured cost per run beside your
blended cost from Part C, item 3. Does it change your Part C verdict? Which of
the four would you ship, and why?

**Answer:**

**The hand-off rule (written before measuring).** The hybrid runs the workflow
first. If the workflow's label is not `question` and its file is `none`, it
does not post, and hands the issue to the agent instead. Otherwise it posts the
workflow's answer. The rule only uses the workflow's own answer, never the
known answers or the issue numbers.

**The traces behind it.** The workflow's usual failure was posting `file: none`
for something that wasn't a question. On 4203 it did so in 6 of 10 runs, after
its search only found the translation file (`workflow-4203-s01-976c36`), and on
4204 in 9 of 10 runs (`workflow-4204-s01-787bc4`). Its correct runs look
different: on 4201 it named a file (`workflow-4201-s01-4548a9`), and on 4205,
which is a question, `none` is the right answer (`workflow-4205-s01-5d4a83`). I
tried three rules from the handout on the workflow's 60 runs (23 passed, 37
failed), re-running each run's searches offline:

| Rule | Fires on passing runs | Fires on failing runs |
|---|---|---|
| Every search returned "No matches." | 0 of 23 | 1 of 37 |
| The chosen file is in none of the search results | 3 of 23 | 4 of 37 |
| No file for something that isn't a question | 0 of 23 | 26 of 37 |

The third rule never fires on a correct run and catches most failures, so that
is the one I chose. It fires on 4202 (3 runs), 4203 (6), 4204 (9) and 4206 (8).
I also tried adding "the file is a folder", which caught 4 more failures, but
all on 4202 where the agent had passed 0 of 10, so it would only add cost. The
agent only clearly earns its cost on 4203, and the rule cannot tell that issue
from the others, because it only sees the workflow's answer.

I chose the rule from the same six issues I measure it on, so its result will be
optimistic.

**Results, beside the three ways** (60 runs each, no `make reset` before the
hybrid runs).

| | Direct | Workflow | Agent | Hybrid |
|---|---|---|---|---|
| Passes (of 60) | 37 | 23 | 29 | 26 |
| 4201 (of 10) | 7 | 10 | 10 | 10 |
| 4202 | 10 | 0 | 0 | 0 |
| 4203 | 10 | 3 | 10 | 6 |
| 4204 | 0 | 0 | 0 | 0 |
| 4205 | 10 | 10 | 9 | 10 |
| 4206 | 0 | 0 | 0 | 0 |
| Lowest / highest sweep (of 6) | 3 / 4 | 2 / 3 | 2 / 3 | 2 / 3 |
| Issues solved in all 10 runs | 3 | 2 | 2 | 2 |
| Mean prompt tokens per run | 1,144 | 995 | 6,506 | 4,395 |
| Mean output tokens per run | 12 | 16 | 127 | 78 |
| Mean cached tokens per run | 0 | 0 | 0 | 0 |
| p50 latency | 0.73 s | 2.60 s | 19.5 s | 1.42 s |
| p95 latency | 2.1 s | 47.4 s | 72.8 s | 8.0 s |
| Mean cost per run | $0.00037 | $0.00034 | $0.00227 | $0.00151 |
| Tool calls, mean (max) | 2.0 (2) | 4.8 (5) | 5.9 (10) | 7.4 (14) |

**Hand-offs.** 24 of the 60 runs were handed to the agent (15 ended
`model_stopped` and 9 `turn_limit`); the other 36 stayed in the workflow and
ended `completed`. By issue: 4203 five times, 4204 nine times and 4206 ten
times, and never on 4201, 4202 or 4205. Only the 5 on 4203 landed where Part C
found the agent earns its cost: the agent passed all five. The other 19 went to
4204 and 4206, where the agent also passes 0 of 10, so they cost money and
bought nothing. On 4203 the other 5 runs stayed in the workflow, and 4 of them
failed by posting `src/api/uploads.ts` instead of `none`, a confident wrong
file, which my rule cannot see. That is
why the hybrid got 6 of 10 there and not 10.

**Cost against the blend.** The hybrid cost $0.00151 a run, against the
$0.00066 blended cost from Part C, item 3. The blend assumed I could hand off
only the one issue in six where the agent helps (about 10 runs of 60). The real
rule handed off 24, because it fires on every issue where the workflow answers
`none`, and most of those are issues the agent cannot solve either. A handed-off
run costs $0.00326 on average (the workflow's part plus the agent's), against
$0.00035 for a run that stayed, and the handed-off runs make up 86% of the
hybrid's total cost.

**Does it change my Part C verdict?** No. The hybrid passed 3 more runs than the
workflow (26 against 23) for 4.5 times the cost, which is about $0.023 for each
extra correct triage. The agent got 6 more passes for about $0.019 each, so
the hybrid was not even a cheaper way to buy the agent's gains. The rule only
sees the workflow's own answer, so it handed off the issues where the workflow
said `none` and missed the ones where it was confidently wrong. I chose the rule
from the same six issues I measured it on, so a fresh set of issues would
probably do worse. My verdict stays workflow.

**Which of the four would I ship?** On these numbers the direct call is the best
of the four: 37 passes at $0.00037 a run. But it won because the repo summary
names the file for most issues, and it never checks anything. It was confidently
wrong on 4204 and 4206 in 10 of 10 runs, and no rule could catch that, so it
only works while a whole repo fits in a short summary. Today, on this 61-file
repo, I would ship the direct call, because it is the cheapest way to get the
most correct triages. If the repo grew past what a summary can hold, I would
ship the workflow and fix its two weak points, the search terms and the "say
none" rule, before touching an agent.


## Assistance
Which AI tool, what it wrote, what you checked.

**Answer:**
I used Claude Code as a coding assistant. It helped me write the python code inside eval, agent, and the ways folder based on my approval and directions. I checked its code by running make test, make bounds-smoke, make check-01, and manual testing / checking with terminal. 