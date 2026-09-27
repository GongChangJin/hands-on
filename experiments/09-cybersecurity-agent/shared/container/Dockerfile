FROM python:3.11-slim

ARG SEMGREP_VERSION=1.178.0
ARG BANDIT_VERSION=1.9.4
ARG PYTEST_VERSION=9.1.1

RUN python -m pip install --no-cache-dir \
    "semgrep==${SEMGREP_VERSION}" \
    "bandit==${BANDIT_VERSION}" \
    "pytest==${PYTEST_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTEST_ADDOPTS="-p no:cacheprovider" \
    SEMGREP_SEND_METRICS=off

WORKDIR /workspace
COPY rules/semgrep.yml /rules/semgrep.yml
CMD ["python", "--version"]
