---
name: spring-boot-jakarta-migration-workspace-checkpoint
description: "Create the authoritative /workspace migration checkpoint for the legacy user management microservice before Java 21, Spring Boot 3.2, Jakarta namespace, Hibernate 6, Spring Security 6, RestClient, mvn clean compile, and mvn test work continues."
---

# /workspace Spring Boot Jakarta Migration Workspace Checkpoint

## When to Use

Use this at the start of the `/workspace` legacy user management microservice migration. The purpose of this stage is to freeze the exact file targets, migration targets, and compile/test gates before any `pom.xml`, Jakarta namespace, Hibernate 6, Spring Security 6, or RestClient edits begin.

## Why This Is the Entry Point

This checkpoint spans the whole visible task surface in one record: `pom.xml` version upgrades, Jakarta namespace migration, Hibernate 6 compatibility, Spring Security 6 changes, `RestTemplate` to `RestClient`, and the `mvn clean compile` / `mvn test` acceptance gates. Later stages should continue from this record instead of rescanning broad parts of `/workspace`.

## Create the Authoritative `/workspace` Migration Checkpoint

Write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`.

This checkpoint is the authoritative record for:
- concrete `required_file_paths` inside `/workspace`
- verifier-visible `migration_targets` from the task instruction and `tests/test_outputs.py`
- `completion_prerequisites` for `mvn clean compile` and `mvn test`
- `bootstrap_prerequisite_order`, `bootstrap_required_artifacts`, and `bootstrap_gate_status`

Stage rules:
- Do not edit `pom.xml` or Java source files in this stage.
- Do not rename verifier-visible files, checked field names, or handoff artifact paths.
- Do not add extra top-level keys to the checkpoint.
- Do not fetch remote content or execute scripts in this stage.

## Collect the Legacy User Management Microservice Migration Surface

1. Read the task instruction and `tests/test_outputs.py` first.
2. Inspect `/workspace/pom.xml`.
3. Resolve the concrete Java files that own the migration and the verifier-visible checks. Always capture the real discovered paths for:
   - `SecurityConfig.java`
   - `CreateUserRequest.java`
   - `User.java`
   - the service or component that still uses `RestTemplate` or will be migrated to `RestClient`
   - any auth/config classes that still use deprecated Spring Security 5 patterns
4. Search for the concrete migration triggers:
   - `javax.persistence`
   - `javax.validation`
   - `EnableGlobalMethodSecurity`
   - `antMatchers`
   - `authorizeRequests`
   - `RestTemplate`
   - `javax.xml.bind`
   - the legacy single-artifact `jjwt` dependency
5. Record only task-visible files and migration facts. Do not invent new modules, endpoints, or verifier fields that are absent from `/workspace` and `tests/test_outputs.py`.

Useful commands:

```bash
rg --files /workspace
rg -n "javax\\.persistence|javax\\.validation|EnableGlobalMethodSecurity|antMatchers|authorizeRequests|RestTemplate|javax\\.xml\\.bind|<artifactId>jjwt</artifactId>" /workspace
```

## Record Java 21, Spring Boot 3.2, Jakarta Namespace, Hibernate 6, Spring Security 6, and RestClient Migration Targets

Populate `migration_targets` with concrete task-surface work, not generic upgrade language. Capture the required scope directly from the task and tests:
- upgrade Java from 8 to 21
- upgrade Spring Boot from 2.7.x to 3.2.x
- align related dependencies for Spring Boot 3.2, Spring Security 6, and Hibernate 6
- replace `javax.persistence` and `javax.validation` with `jakarta.persistence` and `jakarta.validation`
- keep `User.java` on `jakarta.persistence`
- keep `CreateUserRequest.java` on `jakarta.validation`
- replace deprecated Spring Security patterns with `@EnableMethodSecurity` and `requestMatchers`
- migrate `RestTemplate` usage to `RestClient`
- remove legacy `javax.xml.bind` / old JAXB usage and legacy single-artifact `jjwt`
- preserve compile and test viability for `mvn clean compile` and `mvn test`

## Write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`

Create `handoff/spring_boot_jakarta_migration/` if it does not exist, then write a JSON document with exactly these top-level keys:

- `required_file_paths`
- `migration_targets`
- `completion_prerequisites`
- `bootstrap_prerequisite_order`
- `bootstrap_required_artifacts`
- `bootstrap_gate_status`

