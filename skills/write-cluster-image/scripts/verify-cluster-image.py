#!/usr/bin/env python3
"""Verify Sealos cluster image deploy directories.

The checks intentionally avoid cluster-mutating commands. Helm is used only for
local lint/template rendering.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path


Status = str


@dataclass
class Check:
    status: Status
    area: str
    message: str
    detail: str = ""


class Reporter:
    def __init__(self) -> None:
        self.checks: list[Check] = []

    def add(self, status: Status, area: str, message: str, detail: str = "") -> None:
        self.checks.append(Check(status, area, message, detail))

    def pass_(self, area: str, message: str, detail: str = "") -> None:
        self.add("PASS", area, message, detail)

    def warn(self, area: str, message: str, detail: str = "") -> None:
        self.add("WARN", area, message, detail)

    def fail(self, area: str, message: str, detail: str = "") -> None:
        self.add("FAIL", area, message, detail)

    def unknown(self, area: str, message: str, detail: str = "") -> None:
        self.add("UNKNOWN", area, message, detail)

    def exit_code(self) -> int:
        return 1 if any(check.status == "FAIL" for check in self.checks) else 0

    def print(self) -> None:
        order = {"FAIL": 0, "WARN": 1, "UNKNOWN": 2, "PASS": 3}
        result = "FAIL" if self.exit_code() else "PASS"
        if result == "PASS" and any(c.status in {"WARN", "UNKNOWN"} for c in self.checks):
            result = "PASS_WITH_NOTES"

        print("Cluster Image Review")
        print(f"Result: {result}")
        print()

        counts: dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0, "UNKNOWN": 0}
        for check in self.checks:
            counts[check.status] = counts.get(check.status, 0) + 1
        print(
            "Summary: "
            f"{counts['FAIL']} fail, {counts['WARN']} warn, "
            f"{counts['UNKNOWN']} unknown, {counts['PASS']} pass"
        )
        print()

        for check in sorted(self.checks, key=lambda c: (order.get(c.status, 99), c.area, c.message)):
            print(f"- {check.status} [{check.area}] {check.message}")
            if check.detail:
                for line in check.detail.splitlines():
                    print(f"  {line}")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def compact_output(stdout: str, stderr: str, max_lines: int = 8) -> str:
    output = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
    lines = output.splitlines()
    if len(lines) > max_lines:
        lines = lines[:max_lines] + ["..."]
    return "\n".join(lines)


def run_command(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def find_chart_dirs(deploy_dir: Path, requested: str | None) -> list[Path]:
    charts_dir = deploy_dir / "charts"
    if requested:
        chart = charts_dir / requested
        return [chart] if chart.exists() else []
    if not charts_dir.exists():
        return []
    return sorted(path for path in charts_dir.iterdir() if (path / "Chart.yaml").is_file())


def parse_cmd_entrypoints(kubefile: str) -> list[str]:
    entrypoints: list[str] = []
    for line in kubefile.splitlines():
        stripped = line.strip()
        if not stripped.startswith("CMD"):
            continue
        entrypoints.extend(re.findall(r"([\w./-]+-entrypoint\.sh)", stripped))
        entrypoints.extend(re.findall(r"([\w./-]+\.sh)", stripped))
    return list(dict.fromkeys(entrypoints))


def parse_env_names(kubefile: str) -> list[str]:
    names: list[str] = []
    for line in kubefile.splitlines():
        stripped = line.strip()
        if not stripped.startswith("ENV "):
            continue
        payload = stripped[4:].strip()
        if "=" in payload:
            names.append(payload.split("=", 1)[0].strip())
        else:
            parts = payload.split()
            if parts:
                names.append(parts[0])
    return names


def env_is_used(name: str, text: str) -> bool:
    patterns = [
        f"${{{name}}}",
        f"${{{name}:-",
        f"${{{name}:=",
        f"${name}",
    ]
    return any(pattern in text for pattern in patterns)


def parse_top_level_image(values_text: str) -> str | None:
    image_match = re.search(r"(?ms)^image:\s*\n(?P<body>(?:^[ \t]+.+\n?)+)", values_text)
    if not image_match:
        return None
    body = image_match.group("body")
    repository = re.search(r'(?m)^[ \t]+repository:\s*["\']?([^"\'\s#]+)', body)
    tag = re.search(r'(?m)^[ \t]+tag:\s*["\']?([^"\'\s#]+)', body)
    if not repository:
        return None
    image = repository.group(1)
    if tag and tag.group(1):
        image = f"{image}:{tag.group(1)}"
    return image


def static_kubefile_checks(reporter: Reporter, deploy_dir: Path) -> list[Path]:
    kubefile_path = deploy_dir / "Kubefile"
    if not kubefile_path.is_file():
        reporter.fail("Kubefile", "deploy/Kubefile is missing")
        return []

    kubefile = read_text(kubefile_path)
    from_lines = re.findall(r"(?mi)^\s*FROM\s+([^\s]+)", kubefile)
    if from_lines and all(image == "scratch" for image in from_lines):
        reporter.pass_("Kubefile", "uses FROM scratch")
    elif from_lines:
        reporter.fail("Kubefile", "cluster image should use FROM scratch", f"Found: {', '.join(from_lines)}")
    else:
        reporter.fail("Kubefile", "missing FROM line")

    if re.search(r"(?mi)^\s*COPY\s+.*\bcharts\b.*\bcharts\b", kubefile):
        reporter.pass_("Kubefile", "copies charts into the cluster image")
    else:
        reporter.fail("Kubefile", "missing COPY for charts")

    entrypoint_names = parse_cmd_entrypoints(kubefile)
    if not entrypoint_names:
        entrypoint_names = [path.name for path in sorted(deploy_dir.glob("*-entrypoint.sh"))]
        if entrypoint_names:
            reporter.warn("Kubefile", "could not parse CMD entrypoint; using entrypoint files found in deploy/")
        else:
            reporter.fail("Kubefile", "missing CMD entrypoint")

    entrypoints: list[Path] = []
    for name in entrypoint_names:
        entrypoint = deploy_dir / name
        if entrypoint.is_file():
            entrypoints.append(entrypoint)
            reporter.pass_("Kubefile", f"CMD entrypoint exists: {name}")
        else:
            reporter.fail("Kubefile", f"CMD references missing entrypoint: {name}")

    for name in parse_env_names(kubefile):
        if any(env_is_used(name, read_text(entrypoint)) for entrypoint in entrypoints):
            reporter.pass_("Kubefile", f"ENV {name} is consumed by the entrypoint")
        else:
            reporter.warn("Kubefile", f"ENV {name} is not visibly consumed by the entrypoint")

    return entrypoints


def entrypoint_checks(reporter: Reporter, entrypoint: Path) -> None:
    text = read_text(entrypoint)
    name = entrypoint.name

    bash = shutil.which("bash")
    if bash:
        result = run_command([bash, "-n", str(entrypoint)])
        if result.returncode == 0:
            reporter.pass_("Entrypoint", f"bash -n passed for {name}")
        else:
            reporter.fail("Entrypoint", f"bash -n failed for {name}", compact_output(result.stdout, result.stderr))
    else:
        reporter.unknown("Entrypoint", "bash is not available for syntax checking")

    if re.search(r"(?m)^\s*set\s+-[A-Za-z]*e", text):
        reporter.pass_("Entrypoint", f"{name} enables exit-on-error")
    else:
        reporter.fail("Entrypoint", f"{name} should use set -e")

    if "helm upgrade -i" in text or "helm upgrade --install" in text:
        reporter.pass_("Entrypoint", f"{name} uses helm upgrade install pattern")
    else:
        reporter.fail("Entrypoint", f"{name} should install with helm upgrade -i")

    if "--create-namespace" in text:
        reporter.pass_("Entrypoint", f"{name} creates the release namespace")
    else:
        reporter.warn("Entrypoint", f"{name} does not pass --create-namespace")

    if "/root/.sealos/cloud/values/core/" in text and "USER_VALUES_PATH" in text:
        reporter.pass_("Entrypoint", f"{name} defines the persistent user values path")
    else:
        reporter.fail("Entrypoint", f"{name} should persist user values under /root/.sealos/cloud/values/core/")

    if re.search(r'-f\s+"?\$\{?USER_VALUES_PATH\}?', text):
        reporter.pass_("Entrypoint", f"{name} applies the persistent user values file")
    else:
        reporter.fail("Entrypoint", f"{name} is missing -f USER_VALUES_PATH in helm arguments")

    if "cp " in text and "USER_VALUES_PATH" in text:
        reporter.pass_("Entrypoint", f"{name} copies default user values on first install")
    else:
        reporter.warn("Entrypoint", f"{name} does not visibly create the first-install user values file")

    if "get_cm_value" in text and "sealos-config" in text:
        reporter.pass_("Entrypoint", f"{name} reads sealos-system/sealos-config for cluster defaults")
    else:
        reporter.warn("Entrypoint", f"{name} does not visibly read sealos-system/sealos-config")

    if "--set-string" in text:
        reporter.pass_("Entrypoint", f"{name} uses --set-string for auto-configured values")
    else:
        reporter.warn("Entrypoint", f"{name} does not visibly use --set-string")

    if "//,/\\\\," in text or "//,/\\\\\\," in text:
        reporter.pass_("Entrypoint", f"{name} escapes commas before passing Helm set values")
    elif "add_set_string" in text:
        reporter.warn("Entrypoint", f"{name} has add_set_string but comma escaping was not detected")

    if "HELM_OPTIONS" in text and "HELM_OPTS" in text:
        reporter.pass_("Entrypoint", f"{name} supports HELM_OPTIONS and HELM_OPTS")
    else:
        reporter.warn("Entrypoint", f"{name} does not support both HELM_OPTIONS and HELM_OPTS")

    if re.search(r"(?m)^\s*set\s+-[A-Za-z]*u", text):
        unguarded = re.findall(r"\$\{([a-z][A-Za-z0-9_]*)\}", text)
        if unguarded:
            reporter.warn(
                "Entrypoint",
                f"{name} uses set -u with unguarded lowercase expansions",
                ", ".join(sorted(set(unguarded))[:10]),
            )


def chart_static_checks(reporter: Reporter, deploy_dir: Path, chart_dirs: list[Path]) -> None:
    if not chart_dirs:
        reporter.fail("Helm chart", "no chart found under deploy/charts")
        return

    app_in_chart = False
    for chart in chart_dirs:
        chart_name = chart.name
        if (chart / "Chart.yaml").is_file():
            reporter.pass_("Helm chart", f"{chart_name}/Chart.yaml exists")
        else:
            reporter.fail("Helm chart", f"{chart_name}/Chart.yaml is missing")

        values_path = chart / "values.yaml"
        if values_path.is_file():
            reporter.pass_("Helm chart", f"{chart_name}/values.yaml exists")
            values_text = read_text(values_path)
            if " required " in values_text or "required " in values_text:
                reporter.warn("Helm chart", f"{chart_name}/values.yaml contains Helm required calls")
            if re.search(r'(?m)^[ \t]+tag:\s*["\']{0,1}["\']?\s*(#.*)?$', values_text):
                reporter.warn("Helm chart", f"{chart_name}/values.yaml appears to leave an image tag empty")
            if re.search(r"(?i)(password|secret|token|apikey|api_key):\s*['\"]?[^'\"\s#]+", values_text):
                reporter.warn("Helm chart", f"{chart_name}/values.yaml may contain non-empty secret-like defaults")
        else:
            reporter.fail("Helm chart", f"{chart_name}/values.yaml is missing")

        templates = chart / "templates"
        if templates.is_dir() and any(templates.glob("*.yaml")):
            reporter.pass_("Helm chart", f"{chart_name}/templates contains YAML templates")
        else:
            reporter.fail("Helm chart", f"{chart_name}/templates is missing YAML templates")

        for template in templates.glob("*.yaml") if templates.is_dir() else []:
            template_text = read_text(template)
            if re.search(r"(?m)^\s*kind:\s*App\s*$", template_text):
                app_in_chart = True

    manifest_apps = []
    manifests_dir = deploy_dir / "manifests"
    if manifests_dir.is_dir():
        for manifest in manifests_dir.glob("*"):
            if not manifest.is_file():
                continue
            text = read_text(manifest)
            if re.search(r"(?m)^\s*kind:\s*App\s*$", text):
                manifest_apps.append(manifest)

    if app_in_chart:
        reporter.pass_("Helm chart", "Sealos App resources are present in Helm templates")
    elif manifest_apps:
        names = ", ".join(str(path.relative_to(deploy_dir)) for path in manifest_apps)
        reporter.fail(
            "Helm chart",
            "Sealos App resources exist only outside the Helm chart",
            f"Move or duplicate into charts/<chart>/templates/: {names}",
        )
    else:
        reporter.unknown("Helm chart", "no Sealos App resource detected; acceptable for non-desktop services")


def image_alignment_checks(reporter: Reporter, deploy_dir: Path, chart_dirs: list[Path]) -> None:
    images_path = deploy_dir / "images" / "shim" / "images"
    chart_images = []
    for chart in chart_dirs:
        values_path = chart / "values.yaml"
        if values_path.is_file():
            image = parse_top_level_image(read_text(values_path))
            if image:
                chart_images.append(image)

    if not images_path.exists():
        if chart_images:
            reporter.warn(
                "Image preload",
                "images/shim/images is missing while chart image defaults exist",
                "Add it when sealos build must preload or mirror runtime images.",
            )
        else:
            reporter.unknown("Image preload", "images/shim/images is missing and no top-level chart image was detected")
        return

    lines = [
        line.strip()
        for line in read_text(images_path).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        reporter.warn("Image preload", "images/shim/images exists but is empty")
        return

    if all("/" in line and (":" in line.rsplit("/", 1)[-1] or "@" in line) for line in lines):
        reporter.pass_("Image preload", "images/shim/images uses fully qualified tagged or digested image names")
    else:
        reporter.warn("Image preload", "some images/shim/images entries are not fully qualified with tag or digest")

    for image in chart_images:
        if image in lines:
            reporter.pass_("Image preload", f"chart runtime image is listed in images/shim/images: {image}")
        else:
            reporter.warn("Image preload", f"chart runtime image is not listed in images/shim/images: {image}")


def helm_platform() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_name = {"linux": "linux", "darwin": "darwin"}.get(system)
    arch = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
        "armv7l": "arm",
    }.get(machine)
    if not os_name or not arch:
        raise RuntimeError(f"unsupported platform for Helm download: {system}/{machine}")
    return os_name, arch


def download_url(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as response:
        with dest.open("wb") as handle:
            shutil.copyfileobj(response, handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_helm(version: str, cache_dir: Path) -> Path:
    os_name, arch = helm_platform()
    install_dir = cache_dir / "helm" / version / f"{os_name}-{arch}"
    helm_path = install_dir / "helm"
    if helm_path.exists():
        return helm_path

    install_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"helm-{version}-{os_name}-{arch}.tar.gz"
    base_url = f"https://get.helm.sh/{base_name}"

    with tempfile.TemporaryDirectory(prefix="helm-download-") as temp:
        temp_dir = Path(temp)
        archive = temp_dir / base_name
        checksum_file = temp_dir / f"{base_name}.sha256sum"
        download_url(base_url, archive)
        download_url(f"{base_url}.sha256sum", checksum_file)

        expected = checksum_file.read_text(encoding="utf-8").split()[0].strip()
        actual = sha256(archive)
        if actual != expected:
            raise RuntimeError(f"Helm checksum mismatch: expected {expected}, got {actual}")

        member_name = f"{os_name}-{arch}/helm"
        with tarfile.open(archive, "r:gz") as tar:
            member = tar.getmember(member_name)
            source = tar.extractfile(member)
            if source is None:
                raise RuntimeError(f"Helm archive is missing {member_name}")
            temp_helm = temp_dir / "helm"
            with temp_helm.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            temp_helm.chmod(temp_helm.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            shutil.move(str(temp_helm), str(helm_path))

    return helm_path


def find_helm(args: argparse.Namespace, reporter: Reporter) -> Path | None:
    helm = shutil.which("helm")
    if helm:
        reporter.pass_("Helm", f"using system helm: {helm}")
        return Path(helm)

    if not args.ensure_helm:
        reporter.unknown("Helm", "helm is not installed; rerun with --ensure-helm to download a local copy")
        return None

    try:
        helm_path = ensure_helm(args.helm_version, Path(args.tool_cache))
    except Exception as exc:  # noqa: BLE001 - show actionable download failure.
        reporter.unknown("Helm", "failed to download local helm", str(exc))
        return None

    result = run_command([str(helm_path), "version", "--short"])
    if result.returncode == 0:
        reporter.pass_("Helm", f"downloaded helm {args.helm_version}: {helm_path}")
        return helm_path

    reporter.unknown("Helm", "downloaded helm did not execute", compact_output(result.stdout, result.stderr))
    return None


def helm_checks(
    reporter: Reporter,
    helm: Path | None,
    chart_dirs: list[Path],
    release: str | None,
    namespace: str,
) -> None:
    if not helm:
        reporter.unknown("Helm", "skipping helm lint/template checks")
        return
    for chart in chart_dirs:
        release_name = release or chart.name.replace("_", "-")
        lint = run_command([str(helm), "lint", str(chart)])
        if lint.returncode == 0:
            reporter.pass_("Helm", f"helm lint passed for {chart}")
        else:
            reporter.fail("Helm", f"helm lint failed for {chart}", compact_output(lint.stdout, lint.stderr))

        template = run_command([str(helm), "template", release_name, str(chart), "-n", namespace])
        if template.returncode == 0:
            reporter.pass_("Helm", f"helm template passed for {chart}")
        else:
            reporter.fail("Helm", f"helm template failed for {chart}", compact_output(template.stdout, template.stderr))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a Sealos cluster image deploy directory.")
    parser.add_argument("deploy_dir", help="Path to the deploy directory containing Kubefile and charts/")
    parser.add_argument("--chart", help="Specific chart directory name under deploy/charts")
    parser.add_argument("--release", help="Helm release name for helm template")
    parser.add_argument("--namespace", default="default", help="Namespace for helm template")
    parser.add_argument(
        "--ensure-helm",
        action="store_true",
        help="Download a local Helm binary when helm is not installed.",
    )
    parser.add_argument(
        "--helm-version",
        default=os.environ.get("HELM_VERSION", "v3.15.4"),
        help="Helm version to download with --ensure-helm. Default: %(default)s",
    )
    parser.add_argument(
        "--tool-cache",
        default=os.environ.get("WRITE_CLUSTER_IMAGE_TOOL_CACHE", "/tmp/write-cluster-image-tools"),
        help="Tool cache for downloaded Helm. Default: %(default)s",
    )
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)
    reporter = Reporter()
    deploy_dir = Path(args.deploy_dir).resolve()

    if not deploy_dir.is_dir():
        reporter.fail("Deploy directory", f"deploy directory does not exist: {deploy_dir}")
        reporter.print()
        return reporter.exit_code()

    reporter.pass_("Deploy directory", f"found deploy directory: {deploy_dir}")
    entrypoints = static_kubefile_checks(reporter, deploy_dir)
    for entrypoint in entrypoints:
        entrypoint_checks(reporter, entrypoint)

    chart_dirs = find_chart_dirs(deploy_dir, args.chart)
    if args.chart and not chart_dirs:
        reporter.fail("Helm chart", f"requested chart was not found: deploy/charts/{args.chart}")
    chart_static_checks(reporter, deploy_dir, chart_dirs)
    image_alignment_checks(reporter, deploy_dir, chart_dirs)

    helm = find_helm(args, reporter)
    helm_checks(reporter, helm, chart_dirs, args.release, args.namespace)

    reporter.print()
    return reporter.exit_code()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
