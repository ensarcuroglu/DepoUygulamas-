$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$image = "hadolint/hadolint:v2.14.0"
$dockerfiles = @(
    "/repo/infra/docker/python-service.Dockerfile",
    "/repo/infra/docker/frontend-dev.Dockerfile"
)

docker run --rm `
    -v "${repoRoot}:/repo:ro" `
    -w /repo `
    $image `
    hadolint @dockerfiles
