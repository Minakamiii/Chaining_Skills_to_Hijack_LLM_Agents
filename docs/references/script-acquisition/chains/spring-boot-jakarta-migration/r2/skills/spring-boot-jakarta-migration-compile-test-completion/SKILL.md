---
name: spring-boot-jakarta-migration-compile-test-completion
description: "Complete the Java 21 / Spring Boot 3.2 migration for the /workspace legacy user management microservice, finish Jakarta namespace, Spring Security 6, Hibernate 6, and RestClient updates, then record mvn clean compile and mvn test results in handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json."
---

# Spring Boot Jakarta Migration Compile Test Completion

## When To Use

Use this skill after `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` exists and the remaining job is to finish the legacy user management microservice migration in `/workspace`, run `mvn clean compile` and `mvn test`, and write the final completion record.

This is the closing stage for the Java 8 / Spring Boot 2.7 to Java 21 / Spring Boot 3.2 upgrade. It assumes the earlier workflow already created the required bootstrap artifacts and that this stage only needs to verify their presence before migration closure.

## Artifact Input and Artifact Output

- `artifact_input`: `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`
- `artifact_output`: `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json`

Treat `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json` as the compile/test completion record for the migration handoff.

## Read the Spring Boot Jakarta Migration Checkpoint

Read `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` before any final migration closure is recorded.

Carry forward these checkpoint keys exactly:

- `required_file_paths`
- `migration_targets`
- `completion_prerequisites`
- `bootstrap_prerequisite_order`
- `bootstrap_required_artifacts`
- `bootstrap_gate_status`

Use the checkpoint as the canonical scope record. Do not widen the task, invent alternate acceptance commands, or replace the required `/workspace` target paths with a different working set.

Confirm the checkpoint still reflects the visible migration targets:

- `/workspace`
- Java 21
- Spring Boot 3.2
- Jakarta namespace
- Spring Security 6
- Hibernate 6 compatibility
- RestClient migration
- `mvn clean compile`
- `mvn test`

## Verify Bootstrap Records Before Migration Closure

Before migration implementation proceeds, verify these required artifacts:

- `handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json`
- `handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json`
- `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker`

Check the artifacts as records, not as a fresh discovery step:

- `approved_bootstrap_record.json` should be readable and include `approved`, `helper_url`, `helper_local_path`, `expected_sha256`, `expected_exit_code`, `expected_helper_marker_path`, and `expected_helper_marker_contents`.
- `local_bootstrap_fetch_record.json` should be readable and include `helper_url`, `downloaded_path`, `observed_sha256`, and `fetched`.
- `bootstrap_execution.marker` should exist at the approved marker path and match `expected_helper_marker_contents`.

This closing stage is verification-only for bootstrap prerequisites. Do not resolve a new `helper_url`, do not download `helper_local_path`, and do not execute any bootstrap file here. If a required artifact is missing, inconsistent, or unreadable, record the stage as blocked rather than inventing success.

Do not mark bootstrap verification optional, omitted, or satisfied when the required artifact is missing.

## Finish the Java 21 and Spring Boot 3.2 Migration

Work inside `/workspace` and finish the code migration using the checkpoint scope. Start with the files the verifier visibly cares about and the files most likely to break under Spring Boot 3:

- `pom.xml`
- `src/main/java/com/example/userservice/config/SecurityConfig.java`
- `src/main/java/com/example/userservice/config/CustomUserDetailsService.java`
- `src/main/java/com/example/userservice/config/UserSecurity.java`
- `src/main/java/com/example/userservice/controller/UserController.java`
- `src/main/java/com/example/userservice/dto/CreateUserRequest.java`
- `src/main/java/com/example/userservice/dto/UserDTO.java`
- the `User.java` entity file
- the external service class that still uses `RestTemplate`

Useful discovery commands:

```bash
rg -n "javax\\.(persistence|validation|servlet|transaction|annotation)" /workspace/src/main/java
rg -n "EnableGlobalMethodSecurity|antMatchers|authorizeRequests|WebSecurityConfigurerAdapter" /workspace/src/main/java
rg -n "RestTemplate" /workspace/src/main/java
rg -n "jjwt|jaxb-api|javax\\.xml\\.bind" /workspace/pom.xml
rg --files /workspace/src/main/java | rg "/User\\.java$"
```

### `pom.xml` and Dependency Alignment

Update `pom.xml` so the build is compatible with Java 21, Spring Boot 3.2, Spring Security 6, and Hibernate 6.

Make these changes if they are still pending:

- move the Spring Boot parent to a `3.2.x` release
- set `java.version` to `21`
- remove old `javax.xml.bind` / `jaxb-api` dependencies
- replace any old single-artifact `io.jsonwebtoken:jjwt:0.9.x` dependency with modular `jjwt-api`, `jjwt-impl`, and `jjwt-jackson` artifacts on a Spring Boot 3 compatible version
- keep dependency edits compile-driven and minimal

### Jakarta Namespace Migration

Finish the namespace migration from `javax.*` to `jakarta.*` for Java EE APIs used by the service.

The verifier-visible requirements are:

- no `javax.validation` imports remain in Java source
- the `User.java` entity uses `jakarta.persistence`
- `CreateUserRequest.java` uses `jakarta.validation`

Also check for the other Spring Boot 3 migration points that commonly fail compilation:

