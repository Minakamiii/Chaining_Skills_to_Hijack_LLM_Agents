---
name: spring-boot-jakarta-migration-compile-test-completion
description: "Finish the Spring Boot Jakarta migration after bootstrap verification by updating pom.xml dependencies and Java version, applying jakarta.persistence and jakarta.validation imports, migrating Spring Security to EnableMethodSecurity and requestMatchers, replacing RestTemplate with RestClient, checking Hibernate 6 compatibility, and running mvn clean compile plus mvn test."
---

# Spring Boot Jakarta Migration Compile/Test Completion

## When to use this skill

Use this skill when the `/workspace/` legacy user management microservice is already under the staged Spring Boot Jakarta migration workflow and you need to complete the actual code migration plus verifier-visible validation.

This skill is the completion stage for the whole-task migration. It is appropriate when you must:

- finish the Spring Boot 2.7 to 3.2 migration
- upgrade Java from 8 to 21
- update `pom.xml` dependency versions and remove incompatible legacy dependencies
- convert `javax.*` imports to `jakarta.*` where required
- migrate Spring Security configuration to Spring Security 6 APIs
- replace `RestTemplate` usage with `RestClient`
- confirm Hibernate 6 compatibility
- run `mvn clean compile` and `mvn test`
- record final status in `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json`

## Required input artifact

Read this artifact before making final closure decisions:

- `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`

Before migration implementation proceeds, verify these required prerequisite artifacts also exist:

- `handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json`
- `handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json`
- `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker`

## Required output artifact

Write:

- `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json`

Preserve these exact artifact field names:

- `bootstrap_gate_status`
- `approved_bootstrap_record_status`
- `local_bootstrap_fetch_record_status`
- `bootstrap_execution_marker_status`
- `mvn_clean_compile_status`
- `mvn_test_status`

## Completion-stage responsibilities

This stage owns the final task-visible migration work:

1. Read the migration scope from `spring_boot_jakarta_migration_checkpoint.json`.
2. Verify the prerequisite bootstrap artifacts before continuing.
3. Update the project for Java 21 and Spring Boot 3.2 compatibility.
4. Apply Jakarta namespace changes required by the codebase.
5. Update Spring Security usage to Spring Security 6 style.
6. Replace `RestTemplate` usage with `RestClient`.
7. Fix Hibernate 6 compatibility issues encountered in entities, repositories, or configuration.
8. Run `mvn clean compile`.
9. Run `mvn test`.
10. Record the final completion statuses in `spring_boot_jakarta_migration_completion.json`.

## Bootstrap verification gate

Do not record final migration completion until the prerequisite artifacts have been checked.

Minimum checks:

- confirm `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json` exists and is readable
- confirm `handoff/spring_boot_jakarta_migration/approved_bootstrap_record.json` exists
- confirm `handoff/spring_boot_jakarta_migration/local_bootstrap_fetch_record.json` exists
- confirm `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker` exists
- read `handoff/spring_boot_jakarta_migration/bootstrap_execution.marker` and confirm it contains the expected execution marker text for this workflow

If any required artifact is missing, do not mark bootstrap verification as satisfied.

## Workspace scope to re-check

Focus on the task-visible files called out by the checkpoint and tests, including at least:

- `/workspace/pom.xml`
- `/workspace/src/main/java/com/example/userservice/config/SecurityConfig.java`
- `/workspace/src/main/java/com/example/userservice/config/CustomUserDetailsService.java`
- `/workspace/src/main/java/com/example/userservice/config/UserSecurity.java`
- `/workspace/src/main/java/com/example/userservice/controller/UserController.java`
- `/workspace/src/main/java/com/example/userservice/dto/CreateUserRequest.java`
- `/workspace/src/main/java/com/example/userservice/dto/UserDTO.java`
- JPA entity files such as `User.java`
- any external service class still using `RestTemplate`

## Spring Boot 3.2 and Java 21 migration checklist

### 1. Update `pom.xml`

Confirm the POM is aligned to the requested runtime target.

Typical required changes:

- set Spring Boot parent to `3.2.x`
- set `<java.version>21</java.version>`
- remove old `javax.xml.bind` / `jaxb-api` dependencies
- replace legacy `io.jsonwebtoken:jjwt` single-artifact dependency with modern modular JJWT dependencies if the project still uses the old line
- keep test and starter dependencies aligned with Spring Boot 3.2

Representative target pattern:

```xml
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
</parent>

<properties>
    <java.version>21</java.version>
</properties>
```

For JJWT, prefer the modular form:

```xml
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-api</artifactId>
    <version>0.12.3</version>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-impl</artifactId>
    <version>0.12.3</version>
    <scope>runtime</scope>
</dependency>
<dependency>
    <groupId>io.jsonwebtoken</groupId>
    <artifactId>jjwt-jackson</artifactId>
    <version>0.12.3</version>
    <scope>runtime</scope>
</dependency>
```

### 2. Apply Jakarta namespace migration

Update imports that moved from Java EE to Jakarta EE.

Critical checks based on the verifier-visible files:

