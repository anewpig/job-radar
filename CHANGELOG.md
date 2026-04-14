# Changelog

All notable changes to this project should be recorded in this file.

The format is based on Keep a Changelog, adapted for this repository's release discipline.

## [Unreleased]

### Added
- Explicit schema version registry for product state, runtime queue, auth, audit, prompt registry, market snapshot, assistant response, and resume profile.
- Role-aware backend console gating, audit log repository, and `job-radar-user-admin` management CLI.
- Structured AI monitoring metadata for trace IDs, cache efficiency, retrieval policy versions, and prompt versions.
- Build metadata in backend status reporting, plus deployment and release workflow scaffolding.

### Changed
- Assistant and resume monitoring events now carry richer cost/latency metadata for benchmark and runtime reporting.
- Logging now supports JSON output and per-request trace correlation.

## Release Discipline

- Update `Unreleased` on every user-visible or operational change.
- Promote entries to a dated release section when publishing tags.
- Keep schema, prompt, and deployment changes in this changelog even when there is no UI delta.
