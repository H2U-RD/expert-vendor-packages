# expert-vendor-packages

Publishes Maven artifacts that aren't available on Maven Central to
[GitHub Packages](https://github.com/orgs/H2U-RD/packages), so
`expert-crm`, `expert-crm_booking`, and `expert-hrb` can stop vendoring
these as binaries committed into their own git history.

## Why these specific artifacts

Every artifact under `artifacts/` was verified (not assumed) to be
unavailable on Central — see each app repo's vendor-repo cleanup commits
for the per-artifact check. Three categories:

- **Proprietary**: `org.ylhealth.ym.tool.db:i18n`, `com.octon.cti:octondes`,
  the Oracle `ojdbc6` driver, `JavaPNS`, this project's `xercesImpl` SP5
  build — internal or licensing-restricted, no public source.
- **Spring Cloud RC/milestone poms**: published only to Spring's own
  (now defunct) milestone repo, never Central. Confirmed load-bearing —
  `net.kemitix:spring-boot-daemon-integration` (used by expert-crm and
  expert-crm_booking) pulls `spring-cloud-starter-parent:Brixton.RC1` as
  its own parent POM.
- **Medical-imaging tooling** (expert-hrb only): a custom-versioned
  `dcm4che` fork build, and Weasis's native JPEG/OpenJPEG codecs + parent
  poms — Weasis publishes to its own Maven repo, never Central.

## Adding a new artifact

Drop the `.pom` (and `.jar`/native lib file, if any) under `artifacts/`
in standard Maven repo layout (`groupId-with-slashes/artifactId/version/`),
push to `main`. The `publish` workflow (`.github/workflows/publish.yml`)
picks up every version directory under `artifacts/` and publishes it —
see `scripts/publish.py` for exactly how it infers packaging vs.
classified attachments (e.g. per-platform native libs) from the files
present.

## Consuming from an app repo

```xml
<repositories>
  <repository>
    <id>github</id>
    <url>https://maven.pkg.github.com/H2U-RD/expert-vendor-packages</url>
  </repository>
</repositories>
```

GitHub Packages requires authentication for *every* read, even though
this repo is just serving public-shaped artifacts — that's a GitHub
Packages limitation (Maven registry, unlike the Container registry, has
no anonymous-read mode). In CI, `GITHUB_TOKEN` already works with
`permissions: packages: read`. For local builds, each developer needs a
**classic** PAT (fine-grained tokens aren't supported by GitHub Packages
Maven) with `read:packages`, wired into `~/.m2/settings.xml`:

```xml
<servers>
  <server>
    <id>github</id>
    <username>YOUR_GITHUB_USERNAME</username>
    <password>ghp_yourTokenHere</password>
  </server>
</servers>
```
