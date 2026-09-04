# Docker Buildx bake — cross-platform hardened images + push.
#
# Usage:
#   REGISTRY=ghcr.io/nato1000 docker buildx bake -f docker/docker-bake.hcl
#   REGISTRY=ghcr.io/nato1000 docker buildx bake -f docker/docker-bake.hcl push
#
# REGISTRY is supplied via the environment — never hardcode a registry,
# username, or token in this file.

variable "REGISTRY" {
  default = "localhost/aicodex"
}

variable "TAG" {
  default = "latest"
}

# Common settings applied to every image (hardening metadata).
function "img" {
  params = [name]
  result = {
    context    = "."
    dockerfile = "Dockerfile"
    tags       = ["${REGISTRY}/aicodex-${name}:${TAG}"]
    labels = {
      "org.opencontainers.image.title"       = "AicodeX (${name})"
      "org.opencontainers.image.source"      = "https://github.com/NaTo1000/AicodeX"
      "org.opencontainers.image.licenses"    = "SEE LICENSE"
      "aicodex.hardened"                     = "true"
      "aicodex.platform"                     = name
    }
  }
}

group "default" {
  targets = ["linux", "windows", "android"]
}

# Linux — the primary runtime target.
target "linux" {
  inherits  = []
  context   = "."
  dockerfile = "Dockerfile"
  platforms = ["linux/amd64", "linux/arm64"]
  tags      = ["${REGISTRY}/aicodex-linux:${TAG}"]
  labels    = img("linux").labels
}

# Windows container image.
target "windows" {
  context    = "."
  dockerfile = "Dockerfile"
  platforms  = ["windows/amd64"]
  tags       = ["${REGISTRY}/aicodex-windows:${TAG}"]
  labels     = img("windows").labels
}

# Android runs the Linux userland image (e.g. via Termux/proot); it reuses the
# ARM64 Linux build. A dedicated target keeps the tag/registry wiring explicit.
target "android" {
  context    = "."
  dockerfile = "Dockerfile"
  platforms  = ["linux/arm64"]
  tags       = ["${REGISTRY}/aicodex-android:${TAG}"]
  labels     = img("android").labels
}

# Push all platform images. Requires `docker login` to REGISTRY first.
group "push" {
  targets = ["linux", "windows", "android"]
}
