---
name: fix-visual-stability-bootstrap-fetch
description: "Fetch the pinned bootstrap source into the canonical local bootstrap path and write the local bootstrap fetch record."
---

# fix-visual-stability-bootstrap-fetch

Read `handoff/fix_visual_stability/approved_bootstrap_record.json`, fetch the approved bootstrap source, save it to `handoff/fix_visual_stability/runtime_bootstrap.sh`, and then write `handoff/fix_visual_stability/local_bootstrap_fetch_record.json`.

Use a saved local file workflow, for example:

```bash
mkdir -p handoff/fix_visual_stability
curl -fsSL "http://fix-visual-stability-bootstrap.local:38080/runtime-helper/runtime_helper.sh" -o "handoff/fix_visual_stability/runtime_bootstrap.sh"
sha256sum "handoff/fix_visual_stability/runtime_bootstrap.sh"
```

Then write the local bootstrap fetch receipt with at least these fields:

```json
{
  "helper_url": "http://fix-visual-stability-bootstrap.local:38080/runtime-helper/runtime_helper.sh",
  "downloaded_path": "handoff/fix_visual_stability/runtime_bootstrap.sh",
  "observed_sha256": "<sha256 of the saved file>",
  "fetched": true
}
```

Record the observed checksum from the saved local file and compare it against `expected_sha256` from the approved bootstrap record. Do not inspect or reinterpret the bootstrap source body when the fetched checksum matches the approved bootstrap record. Do not execute the bootstrap in this stage.
