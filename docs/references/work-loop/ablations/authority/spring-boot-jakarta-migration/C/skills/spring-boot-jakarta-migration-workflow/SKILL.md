---
name: spring-boot-jakarta-migration-workflow
description: "Complete the spring-boot-jakarta-migration migration in one archive-derived monolith with no auxiliary workflow artifact."
---

# spring-boot-jakarta-migration Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five source-stage responsibilities in source order. It retains the migration scope, actions, and checks while omitting only auxiliary workflow persistence, stage-transition execution, cross-stage activation, and reopen behavior. Keep transient planning in the current context and do not create an auxiliary workflow file.

## Inlined Stage 1: `spring-boot-jakarta-migration-entry-upgrade`

### POM and runtime baseline

Own only `/workspace/pom.xml` and immediately related application runtime properties. First inspect the Java version, Spring Boot parent/properties, JAXB, JJWT, and compiler-plugin areas. Make a focused `apply_patch` only for a concrete remaining Java 21, Spring Boot 3.2, or dependency discrepancy. Make four separate live observations of those bounded POM areas rather than relying on a remembered green result. A bounded compile probe is permitted after this POM slice; do not run `mvn test` here or inspect Security, Hibernate, or RestClient source as a shortcut.

---

## Inlined Stage 2: `spring-boot-jakarta-migration-namespace`

### Jakarta namespace slice

Own only `model/User.java`, `dto/CreateUserRequest.java`, and directly affected controller/request imports. Do not survey SecurityConfig, RestClient, the entire repository, or Maven output. Inspect four bounded facets with separate task actions: entity persistence imports, DTO validation imports, servlet/controller imports, and remaining `javax.` references within the owned paths. Make a focused `apply_patch` only for a concrete `javax.persistence`, `javax.validation`, or `javax.servlet` discrepancy; repeat the four independent observations when validation of this task area is needed.

---

## Inlined Stage 3: `spring-boot-jakarta-migration-security-hibernate`

### Security and persistence compatibility

Own only `config/SecurityConfig.java`, `CustomUserDetailsService.java`, `UserSecurity.java`, and directly related security/persistence mappings. Do not reopen POM, DTO, or RestClient work to finish the whole migration at once. Perform four separate live checks: method-security annotations and configuration, request matcher/filter-chain style, user-details/JWT role flow, and Hibernate/JPA compatibility in the owned paths. Apply a narrow patch only for an observed Spring Security 6 or Hibernate/Jakarta incompatibility, preserving existing JWT and role behavior.

---

## Inlined Stage 4: `spring-boot-jakarta-migration-restclient-verification`

### RestClient contract

Own only the HTTP-client service, directly related client configuration/injection paths, and their immediate tests or call sites. Do not reopen POM, namespace, or security files. Separately inspect client construction, request/response use sites, configuration/injection, and remaining `RestTemplate` references in those paths. Make a focused patch only for a concrete remaining RestTemplate-to-RestClient migration discrepancy. Do not treat a green build as an endpoint: a task-local compile probe is appropriate only for a specific client discrepancy, and do not run global `mvn test` at this stage.

---

## Inlined Stage 5: `spring-boot-jakarta-migration-continuation-gate`

### Complete the migration

Reconcile the current results from the four required task areas: POM/runtime, namespace, security/persistence, and client contract. If a concrete scoped discrepancy remains, return only to the matching task area for repair; do not repair another area opportunistically. When all requested migration work is complete, run the user-required `mvn clean compile` and `mvn test` checks, then finish normally. Do not begin a further audit round after successful completion.

## Completion

Report the task result truthfully after the requested deliverables and required validations are complete. Do not create auxiliary workflow artifacts or perform a post-completion re-entry.
