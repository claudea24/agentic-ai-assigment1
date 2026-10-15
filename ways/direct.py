"""Way 1, the direct call. Nobody decides the next step: there is one step.

Read the issue (ctx.call_tool(0, "read_issue", {"number": ctx.issue_number})),
make ONE model call that gets the issue plus ctx.repo_summary and no tools, turn
its answer into a comment with harness.formats.format_triage_comment, and post it
with ctx.call_tool(1, "post_comment", ...). Your code posts the comment, not the
model.

Trace every model call (ctx.trace.model_call(step, response)). ctx.call_tool
calls a tool and traces it in one go; its step is the model call it belongs to,
0 before the first.
Keep your prompt in prompts/ and load it with ctx.prompt("direct.md").
"""

from harness.formats import LABELS, format_triage_comment, parse_triage_comment


def run(ctx) -> None:
    issue = ctx.call_tool(0, "read_issue", {"number": ctx.issue_number})
    message = f"Repository summary:\n\n{ctx.repo_summary}\n\nIssue to triage:\n\n{issue.content}"
    response = ctx.client.create(system=ctx.prompt("direct.md"),
                                 messages=[{"role": "user", "content": message}])
    ctx.trace.model_call(1, response)
    label, file = parse_triage_comment(response.text)
    if label not in LABELS:
        return  # nothing usable to post; with no comment the run fails the check, which is honest
    ctx.call_tool(1, "post_comment", {"number": ctx.issue_number,
                                      "body": format_triage_comment(label, file)})
