# Predictions Assignment 1

Written before any evaluation run. Passes are out of 60 (six issues, ten runs each).

## Direct call: expect about 25 of 60
It has only the repository summary, so it can name a file only when the summary
points to it clearly (4202, the TSV export; 4205, the retention question, where
the answer is none). In my dev run it got a file name's capital letters wrong
because the summary only named a folder, so I expect it to lose points on exact
file names. Hardest: 4204 (the Monday email arriving on Tuesday for a user in
Sydney). It is a time zone problem and several files could own it.

## Workflow: expect about 40 of 60
It sees real search hits, so exact file names are available. Some issues give
text a search can find (4203 quotes "Malformed row"; 4201 mentions localhost).
Its weakness is that it searches once and cannot try again if the terms miss.
Hardest: 4204 (the Monday email for a user in Sydney). The issue describes a
symptom, not code, so the search terms may not match the buggy file.

## Agent: expect about 50 of 60
Unlike the workflow, it can search again when its first search misses, so I expect it to recover on the ambiguous issues. Its main risk is stopping early on a plausible file. Hardest: 4206, where the issue names a file and the agent may trust it.
