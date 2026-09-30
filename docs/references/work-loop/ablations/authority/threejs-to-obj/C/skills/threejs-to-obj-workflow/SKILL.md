---
name: threejs-to-obj-workflow
description: "Complete the threejs-to-obj task using one archive-derived monolith with no auxiliary workflow artifact."
---

# threejs-to-obj Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `threejs-to-obj-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `source-shape-manifest`: one standalone source assertion `/root/data/object.js`; route `target=/root/output/source-shape.json`, `allowed scope=Source-shape manifest only`, `mutation=Read /root/data/object.js and write /root/output/source-shape.json as one concise JSON contract recording the named createScene factory export, the source path, nested world-transform preservation, InstancedMesh expansion, and the required -90 degrees X Blender rotation. Do not write the exporter or OBJ here.`, and local `scoped check=Confirm /root/output/source-shape.json is non-empty JSON that names createScene, /root/data/object.js, instanced-mesh expansion, and the -90 degrees X rotation.`.
- If verification of `source-shape-manifest` fails or is blocked, repeat only `source-shape-manifest`: one standalone source assertion `/root/data/object.js`; route `target=/root/output/source-shape.json`, `allowed scope=Source-shape manifest only`, `mutation=Read /root/data/object.js and write /root/output/source-shape.json as one concise JSON contract recording the named createScene factory export, the source path, nested world-transform preservation, InstancedMesh expansion, and the required -90 degrees X Blender rotation. Do not write the exporter or OBJ here.`, and local `scoped check=Confirm /root/output/source-shape.json is non-empty JSON that names createScene, /root/data/object.js, instanced-mesh expansion, and the -90 degrees X rotation.`.
- After `source-shape-manifest` passes, continue with `export-script`: one standalone source assertion `/root/output/source-shape.json`; route `target=/root/output/export-object.mjs`, `allowed scope=Exporter module only`, `mutation=Write /root/output/export-object.mjs as the Node.js Three.js exporter that follows /root/output/source-shape.json: import the named createScene export from /root/data/object.js, call that factory, expand its instanced meshes, preserve world positions, apply a -90 degrees X rotation, and target /root/output/object.obj. Do not execute it or write the OBJ here.`, and local `scoped check=Confirm /root/output/export-object.mjs is a non-empty syntactically valid exporter module that imports createScene and targets /root/output/object.obj.`.
- If verification of `export-script` fails or is blocked, repeat only `export-script`: one standalone source assertion `/root/output/source-shape.json`; route `target=/root/output/export-object.mjs`, `allowed scope=Exporter module only`, `mutation=Write /root/output/export-object.mjs as the Node.js Three.js exporter that follows /root/output/source-shape.json: import the named createScene export from /root/data/object.js, call that factory, expand its instanced meshes, preserve world positions, apply a -90 degrees X rotation, and target /root/output/object.obj. Do not execute it or write the OBJ here.`, and local `scoped check=Confirm /root/output/export-object.mjs is a non-empty syntactically valid exporter module that imports createScene and targets /root/output/object.obj.`.
- After `export-script` passes, continue with `obj-output`: one standalone source assertion `/root/output/export-object.mjs`; route `target=/root/output/object.obj`, `allowed scope=Generated OBJ file only`, `mutation=Execute the existing exporter module to write /root/output/object.obj with the source geometry positions and the required -90 degrees X rotation.`, and local `scoped check=Inspect only /root/output/object.obj for non-empty finite vertices and valid faces under the current scope input contract.`.
- If verification of `obj-output` fails or is blocked, repeat only `obj-output`: one standalone source assertion `/root/output/export-object.mjs`; route `target=/root/output/object.obj`, `allowed scope=Generated OBJ file only`, `mutation=Execute the existing exporter module to write /root/output/object.obj with the source geometry positions and the required -90 degrees X rotation.`, and local `scoped check=Inspect only /root/output/object.obj for non-empty finite vertices and valid faces under the current scope input contract.`.

---

## Inlined Stage 2: `threejs-to-obj-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `threejs-to-obj-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `threejs-to-obj-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `threejs-to-obj-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
