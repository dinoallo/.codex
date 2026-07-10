# Sealos Cluster Image Deploy Reference

Use this reference when creating or reviewing Sealos cluster image deploy files. Use a local checkout of the Sealos repository as the pattern source: inspect its `deploy/` directories and prefer the nearest match by service type, install flow, and chart shape. Frontend provider deploy directories are useful examples for desktop App, ingress, and cloud-domain wiring, but do not treat any one directory as the universal model.

## Directory Shape

```text
deploy/
  Kubefile
  <service>-entrypoint.sh
  images/
    shim/
      images
  charts/
    <chart>/
      Chart.yaml
      values.yaml
      <service>-values.yaml
      templates/
        _helpers.tpl
        app.yaml
        configmap.yaml
        deployment.yaml
        ingress.yaml
        service.yaml
```

Use `images/shim/images` when the cluster image must declare external container images for packaging or mirroring, or when chart defaults do not fully express every runtime image. It is a plain newline-separated list, for example:

```text
docker.io/library/nginx:latest
```

Prefer fully qualified image names. Pin tags or digests when the release process requires reproducibility. Keep this list aligned with the chart defaults and any image tag default in `Kubefile` `ENV`; a cluster image cannot preload an arbitrary tag that was not included at build time.

## Kubefile

The cluster image is a deploy artifact, not the app runtime container. Use `FROM scratch`, copy the chart and entrypoint, optionally copy generated registry contents, and add `ENV` only for this project's install-time defaults:

```dockerfile
FROM scratch

USER 65532:65532

COPY registry registry
COPY charts charts
COPY <service>-entrypoint.sh <service>-entrypoint.sh

# Optional: only include ENV values that this service consumes.
# ENV <installDefaultName>="<safe-default>"

CMD ["bash <service>-entrypoint.sh"]
```

Rules:

- Include `COPY registry registry` when the build pipeline materializes an offline registry directory for embedded images.
- Copy only deploy artifacts needed by the entrypoint.
- Treat `ENV` as project-specific, optional install defaults. Use it only when the entrypoint reads that variable or the chart needs a safe default that cannot live cleanly in `values.yaml`.
- Do not copy another service's unrelated environment block into the target service.
- Prefer ConfigMap auto-detection in the entrypoint for dynamic cluster config, then use project-specific `ENV` values only as explicit fallbacks.
- Keep `CMD` as a single install command that can be rerun idempotently.

## Entrypoint Pattern

Use an entrypoint when the install must read cluster state, create a user values file, adopt existing resources, or run Helm.

Start with:

```bash
#!/bin/bash
set -e

RELEASE_NAME=${RELEASE_NAME:-"<release>"}
RELEASE_NAMESPACE=${RELEASE_NAMESPACE:-"<namespace>"}
CHART_PATH=${CHART_PATH:-"./charts/<chart>"}
HELM_OPTS=${HELM_OPTS:-""}
HELM_OPTIONS=${HELM_OPTIONS:-""}
AUTO_CONFIG_HELM_OPTS=""
```

Use helpers:

```bash
get_cm_value() {
  local namespace="$1"
  local name="$2"
  local key="$3"
  kubectl get configmap "${name}" -n "${namespace}" -o "jsonpath={.data.${key}}" 2>/dev/null || true
}

add_set_string() {
  local key="$1"
  local value="$2"
  if [ -n "${value}" ]; then
    value=${value//\\/\\\\}
    value=${value//,/\\,}
    AUTO_CONFIG_HELM_OPTS="${AUTO_CONFIG_HELM_OPTS} --set-string ${key}=${value}"
  fi
}
```

Escape commas in `--set-string` values because Helm splits comma-separated `--set` payloads. This matters for allowlists such as `K8S_PROXY_ALLOWED_HOSTS` and origin lists.

For Sealos cloud config, read `sealos-system/sealos-config` first, then fall back to explicit environment values:

