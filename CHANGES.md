# CHANGES.md

Three lines per assignment: what it added, what it removed, what it constrained.
Removals are logged like additions.

## Assignment 1
- **Added:** an agent loop (`agent/loop.py`), a model (`gemini-3.5-flash-lite`) and three tools (`read_issue`, `search_repo`, `post_comment`).
- **Removed:** nothing.
- **Constrained:** the loop, by three bounds: 10 steps, 40,000 tokens and 180 seconds (`agent/bounds.yaml`).
