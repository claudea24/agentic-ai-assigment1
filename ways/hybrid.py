"""Way 4, the hybrid. The workflow runs first; the agent only takes over when a rule says the
workflow's answer is likely wrong (the rule is written in reports/LAB_01.md, Part D):

    gather (read, extract terms, search)  ->  one call to choose label and file
        ->  label is not question and the file is none?
              no:  post the workflow's comment             (the run ends "completed")
              yes: hand the issue to the agent loop        (the run ends with the loop's reason)

Each run posts exactly one comment: the workflow posts only when it keeps the issue, and the
agent posts only when it is handed the issue.
"""

from agent.loop import load_bounds, run_loop
from harness.formats import LABELS, format_triage_comment, parse_triage_comment
from ways.workflow import gather


def should_hand_off(label, file) -> bool:
    """The hand-off rule. It sees only the workflow's own answer, never the known answers
    or the issue number. A reply with no usable label also goes to the agent, as nothing
    could be posted from it."""
    if label not in LABELS:
        return True
    return label != "question" and file in (None, "none")


def run(ctx) -> None:
    issue, searches = gather(ctx)
    found = "\n\n".join(f"Search for {term!r}:\n{result}" for term, result in searches) or "No searches were run."
    response = ctx.client.create(system=ctx.prompt("workflow_choose.md"),
                                 messages=[{"role": "user",
                                            "content": f"Issue:\n\n{issue}\n\nSearch results:\n\n{found}"}])
    ctx.trace.model_call(2, response)
    label, file = parse_triage_comment(response.text)
    if should_hand_off(label, file):
        run_loop(ctx.client, ctx.tools, ctx.prompt("agent_system.md"),
                 f"Triage issue #{ctx.issue_number}.", load_bounds(), ctx.trace)
        return
    ctx.call_tool(2, "post_comment", {"number": ctx.issue_number,
                                      "body": format_triage_comment(label, file)})
