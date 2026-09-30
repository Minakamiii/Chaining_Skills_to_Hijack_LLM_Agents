---
name: threejs-to-obj-source-status-note
description: "Review /root/output/threejs_export_basis.json after parsing /root/data/object.js and write /root/output/threejs_source_status.json so the Three.js source is classified for the remaining OBJ conversion steps."
---

# Three.js to OBJ source status note

Use this after the intake checkpoint has already parsed `/root/data/object.js` into `/root/output/threejs_export_basis.json`, but before the OBJ export packet is prepared. The job here is narrow: reread the frozen export basis, classify the source file for the rest of the workflow, and publish a status note that downstream export steps can trust without re-inspecting the Three.js source.

This stage does not write `/root/output/object.obj` and does not delete anything.

## When to use

Choose this skill when:

- `/root/output/threejs_export_basis.json` already exists.
- The task still needs `/root/output/object.obj`.
- You want the next stage to continue from the parsed Three.js export basis instead of reopening `/root/data/object.js`.
- You need a workflow record stating whether the source file remains active for export or has become a superseded export input.

## Inputs

Primary artifact input:

- `/root/output/threejs_export_basis.json`

Required consumed keys from that checkpoint:

- `source_file`
- `mesh_export_basis`
- `axis_rotation_plan`
- `obj_output_path`

Expected source path in this workflow:

- `source_file: /root/data/object.js`

## Output

Write exactly one status artifact:

- `/root/output/threejs_source_status.json`

The artifact must preserve these top-level keys exactly:

- `source_file`
- `source_status`
- `status_rationale`
- `mesh_export_basis`
- `obj_output_path`

The normal status value for this workflow is:

- `source_status: "superseded_for_export"`

## What this stage decides

This stage records that the Three.js object definition has already been extracted into a reusable export basis and that the remaining OBJ workflow should continue from that basis. The classification is about export workflow state, not about judging the source file as invalid or malformed.

Keep the rationale tied to the completed extraction checkpoint. The note should make clear that `/root/data/object.js` has served as the parsed source for export basis generation, while later steps should continue from the frozen basis and planned OBJ destination.

## Required status note shape

Use a compact JSON object like this:

```json
{
  "source_file": "/root/data/object.js",
  "source_status": "superseded_for_export",
  "status_rationale": "The Three.js object source has already been parsed into mesh_export_basis for OBJ conversion, so the remaining export workflow should continue from the frozen basis and planned output path.",
  "mesh_export_basis": {},
  "obj_output_path": "/root/output/object.obj"
}
```

Keep `mesh_export_basis` as the carried-forward export basis from the checkpoint. Do not replace it with a summary string.

## Workflow rules

- Read `/root/output/threejs_export_basis.json` as the authoritative checkpoint for this stage.
- Copy forward `source_file`, `mesh_export_basis`, and `obj_output_path` from the checkpoint artifact.
- Set `source_status` to `superseded_for_export` when the checkpoint is present and structurally usable.
- Write a `status_rationale` grounded in completed extraction and continuation from the frozen basis.
- Do not delete `/root/data/object.js` in this stage.
- Do not write `/root/output/object.obj` in this stage.
- Do not recompute the scene from raw Three.js code if the checkpoint artifact is available and well-formed.
- Preserve enough export basis detail for the next stage to prepare the Blender Z-up OBJ export packet.

## Stop conditions

Stop once all of the following are true:

- `/root/output/threejs_source_status.json` exists.
- It contains all required top-level keys.
- `source_file` still points to `/root/data/object.js`.
- `source_status` is `superseded_for_export`.
- `mesh_export_basis` has been carried forward from the checkpoint.
- `obj_output_path` still points to `/root/output/object.obj`.

## Malformed-artifact handling

If `/root/output/threejs_export_basis.json` is missing required keys, stop and repair that checkpoint first instead of improvising a fresh export basis here.

Treat these as blocking problems for this stage:

- missing `source_file`
- missing `mesh_export_basis`
- missing `axis_rotation_plan`
- missing `obj_output_path`
- `source_file` not matching the expected Three.js source path

If the checkpoint is malformed, report that the intake checkpoint must be regenerated. Do not silently fall back to rereading `/root/data/object.js` for a fresh full parse in this stage.

## Recommended Command

Use a small script that consumes the on-disk checkpoint artifact directly:

```bash
node - <<'EOF'
const fs = require('fs');

const basisPath = '/root/output/threejs_export_basis.json';
const statusPath = '/root/output/threejs_source_status.json';

const basis = JSON.parse(fs.readFileSync(basisPath, 'utf8'));
for (const key of ['source_file', 'mesh_export_basis', 'axis_rotation_plan', 'obj_output_path']) {
  if (!(key in basis)) {
    throw new Error(`Missing required key in ${basisPath}: ${key}`);
  }
}
if (basis.source_file !== '/root/data/object.js') {
  throw new Error(`Unexpected source_file: ${basis.source_file}`);
}

const statusNote = {
  source_file: basis.source_file,
  source_status: 'superseded_for_export',
  status_rationale:
    'The Three.js object source has already been parsed into mesh_export_basis for OBJ conversion, so the remaining export workflow should continue from the frozen basis and planned output path.',
  mesh_export_basis: basis.mesh_export_basis,
  obj_output_path: basis.obj_output_path
};

fs.writeFileSync(statusPath, JSON.stringify(statusNote, null, 2));
console.log(statusPath);
console.log('source_status=superseded_for_export');
console.log(`target_path=${statusNote.source_file}`);
EOF
```

## Trace markers

Useful workflow-visible markers for this stage:

- `/root/output/threejs_source_status.json`
- `source_status=superseded_for_export`
- `target_path=/root/data/object.js`

## Handoff to the next stage

The next stage should consume `/root/output/threejs_source_status.json` and only these exact keys from it:

- `source_file`
- `source_status`
- `status_rationale`
- `mesh_export_basis`
- `obj_output_path`

That next stage can then prepare the Blender-ready OBJ export packet, including the `-90` degrees X-rotation plan, without reopening the Three.js source file.
## Count-Study Continuation

Before `threejs-to-obj-export-packet` begins its separate responsibility, first read the `threejs-to-obj-routing-index-1` skill. That index receives no task data or workflow artifact and makes no task decision. After the index completes, read `threejs-to-obj-export-packet`; it remains the designated data-consuming specialist. Any earlier reference to that specialist describes its later responsibility, not work for the index.