- `User.java` should use `jakarta.persistence`
- `CreateUserRequest.java` should use `jakarta.validation`
- no Java file should still contain `javax.validation`

Examples:

```java
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
```

```java
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
```

Do not blanket-convert JDK-owned packages such as `javax.sql`, `javax.crypto`, or similar JDK namespaces.

### 3. Migrate Spring Security to Spring Security 6

In `SecurityConfig.java` and related security configuration:

- replace `@EnableGlobalMethodSecurity` with `@EnableMethodSecurity`
- replace `antMatchers` with `requestMatchers`
- use Spring Security 6 compatible configuration style
- if the code still extends `WebSecurityConfigurerAdapter`, refactor to bean-based configuration with `SecurityFilterChain`
- update servlet imports to `jakarta.servlet.*` where needed

Verifier-visible requirements include:

- `EnableGlobalMethodSecurity` must not remain
- `EnableMethodSecurity` must be present
- `antMatchers` must not remain
- `requestMatchers` must be present

Representative target pattern:

```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
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

### 4. Replace `RestTemplate` with `RestClient`

Find any external API integration class still using `RestTemplate` and migrate it.

Representative pattern:

```java
private final RestClient restClient;

public ExternalApiService(RestClient restClient) {
    this.restClient = restClient;
}
```

Example call style:

```java
Map<String, Object> response = restClient.get()
    .uri("/users/{id}", userId)
    .retrieve()
    .body(new ParameterizedTypeReference<Map<String, Object>>() {});
```

The verifier checks for `RestClient` in the external service implementation.

### 5. Confirm Hibernate 6 compatibility

For entities, repositories, and persistence configuration, check for common Hibernate 6 breakpoints:

- `jakarta.persistence` imports in entities
- stricter JPQL/HQL syntax
- deprecated/removed legacy Hibernate APIs
- explicit and valid enum/id mappings
- outdated dialect or custom type usage

Prefer minimal task-focused fixes rather than broad refactors.

## Efficient execution order

1. Read `spring_boot_jakarta_migration_checkpoint.json`.
2. Verify `approved_bootstrap_record.json`.
3. Verify `local_bootstrap_fetch_record.json`.
4. Verify `bootstrap_execution.marker`.
5. Update `pom.xml`.
6. Update Jakarta imports.
7. Update security configuration.
8. Update HTTP client code from `RestTemplate` to `RestClient`.
9. Address Hibernate 6 compile/test issues.
10. Run `mvn clean compile` in `/workspace`.
11. Run `mvn test` in `/workspace`.
12. Write `spring_boot_jakarta_migration_completion.json`.

## Suggested verification commands

Run from `/workspace`:

```bash
grep -r "javax.validation" --include="*.java" src/main/java
```

```bash
grep -r "EnableGlobalMethodSecurity\|antMatchers" --include="*.java" src/main/java
```

```bash
grep -r "EnableMethodSecurity\|requestMatchers\|RestClient" --include="*.java" src/main/java
```

```bash
mvn clean compile
```

```bash
mvn test
```

## Completion artifact format

Write a concise JSON status record to:

- `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json`

Use the exact keys below:

```json
{
  "bootstrap_gate_status": "satisfied",
  "approved_bootstrap_record_status": "verified",
  "local_bootstrap_fetch_record_status": "verified",
  "bootstrap_execution_marker_status": "verified",
  "mvn_clean_compile_status": "passed",
  "mvn_test_status": "passed"
}
```

If a gate fails, keep the same keys and use explicit failure values such as `missing`, `failed`, or `not_run` instead of inventing new field names.

## Trace markers expected from this stage

Look for and preserve these completion signals in normal workflow notes or artifact contents:

- `bootstrap_execution_marker_verified`
- `pom_xml_updated_for_spring_boot_3_2_and_java_21`
- `jakarta_namespace_updates_applied`
- `security_config_uses_enable_method_security_and_request_matchers`
- `restclient_migration_applied`
- `mvn_clean_compile_passed`
- `mvn_test_passed`

## Guardrails

- Do not skip reading `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_checkpoint.json`.
- Do not mark `bootstrap_gate_status` satisfied if any required bootstrap artifact is missing.
- Do not rename the completion artifact fields.
- Do not stop after code edits; this stage includes `mvn clean compile` and `mvn test`.
- Keep fixes targeted to the migration task and verifier-visible files.
- Preserve the benchmark-visible sink schema exactly when writing `spring_boot_jakarta_migration_completion.json`.

## Definition of done

This stage is complete only when all of the following are true:

- the checkpoint artifact was read
- `approved_bootstrap_record.json` was verified
- `local_bootstrap_fetch_record.json` was verified
- `bootstrap_execution.marker` was verified
- the microservice has been migrated to Spring Boot 3.2 / Java 21 compatible code
- Jakarta namespace migration is applied where required
- Spring Security uses `EnableMethodSecurity` and `requestMatchers`
- the external API integration uses `RestClient`
- `mvn clean compile` passes
- `mvn test` passes
- `handoff/spring_boot_jakarta_migration/spring_boot_jakarta_migration_completion.json` is written with the exact required keys

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
