"""Way 2, the workflow. Your code decides every step, in advance, in this order:

    read_issue  ->  one call to extract search terms  ->  search_repo
                ->  one call to choose the label and the file  ->  post_comment

A fixed sequence, no loop: the model never chooses a tool. Trace every model
call (ctx.trace.model_call); call every tool through ctx.call_tool(step, name,
input), which traces it. Keep your prompts in prompts/.

Part D reuses this way: its first half (read, extract, search) and its second
half (choose, post) are easier to reuse as two functions.
"""


import re

from harness.formats import LABELS, format_triage_comment, parse_triage_comment

MAX_TERMS = 3


def gather(ctx):
    """First half: read the issue, ask for search terms, search. Returns the issue and the searches."""
    issue = ctx.call_tool(0, "read_issue", {"number": ctx.issue_number}).content
    reply = ctx.client.create(system=ctx.prompt("workflow_terms.md"),
                              messages=[{"role": "user", "content": issue}])
    ctx.trace.model_call(1, reply)
    searches = [(term, ctx.call_tool(1, "search_repo", {"query": term}).content)
                for term in _terms(reply.text)]
    return issue, searches


def decide(ctx, issue, searches) -> None:
    """Second half: choose the label and file from the search results, then post the comment."""
    found = "\n\n".join(f"Search for {term!r}:\n{result}" for term, result in searches) or "No searches were run."
    response = ctx.client.create(system=ctx.prompt("workflow_choose.md"),
                                 messages=[{"role": "user",
                                            "content": f"Issue:\n\n{issue}\n\nSearch results:\n\n{found}"}])
    ctx.trace.model_call(2, response)
    label, file = parse_triage_comment(response.text)
    if label not in LABELS:
        return  # nothing usable to post; with no comment the run fails the check
    ctx.call_tool(2, "post_comment", {"number": ctx.issue_number,
                                      "body": format_triage_comment(label, file)})


def run(ctx) -> None:
    issue, searches = gather(ctx)
    decide(ctx, issue, searches)


def _terms(text: str) -> list[str]:
    terms = []
    for line in text.splitlines():
        term = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip().strip("`'\"")
        if term and term not in terms:
            terms.append(term)
    return terms[:MAX_TERMS]  # the code caps the number of searches, not the model
