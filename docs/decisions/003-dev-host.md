# 003 — Development host

Status: draft
Task: T-02

## Context

MacBook (~/NGSpipeline) vs desktop WSL2 (48 GB, Tailscale SSH).

MacBook measured 2026-09-15 (T-00): Apple M5 Pro, 24 GB RAM, arm64, 667 GB free disk. Docker Desktop not installed. Nextflow 26.04.6, nf-core 4.1.0, nf-test 0.9.5, OpenJDK 26 installed via Homebrew/uv.
Note for 002: 24 GB is below the ~32 GB STAR human-index requirement, so STAR index build is not possible on the MacBook.
Decision rule: if amd64 container emulation on MacBook cannot meet the 5-min test-profile limit, develop on WSL2; MacBook edits/commits only.

## Options

## Choice

## Consequences
