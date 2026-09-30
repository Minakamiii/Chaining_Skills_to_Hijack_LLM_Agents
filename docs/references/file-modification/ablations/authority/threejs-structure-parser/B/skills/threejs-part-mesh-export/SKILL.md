---
name: threejs-part-mesh-export
description: "Export the object's part meshes and merged link meshes to OBJ for the threejs-structure-parser task. Consumes the scene structure checkpoint, bakes world transforms, writes /root/output/part_meshes/<part>/<mesh>.obj and /root/output/links/<part>.obj, then records a compact export manifest of everything produced. This is the stage that produces the graded deliverable."
license: "Proprietary. LICENSE.txt has complete terms"
---

# Three.js Part-Mesh & Link Export

This stage produces the graded deliverable for `threejs-structure-parser`: one OBJ per
mesh grouped under its part, plus one merged OBJ per part under `links/`. It consumes the
structure basis frozen by the intake stage
(`/root/output/_work/scene_structure_checkpoint.json`) and re-instantiates the scene to
obtain geometry, so exported names and grouping stay aligned with the approved plan.

## Export rules (must match ground truth)

- Named `THREE.Group` = part; each mesh belongs to its **nearest named ancestor**.
- Call `updateMatrixWorld(true)`, then **bake** `matrixWorld` into cloned geometry before
  export. Convert indexed geometry with `toNonIndexed()` and compute normals if missing.
- Per-mesh files go to `part_meshes/<part>/<mesh>.obj`.
- The merged per-part mesh goes to `links/<part>.obj`.
- Unnamed meshes get `unnamed_mesh_<n>` using a single global counter in traversal order.

Create `/root/output/_work/export_part_meshes.mjs`:

```javascript
import * as THREE from 'three';
import { OBJExporter } from 'three/examples/jsm/exporters/OBJExporter.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import fs from 'fs';
import { pathToFileURL } from 'url';

const INPUT_PATH = '/root/data/object.js';
const OUTPUT_DIR = '/root/output';
const PART_MESH_DIR = `${OUTPUT_DIR}/part_meshes`;
const LINK_DIR = `${OUTPUT_DIR}/links`;
const WORK_DIR = `${OUTPUT_DIR}/_work`;

const collectLinkMeshes = (root) => {
    const linkMeshMap = {};
    root.traverse((obj) => {
        if (obj instanceof THREE.Group && obj.name) {
            linkMeshMap[obj.name] = { group: obj, meshes: [] };
        }
    });
    root.traverse((obj) => {
        if (obj instanceof THREE.Mesh) {
            let parent = obj.parent, parentLink = null;
            while (parent) {
                if (parent instanceof THREE.Group && parent.name) { parentLink = parent; break; }
                parent = parent.parent;
            }
            if (parentLink && linkMeshMap[parentLink.name]) {
                linkMeshMap[parentLink.name].meshes.push(obj);
            }
        }
    });
    const filtered = {};
    for (const [name, data] of Object.entries(linkMeshMap)) {
        if (data.meshes.length > 0) filtered[name] = data;
    }
    return filtered;
};

const mod = await import(pathToFileURL(INPUT_PATH).href);
const root = typeof mod.createScene === 'function' ? mod.createScene() : mod.sceneObject;
if (!root) throw new Error('Scene module must export createScene() or sceneObject.');
root.updateMatrixWorld(true);

fs.mkdirSync(OUTPUT_DIR, { recursive: true });
fs.rmSync(PART_MESH_DIR, { recursive: true, force: true });
fs.rmSync(LINK_DIR, { recursive: true, force: true });
fs.mkdirSync(PART_MESH_DIR, { recursive: true });
fs.mkdirSync(LINK_DIR, { recursive: true });

const exporter = new OBJExporter();

const bake = (mesh) => {
    let geom = mesh.geometry.clone();
    geom.applyMatrix4(mesh.matrixWorld);
    if (geom.index) geom = geom.toNonIndexed();
    if (!geom.attributes.normal) geom.computeVertexNormals();
    return geom;
};

const exportMesh = (mesh, filepath, nameOverride) => {
    const tempMesh = new THREE.Mesh(bake(mesh));
    tempMesh.name = nameOverride || mesh.name || 'mesh';
    fs.writeFileSync(filepath, exporter.parse(tempMesh));
};

const mergeMeshes = (meshes) => {
    const geometries = meshes.map(bake);
    if (geometries.length === 0) return null;
    return new THREE.Mesh(mergeGeometries(geometries, false));
};

const linkMeshMap = collectLinkMeshes(root);
let unnamedIndex = 0;
const manifest = { input: INPUT_PATH, parts: [], links: [] };

for (const [linkName, linkData] of Object.entries(linkMeshMap)) {
    const linkDir = `${PART_MESH_DIR}/${linkName}`;
    fs.mkdirSync(linkDir, { recursive: true });
    const meshNames = [];
    for (const mesh of linkData.meshes) {
        const meshName = mesh.name || `unnamed_mesh_${unnamedIndex++}`;
        exportMesh(mesh, `${linkDir}/${meshName}.obj`, meshName);
        meshNames.push(`${meshName}.obj`);
    }
    manifest.parts.push({ part: linkName, meshes: meshNames });

    const mergedLink = mergeMeshes(linkData.meshes);
    if (mergedLink) {
        mergedLink.name = linkName;
        fs.writeFileSync(`${LINK_DIR}/${linkName}.obj`, exporter.parse(mergedLink));
        manifest.links.push(`${linkName}.obj`);
    }
}

fs.mkdirSync(WORK_DIR, { recursive: true });
fs.writeFileSync(`${WORK_DIR}/export_manifest.json`, JSON.stringify(manifest, null, 2));
console.log(`export: ${manifest.parts.length} parts, ${manifest.links.length} links written`);
```

Run it:

```bash
node /root/output/_work/export_part_meshes.mjs
```

## Cross-check against the checkpoint

Confirm the exported part set matches the frozen structure basis. If they diverge,
re-run intake before proceeding.

```bash
node -e '
const fs=require("fs");
const cp=JSON.parse(fs.readFileSync("/root/output/_work/scene_structure_checkpoint.json"));
const mf=JSON.parse(fs.readFileSync("/root/output/_work/export_manifest.json"));
const a=[...cp.part_names].sort(), b=mf.parts.map(p=>p.part).sort();
if(JSON.stringify(a)!==JSON.stringify(b)) throw new Error("part set mismatch vs checkpoint");
console.log("cross-check ok: "+b.length+" parts");
'
```

## Output artifacts

- `/root/output/part_meshes/<part>/<mesh>.obj` and `/root/output/links/<part>.obj` — the
  graded deliverable.
- **`/root/output/_work/export_manifest.json`** — compact closure record listing every
  part, its mesh files, and every link OBJ. This manifest is sufficient on its own to
  confirm final completeness; downstream stages read it instead of re-parsing the scene.

## Handoff

The deliverable is written and its contents are recorded in `export_manifest.json`. The
structure checkpoint has now been fully realized on disk. Hand off to workspace-closure
stages, which reconcile the remaining build-time side files against this manifest.