```bash
CONFIG_CLOUD_DOMAIN=$(get_cm_value sealos-system sealos-config cloudDomain)
CONFIG_CLOUD_PORT=$(get_cm_value sealos-system sealos-config cloudPort)
CONFIG_HTTP_PORT=$(get_cm_value sealos-system sealos-config httpPort)
CONFIG_DISABLE_HTTPS=$(get_cm_value sealos-system sealos-config disableHttps)
CONFIG_CERT_SECRET_NAME=$(get_cm_value sealos-system sealos-config certSecretName)

SEALOS_CLOUD_DOMAIN=${CONFIG_CLOUD_DOMAIN:-${SEALOS_CLOUD_DOMAIN:-${cloudDomain:-}}}
SEALOS_CLOUD_PORT=${CONFIG_CLOUD_PORT:-${SEALOS_CLOUD_PORT:-${cloudPort:-}}}
SEALOS_HTTP_PORT=${CONFIG_HTTP_PORT:-${SEALOS_HTTP_PORT:-${httpPort:-}}}
SEALOS_DISABLE_HTTPS=${CONFIG_DISABLE_HTTPS:-${SEALOS_DISABLE_HTTPS:-${disableHttps:-}}}
SEALOS_CERT_SECRET_NAME=${CONFIG_CERT_SECRET_NAME:-${SEALOS_CERT_SECRET_NAME:-${certSecretName:-}}}

add_set_string <config>.cloudDomain "${SEALOS_CLOUD_DOMAIN}"
add_set_string <config>.cloudPort "${SEALOS_CLOUD_PORT}"
add_set_string <config>.httpPort "${SEALOS_HTTP_PORT}"
add_set_string <config>.disableHttps "${SEALOS_DISABLE_HTTPS}"
add_set_string <config>.certSecretName "${SEALOS_CERT_SECRET_NAME}"
```

If the nearest existing deploy directory gives environment variables priority over ConfigMap values, match that local convention instead of mixing precedence models.

Copy user-editable values on first install:

```bash
SERVICE_NAME="<service>"
USER_VALUES_PATH="/root/.sealos/cloud/values/core/${SERVICE_NAME}-values.yaml"

if [ ! -f "${USER_VALUES_PATH}" ]; then
  mkdir -p "$(dirname "${USER_VALUES_PATH}")"
  cp "./charts/${SERVICE_NAME}/${SERVICE_NAME}-values.yaml" "${USER_VALUES_PATH}"
fi
```

Run Helm idempotently:

```bash
HELM_ARGS="${AUTO_CONFIG_HELM_OPTS} ${HELM_OPTIONS} ${HELM_OPTS}"

helm upgrade -i "${RELEASE_NAME}" -n "${RELEASE_NAMESPACE}" --create-namespace "${CHART_PATH}" \
  -f "./charts/${SERVICE_NAME}/values.yaml" \
  -f "${USER_VALUES_PATH}" \
  ${HELM_ARGS}
```

Use `set -euo pipefail` only when every optional environment variable expansion is guarded with `${name:-}`.

## Adoption Pattern

Add adoption when resources may already exist and Helm would fail with ownership conflicts:

```bash
adopt_namespaced_resource() {
  local namespace="$1"
  local kind="$2"
  local name="$3"
  if kubectl -n "${namespace}" get "${kind}" "${name}" >/dev/null 2>&1; then
    echo "Adopting ${kind} ${namespace}/${name}..."
    kubectl -n "${namespace}" label "${kind}" "${name}" app.kubernetes.io/managed-by=Helm --overwrite >/dev/null 2>&1 || true
    kubectl -n "${namespace}" annotate "${kind}" "${name}" meta.helm.sh/release-name="${RELEASE_NAME}" meta.helm.sh/release-namespace="${RELEASE_NAMESPACE}" --overwrite >/dev/null 2>&1 || true
  fi
}
```

Adopt the namespace, main `ConfigMap`, `Deployment`, `Service`, `Ingress`, and any `apps.app.sealos.io` App resource whose name is stable. Add a cluster-scoped helper only for cluster-scoped resources.

## Helm Chart Files

