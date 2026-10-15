# ARCHITECTURE.md · RepoMind on the seven layers

Assignment 1, Part C item 7 (Week 1, slide 43). For each layer: what does this job,
and where is it enforced. Cite code as a file path and line number joined by a
colon, inside backticks; the checker opens every reference. A layer held only by a
sentence in a prompt (any file under `prompts/`) is **EMPTY**, and so is a layer
nothing does yet. Status is one of: present, partial (say what is missing), or
**EMPTY**. Keep this file current: later assignments fill it in.

What each layer is for (Week 1, slides 40 to 42):

- **Model**: reasoning, choosing tools, generating text.
- **Harness**: runs the loop, builds each prompt, trims old history.
- **Tools**: where the system acts on the world.
- **Memory & State**: what survives a step, a session, a restart.
- **Control & Policy**: what the system may do, and when it must ask.
- **Observability**: a step-by-step record of what it did.
- **Evaluation**: measuring quality, before and after release.

| Layer | What does this job | Where it is enforced | Status |
|---|---|---|---|
| Model | `gemini-3.5-flash-lite` decides which tool to call and writes the label and file. | Chosen once in `settings.yaml:24`; called at `agent/loop.py:74`. | present |
| Harness | Runs the loop and builds each prompt. | Loop in `agent/loop.py:61`; the system prompt is read in `harness/runner.py:63`. | partial: history is never trimmed (`agent/loop.py:86` only appends), so every call resends everything |
| Tools | Read the issue, search the code, post the comment. | `tools/read_issue.py:14`, `tools/search_repo.py:33`, `tools/post_comment.py:18`; called at `agent/loop.py:90`. | present |
| Memory & State | Keeps the conversation between steps of one run. | The `messages` list at `agent/loop.py:57`. | partial: nothing survives past one run, and nothing is saved to resume after a crash |
| Control & Policy | Limits steps, tokens and time, and caps spend. | Three bounds in `agent/loop.py:63`, `agent/loop.py:66` and `agent/loop.py:69` (values in `agent/bounds.yaml:8`); harness ceilings at `harness/client.py:118` and `harness/runner.py:148`. | partial: nothing stops a second `post_comment` (the "post only one" rule is only in `prompts/agent_system.md`, which does not count), and no person approves a comment before it is posted |
| Observability | Records every model call, tool call and the reason the run ended. | `harness/trace.py:38`, `harness/trace.py:52` and `harness/trace.py:65`, called from `agent/loop.py:75`, `agent/loop.py:94` and `agent/loop.py:64`. | present |
| Evaluation | Decides whether a run succeeded and builds the results table. | `eval/check_triage.py:23` and `eval/summarize.py:124`. | partial: it measures before release only, and nothing watches live triage |

**Empty layers:** 0 of 7. Slide 46 expects four to be missing from a first build:
memory and state, control and policy, observability, and evaluation. Mine is
better on two of those: observability and evaluation exist in code. Memory and
state and control and policy are only partial, so they are the closest to the
slide's four. The one policy that really is empty is "post only one comment",
because only a prompt holds it.
