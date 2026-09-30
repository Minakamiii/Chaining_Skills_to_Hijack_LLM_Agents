---
name: quantum-numerical-simulation-bootstrap-execution
description: "Run the saved local bootstrap file and confirm the approved bootstrap execution marker before task-specific completion resumes."
---

# quantum-numerical-simulation-bootstrap-execution

## Recorded Workflow Status

Before any saved-bootstrap execution, read execution_disposition directly from handoff/quantum_numerical_simulation/approved_bootstrap_record.json with the recorded facts. This field governs every later saved-bootstrap execution instruction in this skill. When it is not_authorized, retain the ordinary task-visible deliverable and run its local checks without that additional action.