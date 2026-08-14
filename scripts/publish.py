#!/usr/bin/env python3
"""Publish every artifact under artifacts/ (a standard Maven repo-layout tree)
to GitHub Packages via `mvn deploy:deploy-file`.

Each leaf directory (artifacts/<groupPath>/<artifactId>/<version>/) is one
Maven coordinate. Handles three shapes:
  - main file + pom (+ optional classified attachments, e.g. per-platform jars)
  - pom + classified attachments only, no unclassified main file (e.g. the
    Weasis native libs, which are always resolved with an explicit classifier)
  - pom only (parent/BOM poms)
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "artifacts"
REPO_ID = "github"
REPO_URL = "https://maven.pkg.github.com/H2U-RD/expert-vendor-packages"

dry_run = "--dry-run" in sys.argv


def find_version_dirs(root: Path):
    for pom in root.rglob("*.pom"):
        yield pom.parent


def main():
    version_dirs = sorted(set(find_version_dirs(ROOT)))
    print(f"Found {len(version_dirs)} version directories\n")

    for vdir in version_dirs:
        parts = vdir.relative_to(ROOT).parts
        artifact_id, version = parts[-2], parts[-1]
        group_id = ".".join(parts[:-2])

        files = [f for f in vdir.iterdir() if f.is_file() and f.suffix != ".sha1"]
        poms = [f for f in files if f.suffix == ".pom"]
        if len(poms) != 1:
            print(f"SKIP {vdir}: expected exactly 1 pom, found {len(poms)}")
            continue
        pom = poms[0]
        others = [f for f in files if f != pom]

        prefix = f"{artifact_id}-{version}"
        main_file = None
        classified = []  # (classifier, ext, path)
        for f in others:
            stem = f.name[: -len(f.suffix)] if f.suffix else f.name
            if stem == prefix:
                main_file = f
            elif stem.startswith(prefix + "-"):
                classifier = stem[len(prefix) + 1:]
                classified.append((classifier, f.suffix.lstrip("."), f))
            else:
                print(f"WARN {vdir}: unrecognized file {f.name}, skipping it")

        cmd = [
            "mvn", "-B", "deploy:deploy-file",
            f"-DrepositoryId={REPO_ID}",
            f"-Durl={REPO_URL}",
            f"-DgroupId={group_id}",
            f"-DartifactId={artifact_id}",
            f"-Dversion={version}",
            f"-DpomFile={pom}",
            "-DgeneratePom=false",
        ]

        if main_file:
            packaging = main_file.suffix.lstrip(".")
            cmd += [f"-Dfile={main_file}", f"-Dpackaging={packaging}"]
        else:
            # No unclassified main artifact (parent pom, or classifier-only
            # native libs) — deploy the pom itself as the primary file.
            cmd += [f"-Dfile={pom}", "-Dpackaging=pom"]

        if classified:
            cmd += [
                "-Dfiles=" + ",".join(str(f) for _, _, f in classified),
                "-Dclassifiers=" + ",".join(c for c, _, _ in classified),
                "-Dtypes=" + ",".join(t for _, t, _ in classified),
            ]

        label = f"{group_id}:{artifact_id}:{version}"
        if dry_run:
            print(f"[dry-run] {label}")
            print("  " + " ".join(cmd) + "\n")
            continue

        print(f"Publishing {label} ...")
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"FAILED: {label}")
            sys.exit(result.returncode)

    print("\nDone.")


if __name__ == "__main__":
    main()
