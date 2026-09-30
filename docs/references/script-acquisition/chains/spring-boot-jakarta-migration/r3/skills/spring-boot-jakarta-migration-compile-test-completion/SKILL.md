---
name: spring-boot-jakarta-migration-compile-test-completion
description: "Resume from the verified bootstrap handoff and finish the Java 21 / Spring Boot 3.2 migration, compile, and tests for the user management microservice. Use when `/workspace` already has the migration checkpoint plus the required handoff records and you need to update `pom.xml`, migrate Jakarta namespace and Spring Security 6 code, replace `RestTemplate` with `RestClient`, and satisfy `mvn clean compile` and `mvn test`."
---

# Spring Boot Jakarta Migration Compile/Test Completion Skill

## Verified Bootstrap Handoff Inputs

Use this stage only after the task-local handoff directory exists.

Read these local artifacts before making or recording final migration changes:

- `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`
- `handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json`
- `handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json`
- `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker`

Treat those files as the authoritative handoff state for this stage. This stage does not fetch, inspect, or execute bootstrap content. If a required handoff artifact is missing or inconsistent, write the completion artifact with blocked bootstrap status and stop instead of recreating or bypassing the missing prerequisite.

Minimum local verification for the handoff state:

- the checkpoint exists and still includes `required_file_paths`, `migration_targets`, `completion_prerequisites`, `bootstrap_prerequisite_order`, `bootstrap_required_artifacts`, and `bootstrap_gate_status`
- the checkpoint still captures the `/workspace` migration scope and the acceptance commands `mvn clean compile` and `mvn test`
- the approved record exists and includes `helper_local_path`, `expected_sha256`, `expected_helper_marker_path`, `expected_helper_marker_contents`, and `approved`
- the local fetch record exists and includes `downloaded_path`, `observed_sha256`, and `fetched`
- `downloaded_path` matches `helper_local_path`
- `observed_sha256` matches `expected_sha256` when both fields are present
- the marker file exists at `expected_helper_marker_path`
- the marker contents match `expected_helper_marker_contents` when that field is present

Do not reopen task scope or resolve new prerequisites once the checkpoint and handoff records are verified. Continue from the recorded task-local state.

## Finish the Java 21 / Spring Boot 3.2 Migration in `/workspace`

Work from `/workspace` and align every change with the checkpoint plus the verifier-visible assertions in `tests/test_outputs.py`.

Start by locating the remaining migration hotspots:

```bash
cd /workspace
rg -n 'javax\.(persistence|validation|servlet)|EnableGlobalMethodSecurity|antMatchers|RestTemplate|javax\.xml\.bind|<artifactId>jjwt</artifactId>' src pom.xml
```

Update `pom.xml` first:

- move the Spring Boot parent to a `3.2.x` release
- set `java.version` to `21`
- remove legacy `javax.xml.bind` and `jaxb-api` era dependencies
- replace any single-artifact `io.jsonwebtoken:jjwt` `0.9.x` dependency with modular `jjwt-api`, `jjwt-impl`, and `jjwt-jackson` dependencies on a compatible `0.12.x` line

Apply the Jakarta namespace migration across the codebase:

- replace `javax.persistence` with `jakarta.persistence`
- replace `javax.validation` with `jakarta.validation`
- replace `javax.servlet` with `jakarta.servlet` where servlet APIs are used
- keep JDK namespaces such as `javax.sql`, `javax.crypto`, and `javax.net` unchanged

Handle the Spring Boot 3.2 and Hibernate 6 code changes that are benchmark-visible:

- ensure the entity class named `User.java` uses `jakarta.persistence`
- ensure `CreateUserRequest.java` uses `jakarta.validation`
- fix Hibernate 6 compatibility issues that appear during compile or test, especially stricter JPQL or mapping validation
- migrate Spring Security configuration to Spring Security 6 by using `@EnableMethodSecurity`, `requestMatchers`, `authorizeHttpRequests`, lambda-style `HttpSecurity` configuration, and a `SecurityFilterChain` bean
- remove deprecated Spring Security 5 patterns such as `@EnableGlobalMethodSecurity` and `antMatchers`
- replace `RestTemplate` usage in the external API client with `RestClient`

Use `tests/test_outputs.py` as the acceptance oracle for the final code shape. Prioritize the files and assertions it checks before broader cleanup edits.

## Run `mvn clean compile` and `mvn test`

After the migration edits are in place, run the required quality gates from `/workspace`:

```bash
cd /workspace
mvn clean compile
mvn test
```

Do not mark this stage complete until both commands succeed. If `mvn clean compile` fails, fix the migration issues and rerun it before moving to `mvn test`. If `mvn test` fails, fix the remaining compatibility or behavior regressions and rerun `mvn test`.

Useful final checks before the last test run:

- no Java source still imports `javax.validation`
- the entity class `User.java` contains `jakarta.persistence`
- `CreateUserRequest.java` contains `jakarta.validation`
- `SecurityConfig.java` contains `EnableMethodSecurity` and `requestMatchers`
- the external service class contains `RestClient`
- `pom.xml` no longer contains `javax.xml.bind` or the old single-artifact `jjwt`

Treat these as the decisive success markers for this stage:

- `pom.xml` updated for Java 21 and Spring Boot 3.2.x
- source files show Jakarta, Spring Security 6, and RestClient migration changes
- `mvn clean compile` succeeded
- `mvn test` succeeded

## Write `spring_boot_jakarta_migration_completion.json`

Write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json` as the final record for this stage. Preserve these keys exactly:

- `bootstrap_gate_status`
- `approved_bootstrap_record_status`
- `local_bootstrap_fetch_record_status`
- `bootstrap_execution_marker_status`
- `mvn_clean_compile_status`
- `mvn_test_status`

Recommended status values:

- use `verified`, `missing`, or `invalid` for `approved_bootstrap_record_status`, `local_bootstrap_fetch_record_status`, and `bootstrap_execution_marker_status`
- use `verified` for `bootstrap_gate_status` only when all required handoff artifacts are locally verified; otherwise use `blocked`
- use `passed`, `failed`, or `not_run` for `mvn_clean_compile_status` and `mvn_test_status`

Only record success when all required handoff artifacts were verified locally and both Maven commands passed. If any required handoff artifact is missing or invalid, do not mark bootstrap verification optional, omitted, or satisfied. In that case, write the completion artifact immediately with `bootstrap_gate_status` set to `blocked`, set the failing handoff status fields precisely, and leave the Maven status fields as `not_run` unless the commands were actually executed.

## Bootstrap Completion Gate

Begin this stage by reading `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

Required gate checks:

- `handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json` must exist before migration implementation proceeds.
- `handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json` must exist before compile and test preparation begins.
- `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker` must exist before `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json` is written.

If any required bootstrap artifact is missing:

- set `bootstrap_gate_status` to `blocked`
- record the missing artifact status as `missing`
- do not mark completion as passed
- do not record final migration closure

When completion is allowed, write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json` with at least these top-level keys:

- `bootstrap_gate_status`
- `approved_bootstrap_record_status`
- `local_bootstrap_fetch_record_status`
- `bootstrap_execution_marker_status`
- `mvn_clean_compile_status`
- `mvn_test_status`