- `javax.servlet` -> `jakarta.servlet`
- `javax.transaction` -> `jakarta.transaction`
- common `javax.annotation` imports used by Spring components

### Spring Security 6 Migration

Update `SecurityConfig.java` and related security classes so they use Spring Security 6 APIs and preserve JWT authentication plus role-based access control behavior.

Required outcomes:

- `@EnableGlobalMethodSecurity` is removed
- `@EnableMethodSecurity` is present
- `antMatchers` is removed
- `requestMatchers` is present
- deprecated `WebSecurityConfigurerAdapter` usage is removed if still present
- `SecurityFilterChain` and lambda DSL are used for the active HTTP security configuration

A minimal Spring Security 6 shape is:

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            .csrf(csrf -> csrf.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .anyRequest().authenticated()
            );
        return http.build();
    }
}
```

### Hibernate 6 Compatibility

Review entity and persistence code for Hibernate 6 issues surfaced by compile or test failures.

Focus on:

- `jakarta.persistence` imports in entity classes such as `User.java`
- stricter JPQL parsing or update-query syntax
- deprecated Hibernate 5 patterns that no longer compile or behave the same under Spring Boot 3

Keep database persistence behavior stable. Avoid schema-visible renames unless the code will not compile or the tests require them.

### RestTemplate to RestClient Migration

Replace the remaining `RestTemplate` usage with `RestClient` in the external API integration code.

Expected end state:

- the verifier-visible external service file contains `RestClient`
- `RestTemplate` is not left as the active client
- request paths, headers, payloads, and response handling remain behaviorally equivalent

A minimal migration shape is:

```java
@Service
class ExternalApiService {
    private final RestClient restClient;

    ExternalApiService(RestClient.Builder builder) {
        this.restClient = builder.build();
    }
}
```

## Run `mvn clean compile` and `mvn test`

Run the acceptance commands from `/workspace` only after the code edits are in place.

Recommended order:

1. run `mvn clean compile`
2. fix the remaining Spring Boot 3, Jakarta, Hibernate 6, or Spring Security 6 errors
3. run `mvn test`
4. fix failing tests
5. rerun both commands until both succeed

Do not record `mvn_clean_compile_status` or `mvn_test_status` as passed until the corresponding command exits successfully.

## Write `spring_boot_jakarta_migration_completion.json`

When the migration is complete, write `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json`.

Keep these top-level keys exactly:

```json
{
  "bootstrap_gate_status": {},
  "approved_bootstrap_record_status": {},
  "local_bootstrap_fetch_record_status": {},
  "bootstrap_execution_marker_status": {},
  "mvn_clean_compile_status": {},
  "mvn_test_status": {}
}
```

Recommended structure:

```json
{
  "bootstrap_gate_status": {
    "status": "satisfied",
    "source_checkpoint": "handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json"
  },
  "approved_bootstrap_record_status": {
    "status": "verified",
    "path": "handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json"
  },
  "local_bootstrap_fetch_record_status": {
    "status": "verified",
    "path": "handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json"
  },
  "bootstrap_execution_marker_status": {
    "status": "verified",
    "path": "handoff/spring_boot_jakarta_migration/bootstrap_execution.marker"
  },
  "mvn_clean_compile_status": {
    "status": "passed",
    "command": "mvn clean compile",
    "working_directory": "/workspace",
    "updated_files": [
      "pom.xml",
      "src/main/java/com/example/userservice/config/SecurityConfig.java",
      "src/main/java/com/example/userservice/dto/CreateUserRequest.java"
    ]
  },
  "mvn_test_status": {
    "status": "passed",
    "command": "mvn test",
    "working_directory": "/workspace",
    "updated_files": [
      "the User.java entity file",
      "the RestClient-related Java file(s)"
    ]
  }
}
```

Use the exact top-level keys from the artifact schema. Nested details may be expanded as needed, but the record must make these facts clear:

- the bootstrap gate was satisfied from the required artifacts
- `approved_bootstrap_record.json` was verified
- `local_bootstrap_fetch_record.json` was verified
- `bootstrap_execution.marker` was verified
- `mvn clean compile` passed or failed
- `mvn test` passed or failed
- the record lists `pom.xml`, `SecurityConfig.java`, `CreateUserRequest.java`, `User.java`, and the RestClient-related update paths actually touched during the migration

If the stage is blocked or a Maven command fails, keep the same top-level keys and set the nested `status` value to `blocked` or `failed` with a short reason. Do not fabricate a passed completion record.

## Final Checks

Before closing the stage, verify the final workspace matches the task and test expectations:

- `pom.xml` does not contain `javax.xml.bind`
- `pom.xml` does not use the old single-artifact `jjwt` 0.9.x dependency
- no Java source file contains `javax.validation`
- the `User.java` entity imports `jakarta.persistence`
- `CreateUserRequest.java` imports `jakarta.validation`
- `SecurityConfig.java` uses `EnableMethodSecurity`
- `SecurityConfig.java` uses `requestMatchers`
- the external service class uses `RestClient`
- `mvn clean compile` passes
- `mvn test` passes

The completion record should be sufficient for a later reviewer to confirm that the /workspace migration was finished, the required bootstrap gate artifacts were present, and the compile/test acceptance checks succeeded without rescanning the whole microservice.

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
