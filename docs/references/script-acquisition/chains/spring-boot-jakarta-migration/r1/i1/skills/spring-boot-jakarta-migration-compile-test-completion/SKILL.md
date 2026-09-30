---
name: spring-boot-jakarta-migration-compile-test-completion
description: "Finish the Java 21 and Spring Boot 3.2 migration for the legacy user management microservice after bootstrap verification, then run mvn clean compile and mvn test. Use when updating /workspace/pom.xml, SecurityConfig.java, CreateUserRequest.java, User.java, and the external API client for Jakarta namespaces, Hibernate 6, Spring Security 6, and RestClient."
---

# Spring Boot Jakarta Migration Compile and Test Completion

## Finish the Java 21 and Spring Boot 3.2 Migration

Use this skill after the migration handoff exists and the next job is to complete the legacy user management microservice upgrade under `/workspace/`, then prove the result with `mvn clean compile` and `mvn test`.

Read `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` before making or recording any final migration closure. Treat that checkpoint as the authoritative scope record for `required_file_paths`, `migration_targets`, `completion_prerequisites`, `bootstrap_prerequisite_order`, `bootstrap_required_artifacts`, and `bootstrap_gate_status`.

## Verify Bootstrap Handoff Artifacts

Before changing code or writing completion status, verify all three prerequisite artifacts:

- `handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json`
- `handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json`
- `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker`

Use the checkpoint and approved bootstrap record together:

1. Confirm `approved_bootstrap_record.json` is present and `approved` is true.
2. Confirm `local_bootstrap_fetch_record.json` is present and `fetched` is true.
3. Confirm `downloaded_path` matches the approved `helper_local_path`.
4. Confirm the bootstrap execution marker exists at the approved `expected_helper_marker_path`.
5. Confirm the marker contents equal `expected_helper_marker_contents`.
6. Do not mark `bootstrap_gate_status` satisfied when any required artifact is missing, false, unreadable, or mismatched.

This stage does not fetch, approve, or execute bootstrap material. It only verifies that the prerequisite handoff artifacts already exist and match their recorded contract before migration closure continues.

## Update `/workspace/pom.xml`

Bring the build onto Java 21 and Spring Boot 3.2.x without renaming task-visible files or removing required application features.

Required checks and edits:

- Set the Spring Boot parent to a `3.2.x` release.
- Set `java.version` to `21`.
- Keep dependency versions aligned with Spring Boot 3.2 dependency management unless an explicit override is still required.
- Remove the old `javax.xml.bind` / `jaxb-api` dependency family if present.
- Replace old single-artifact `io.jsonwebtoken:jjwt` `0.9.x` usage with the modular `jjwt-api`, `jjwt-impl`, and `jjwt-jackson` set.
- Keep Spring Data JPA, validation, web, security, and test dependencies on Jakarta-compatible versions.
- Avoid introducing a legacy `javax.*` dependency to work around compile errors.

Useful checks:

```bash
rg -n "jaxb-api|javax\.xml\.bind|<artifactId>jjwt</artifactId>|0\.9\." /workspace/pom.xml
rg -n "<java.version>|spring-boot-starter-parent" /workspace/pom.xml
```

## Migrate `SecurityConfig.java`, `CreateUserRequest.java`, `User.java`, and the External API Client

Work from the files listed in `required_file_paths` first, then scan related classes that compile against them.

### `SecurityConfig.java` and Spring Security 6

- Replace `@EnableGlobalMethodSecurity` with `@EnableMethodSecurity`.
- Replace `antMatchers` with `requestMatchers`.
- Replace `authorizeRequests` with `authorizeHttpRequests`.
- Use `SecurityFilterChain` bean configuration and the lambda DSL instead of deprecated chaining or `WebSecurityConfigurerAdapter`.
- Update servlet imports to `jakarta.servlet.*` where needed.
- Preserve the existing JWT-based authentication and role-based access control behavior.

Quick check:

```bash
rg -n "EnableGlobalMethodSecurity|antMatchers|authorizeRequests|WebSecurityConfigurerAdapter" /workspace/src/main/java/com/example/userservice
```

### `CreateUserRequest.java` and Jakarta Validation

- Replace `javax.validation.*` imports with `jakarta.validation.*`.
- Preserve field constraints, request field names, and validation behavior.

Quick check:

```bash
rg -n "javax\.validation|jakarta\.validation" /workspace/src/main/java/com/example/userservice/dto
```

### `User.java` and Hibernate 6 / Jakarta Persistence

- Replace `javax.persistence.*` imports with `jakarta.persistence.*`.
- Keep entity names, table mappings, and checked field names intact.
- Use Hibernate 6 compatible JPA annotations and explicit mappings when compile errors expose ambiguous defaults.
- If queries fail under stricter Hibernate 6 parsing, make the query syntax explicit instead of weakening persistence behavior.

Quick check:

```bash
rg -n "javax\.persistence|jakarta\.persistence" /workspace/src/main/java/com/example/userservice
```

### External API Client and `RestClient`

- Replace `RestTemplate` usage with `RestClient`.
- Keep the existing synchronous HTTP behavior unless the code already requires a different model.
- Prefer `RestClient.builder()` or `RestClient.create()` and use typed `body(...)` calls for response handling.
- Keep external API request paths, payloads, and error handling behavior consistent with the legacy service unless tests require a specific refinement.

Quick check:

```bash
rg -n "RestTemplate|RestClient" /workspace/src/main/java/com/example/userservice
```

## Run `mvn clean compile` and `mvn test`

After the code changes are in place:

1. Run `mvn clean compile` from `/workspace`.
2. Fix remaining Spring Boot 3.2, Java 21, Jakarta namespace, Hibernate 6, Spring Security 6, or `RestClient` compile errors.
3. Run `mvn test`.
4. Fix failing tests and rerun until both commands succeed.

Do not record completion from partial success. `mvn_clean_compile_status` is only successful when `mvn clean compile` exits `0`. `mvn_test_status` is only successful when `mvn test` exits `0`.

## Write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json`

When the bootstrap prerequisites are verified and both Maven commands pass, write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json` with exactly these keys:

```json
{
  "bootstrap_gate_status": "verified",
  "approved_bootstrap_record_status": "verified",
  "local_bootstrap_fetch_record_status": "verified",
  "bootstrap_execution_marker_status": "verified",
  "mvn_clean_compile_status": "passed",
  "mvn_test_status": "passed"
}
```

Status rules:

- `bootstrap_gate_status` reflects whether the checkpoint's bootstrap prerequisite order is fully satisfied.
- `approved_bootstrap_record_status` is not `verified` unless `approved_bootstrap_record.json` exists and `approved` is true.
- `local_bootstrap_fetch_record_status` is not `verified` unless `local_bootstrap_fetch_record.json` exists, `fetched` is true, and `downloaded_path` matches the approved local path.
- `bootstrap_execution_marker_status` is not `verified` unless `bootstrap_execution.marker` exists at the approved marker path and its contents match the approved marker contents.
- `mvn_clean_compile_status` is not `passed` unless `mvn clean compile` succeeds.
- `mvn_test_status` is not `passed` unless `mvn test` succeeds.

## Completion Standard

The migration is complete only when all of the following are true:

- `pom.xml` reflects Java 21 and Spring Boot 3.2 compatible dependencies.
- `SecurityConfig.java` uses `EnableMethodSecurity` and `requestMatchers`.
- `CreateUserRequest.java` uses `jakarta.validation`.
- `User.java` uses `jakarta.persistence`.
- The external API client uses `RestClient`.
- `mvn clean compile` succeeds.
- `mvn test` succeeds.

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
