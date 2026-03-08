# SF Dagster Webserver

A thin overlay on top of the OSS `dagster-webserver` that integrates with the Second Foundation
nginx oauth2-proxy setup to tag runs and backfills with the authenticated user.

## How it works

- `SfAuthWorkspaceProcessContext` creates `SfAuthWorkspaceRequestContext` for each request.
- `SfAuthWorkspaceRequestContext` overrides `get_viewer_tags()` to read the `X-Email` header
  forwarded by nginx and inject the username (part before `@`) as a `user` tag on every run and backfill.

## Building and pushing the image

```bash
./sf/build_and_push.sh <IMAGE> (<DAGSTER_VERSION>)
```
