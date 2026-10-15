"""Part 0: read the recorded agent run and measure how its prompt grew.

Usage: python eval/part0.py [path]    (no API calls)
Prints the part0 object for reports/LAB_01.json.
"""

import json
import sys
from pathlib import Path

RECORDING = Path(__file__).resolve().parent.parent / "fixtures" / "week01_recorded_run.jsonl"


def measure(path: Path = RECORDING) -> dict:
    prompts = {}      # message.id -> prompt tokens, in order of first appearance
    cache_reads = {}  # message.id -> cache read tokens
    tool_ids = set()
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("type") != "assistant":
            continue
        msg = row["message"]
        usage = msg["usage"]
        cache_read = usage.get("cache_read_input_tokens", 0)
        # One call spans several lines with the same usage, so key by message.id.
        prompts.setdefault(msg["id"], usage.get("input_tokens", 0) + cache_read
                           + usage.get("cache_creation_input_tokens", 0))
        cache_reads.setdefault(msg["id"], cache_read)
        tool_ids.update(b["id"] for b in msg["content"] if b.get("type") == "tool_use")
    sizes = list(prompts.values())
    total = sum(sizes)
    cached = sum(cache_reads.values())
    return {
        "model_calls": len(sizes),
        "tool_calls": len(tool_ids),
        "prompt_tokens": total,
        "cache_read_tokens": cached,
        "cache_read_share": round(cached / total, 3),
        "first_prompt": sizes[0],
        "last_prompt": sizes[-1],
        "cumulative_over_first": round(total / sizes[0], 2),
    }


if __name__ == "__main__":
    print(json.dumps(measure(Path(sys.argv[1]) if len(sys.argv) > 1 else RECORDING), indent=2))
