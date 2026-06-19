# Java Spring Boot Service

Scaffolds a minimal Spring Boot 3 service with:

- Maven `pom.xml` parameterized by component ID and Java version
- `Application.java` and `application.properties`
- `catalog-info.yaml` for Software Catalog registration

## Parameters

| Parameter | Purpose |
|-----------|---------|
| `componentId` | Catalog entity name and Maven artifact ID |
| `description` | Shown in catalog and repository |
| `owner` | Catalog owner entity ref |
| `javaVersion` | Java LTS version (`17` or `21`) |
| `packageName` | Java base package for generated sources |
| `repoUrl` | Target GitHub repository |

## Post-scaffold steps

1. Run `./mvnw spring-boot:run` locally
2. Confirm CI passes after first push
3. Verify catalog registration in RHDH