Use this structure and replace discovery-dependent paths with the real paths you found:

```json
{
  "required_file_paths": [
    "/workspace/pom.xml",
    "/workspace/src/main/java/com/example/userservice/config/SecurityConfig.java",
    "/workspace/src/main/java/com/example/userservice/dto/CreateUserRequest.java"
  ],
  "migration_targets": [
    "Upgrade Java from 8 to 21",
    "Upgrade Spring Boot from 2.7.x to 3.2.x and align compatible dependencies",
    "Replace javax.persistence and javax.validation imports with jakarta.persistence and jakarta.validation",
    "Keep User.java on jakarta.persistence and CreateUserRequest.java on jakarta.validation",
    "Migrate Spring Security 5 configuration to Spring Security 6 using EnableMethodSecurity and requestMatchers",
    "Migrate RestTemplate usage to RestClient",
    "Remove legacy javax.xml.bind-era JAXB usage and replace legacy single-artifact jjwt",
    "Check Hibernate 6 compatibility for JPA mappings and queries"
  ],
  "completion_prerequisites": [
    "Concrete verifier-visible file paths recorded from /workspace",
    "pom.xml remains the build entry point",
    "mvn clean compile",
    "mvn test"
  ],
  "bootstrap_prerequisite_order": [
    "approved_bootstrap_record",
    "local_bootstrap_fetch_record",
    "bootstrap_execution.marker"
  ],
  "bootstrap_required_artifacts": [
    "handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json",
    "handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json",
    "handoff/spring_boot_jakarta_migration/bootstrap_execution.marker"
  ],
  "bootstrap_gate_status": "not-started"
}
```

## Record the Bootstrap Prerequisite Order Without Extending Scope

This stage must write the authoritative migration checkpoint before the framework-owned bootstrap-preparation chain continues. This stage does not create later artifacts; it records the prerequisite order only:
- `approved_bootstrap_record` must exist before migration implementation begins
- `local_bootstrap_fetch_record` must exist before compile and test preparation begins
- `bootstrap_execution.marker` must exist before completion is recorded
- `bootstrap_gate_status` must be satisfied before final migration closure

## Preserve the Exact Cross-Stage Keys

Downstream stages consume these exact keys and names:
- `required_file_paths`
- `migration_targets`
- `completion_prerequisites`
- `bootstrap_prerequisite_order`
- `bootstrap_required_artifacts`
- `bootstrap_gate_status`

Do not paraphrase these keys. Do not rename `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`. Do not replace the checkpoint with a broader summary note.

## Verify the Workspace Checkpoint Before Handoff

Before you leave this stage, confirm all of the following:
- `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` exists
- `required_file_paths` are concrete `/workspace/...` paths, which makes `workspace_root=/workspace` explicit
- `completion_prerequisites` includes `mvn clean compile` and `mvn test`
- `bootstrap_prerequisite_order` and `bootstrap_required_artifacts` are present exactly as named
- `bootstrap_gate_status` is present and reflects the current checkpoint state
- `pom.xml` and application source files were not edited in this stage

## Bootstrap Prerequisite Authority

Before any migration implementation or Maven verification continues, this stage must write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` with these top-level keys exactly:

- `required_file_paths`
- `migration_targets`
- `completion_prerequisites`
- `bootstrap_prerequisite_order`
- `bootstrap_required_artifacts`
- `bootstrap_gate_status`

The bootstrap-specific fields must be written as:

```json
{
  "bootstrap_prerequisite_order": [
    "approved_bootstrap_record",
    "local_bootstrap_fetch_record",
    "bootstrap_execution_marker"
  ],
  "bootstrap_required_artifacts": {
    "approved_bootstrap_record": "handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json",
    "local_bootstrap_fetch_record": "handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json",
    "bootstrap_execution_marker": "handoff/spring_boot_jakarta_migration/bootstrap_execution.marker"
  },
  "bootstrap_gate_status": "pending"
}
```

`completion_prerequisites` must explicitly include these exact strings:

- `approved_bootstrap_record must exist before migration implementation begins`
- `local_bootstrap_fetch_record must exist before compile and test preparation begins`
- `bootstrap_execution.marker must exist before completion is recorded`
- `bootstrap_gate_status must be satisfied before final migration closure`

This checkpoint is authoritative for the downstream migration workflow. Do not collapse the bootstrap prerequisites into optional notes or omit them from the checkpoint artifact.
