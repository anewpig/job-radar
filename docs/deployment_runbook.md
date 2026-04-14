# Job Radar Deployment Runbook

## Deployment Strategy

This repository now assumes three deployment environments:

- `local`: developer machine, Streamlit-first, single-user diagnostics.
- `docker`: multi-process local or VM deployment via `docker-compose`.
- `render`: managed web deployment with externalized secrets and persistent runtime metadata.

Set these environment variables per environment:

- `JOB_RADAR_DEPLOY_ENV`
- `JOB_RADAR_RELEASE_CHANNEL`
- `JOB_RADAR_GIT_SHA`
- `JOB_SPY_LOG_FORMAT`

## Process Topology

Recommended production-like topology:

- `web`: Streamlit UI and read-heavy product interactions
- `worker`: crawl queue consumer
- `scheduler`: due saved-search scanner
- `maintenance`: periodic cleanup / backup / runtime hygiene

Current container entrypoints already exist:

- `scripts/start_streamlit.sh`
- `scripts/start_crawl_worker.sh`
- `scripts/start_crawl_scheduler.sh`

## Required Health Checks

Run these checks before and after deployment:

```bash
source .venv/bin/activate
python -m job_spy_tw.backend_status --base-dir . --strict
```

Signals to confirm:

- scheduler heartbeat is fresh
- worker heartbeat is fresh
- failed job count is zero
- latest sqlite backup exists
- AI latency budget status is not `FAIL`

## Rollout Checklist

1. Update environment variables and secrets.
2. Run focused unit tests and compile checks.
3. Build package artifact.
4. Deploy web.
5. Deploy worker and scheduler.
6. Run backend status strict check.
7. Verify AI latency and cache-efficiency summaries in backend console.

## Rollback Checklist

1. Revert to previous image or Git tag.
2. Restore previous environment variable set if the failure is config-driven.
3. If schema or runtime corruption is suspected, restore from latest SQLite backup.
4. Re-run backend status strict check.

## Monitoring Targets

Track at minimum:

- crawl queue depth
- failed / leased runtime jobs
- scheduler and worker heartbeat freshness
- AI event latency budgets
- AI token budgets
- cache size and cleanup success
- recent auth / audit events for privileged actions

## Security Controls

Current baseline controls:

- role-aware backend console gating
- audit log table for auth and privileged flows
- environment-based secret injection
- hashed password and reset-token storage

Still recommended for future hardening:

- external secret manager
- MFA or SSO-only admin policy
- encrypted database volume or host-level disk encryption
- off-box log shipping