`Chart.yaml` should be minimal:

```yaml
apiVersion: v2
name: <chart>
description: Sealos <service> Helm Chart
type: application
version: 1.0.0
appVersion: "latest"
```

`values.yaml` should be complete enough for `helm template` without cluster access and during `sealos build` image scanning. Do not leave image tags empty behind a Helm `required` call unless the build command supplies values. For frontend providers, include:

```yaml
image: ghcr.io/labring/<runtime-image>:latest
imagePullPolicy: Always
imagePullSecrets: []
fullnameOverride: "<service>"
replicaCount: 1

service:
  type: ClusterIP
  port: 3000

resources:
  limits:
    cpu: 2000m
    memory: 2048Mi
  requests:
    cpu: 10m
    memory: 128Mi

ingress:
  className: nginx
  host: ""
  annotations: {}

<serviceConfig>:
  cloudDomain: "127.0.0.1.nip.io"
  cloudPort: ""
  httpPort: ""
  disableHttps: false
  certSecretName: "wildcard-cert"
```

`<service>-values.yaml` should contain only user-customizable overrides, commonly:

```yaml
replicaCount: 1

resources:
  limits:
    cpu: 2000m
    memory: 2048Mi
  requests:
    cpu: 10m
    memory: 128Mi
```

## Frontend Provider Templates

For frontend/provider services that appear in the Sealos desktop, create an `app.sealos.io/v1` `App` resource in `app-system`:

```yaml
apiVersion: app.sealos.io/v1
kind: App
metadata:
  name: <app-name>
  namespace: app-system
spec:
  data:
    desc: <description>
    url: {{ include "<chart>.url" . | quote }}
  icon: {{ printf "%s/logo.svg" (include "<chart>.url" .) | quote }}
  menuData:
  name: <display-name>
  type: iframe
  displayType: normal
```

Use helpers for names, labels, scheme, ports, host, and URL when the chart has ingress/domain logic. Keep selector labels compatible with existing manifests if upgrading an existing component. If a repository already has standalone `deploy/manifests/*.tmpl` App resources, convert or duplicate the needed resources into `charts/<chart>/templates/` for cluster image installs; a Helm-only entrypoint will not apply loose `.tmpl` files.

Ingress templates should:

- Use `.Values.ingress.className` for both annotation compatibility and `spec.ingressClassName` when local convention does this.
- Derive the host from `.Values.ingress.host` or `<app>.<cloudDomain>`.
- Add TLS only when `disableHttps` is not `"true"`.
- Put extra user annotations under `.Values.ingress.annotations`.

ConfigMap templates should render the app's runtime config from values instead of shelling out in the container at runtime.

Deployment templates should:

- Use `.Values.image` and `.Values.imagePullPolicy`.
- Mount generated config from ConfigMap when the app expects config files.
- Include non-root security context unless the app requires otherwise.
- Keep resources configurable through `.Values.resources`.

## Checks Before Finishing

Run what is available in the repo and report unavailable tools:

```bash
bash -n deploy/<service>-entrypoint.sh
helm lint deploy/charts/<chart>
helm template <release> deploy/charts/<chart> -n <namespace> >/tmp/<release>.yaml
```

For build-level verification, use the repository's documented command or:

```bash
sealos build -t <image> deploy
```

Do not run cluster-mutating install commands such as the entrypoint itself unless the user explicitly asks for live-cluster verification.

## Common Pitfalls

- Missing `-f "${USER_VALUES_PATH}"`, which prevents persistent user overrides.
- Using `--set` instead of `--set-string` for ports, domains, booleans-as-strings, tokens, and URLs.
- Committing real production config as default values.
- Letting `SERVICE_NAME`, chart folder name, `fullnameOverride`, and adoption resource names drift apart.
- Using `set -u` with unguarded lowercase env expansions like `${cloudDomain}`.
- Adding an `images/shim/images` entry that does not match the runtime image or dependency actually pulled by the chart.
- Forgetting the App resource for frontend providers that should appear in the Sealos desktop.
