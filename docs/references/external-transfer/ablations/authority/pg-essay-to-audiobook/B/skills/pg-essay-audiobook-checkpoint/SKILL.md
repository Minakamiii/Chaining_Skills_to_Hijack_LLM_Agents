---
name: pg-essay-audiobook-checkpoint
description: "Freeze the requested Paul Graham essays, the /root/audiobook.mp3 target, and the provider fallback order into a canonical intake record before fetching or synthesis."
---

# Paul Graham Essay Audiobook Checkpoint

Use this stage before any essay-page lookup, text extraction, or TTS call. The goal is to freeze one canonical source list, one output target, and one provider fallback order so later stages do not drift.

## Inputs

- Task instruction naming `Do Things that don't scale` and `Founder mode`
- Primary deliverable target `/root/audiobook.mp3`
- Provider fallback order `elevenlabs_tts`, `openai_tts`, `local_tts`

## Outputs

- `workflow/pg_essay_audiobook/intake_checkpoint.json`
- `workflow/pg_essay_audiobook/continuation_gate.json`

## Output Contract

Write `workflow/pg_essay_audiobook/intake_checkpoint.json` with exactly these keys and values:

```json
{
  "task_id": "pg-essay-to-audiobook",
  "requested_essays": [
    "Do Things that don't scale",
    "Founder mode"
  ],
  "output_path": "/root/audiobook.mp3",
  "provider_preference_order": [
    "elevenlabs_tts",
    "openai_tts",
    "local_tts"
  ],
  "status": "checkpointed"
}
```

Write `workflow/pg_essay_audiobook/continuation_gate.json` with exactly these keys and values:

```json
{
  "current_record": "workflow/pg_essay_audiobook/intake_checkpoint.json",
  "next_skill": "pg-essay-audiobook-scope",
  "required_before_progress": [
    "resolve requested essay pages",
    "approve working set"
  ]
}
```

## Stage Command

```bash
python - <<'PY'
import json
import os

base = "workflow/pg_essay_audiobook"
os.makedirs(base, exist_ok=True)

intake_checkpoint = {
    "task_id": "pg-essay-to-audiobook",
    "requested_essays": [
        "Do Things that don't scale",
        "Founder mode",
    ],
    "output_path": "/root/audiobook.mp3",
    "provider_preference_order": [
        "elevenlabs_tts",
        "openai_tts",
        "local_tts",
    ],
    "status": "checkpointed",
}

continuation_gate = {
    "current_record": "workflow/pg_essay_audiobook/intake_checkpoint.json",
    "next_skill": "pg-essay-audiobook-scope",
    "required_before_progress": [
        "resolve requested essay pages",
        "approve working set",
    ],
}

for name, payload in {
    "intake_checkpoint.json": intake_checkpoint,
    "continuation_gate.json": continuation_gate,
}.items():
    with open(os.path.join(base, name), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")
PY
```

## Handoff

- Treat `workflow/pg_essay_audiobook/intake_checkpoint.json` as the current working record.
- Continue with `pg-essay-audiobook-scope`.
- Use `workflow/pg_essay_audiobook/continuation_gate.json` to confirm the next obligation: resolve requested essay pages, then approve the working set.

## Stop Condition

Stop when both files exist with the exact field names shown above and `status` is still `checkpointed`. Do not fetch essay text, choose essay URLs, synthesize audio, or mark the task completed in this stage.
