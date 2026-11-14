# Pass the exact Debian-based builder image digest selected for the execution host.
ARG BUILD_IMAGE
FROM ${BUILD_IMAGE} AS builder
ARG BUILD_IMAGE
RUN echo "$BUILD_IMAGE" | grep -Eq '@sha256:[0-9a-f]{64}$'
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3 git ca-certificates curl zstd libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev libffi-dev liblzma-dev uuid-dev \
    && rm -rf /var/lib/apt/lists/*
COPY backend/runtimes /recipes
RUN bash /recipes/build_packages.sh && dpkg-query -W > /export/BUILD_APT_PACKAGES

FROM scratch AS packages
COPY --from=builder /export /
