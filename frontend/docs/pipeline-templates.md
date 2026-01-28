# Pipeline Templates — The Standard Patterns

All workflows MUST adhere to these templates to ensure consistency and "AI-readability."

## 1. Standard Service Deployment
```yaml
name: Deploy [Service Name]

on:
  push:
    branches: [ main ]
    paths:
      - '[service_dir]/**'

env:
  SERVICE: [service_name]
  REGISTRY: ghcr.io

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install Deps
        run: pip install -r [service_dir]/requirements.txt
      - name: Lint
        run: ruff check [service_dir]
      - name: Test
        run: pytest [service_dir]
      - name: Security Audit
        run: pip-audit -r [service_dir]/requirements.txt

  build-and-push:
    needs: quality-gate
    runs-on: ubuntu-latest
    steps:
      - uses: docker/login-action@v2
        # ... login details ...
      - uses: docker/build-push-action@v4
        with:
          context: ./[service_dir]
          push: true
          tags: ...

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    steps:
      - uses: appleboy/ssh-action@master
        with:
          script: |
            cd /srv/[service_dir]
            docker compose pull
            docker compose up -d
```

## 2. The Guardian Job
Every workflow must include a `guardian-check` or be monitored by the global `ci-guardian.yml`.

## 3. Epistemological Logging
Steps should be named clearly to allow the AI to parse logs:
*   GOOD: `name: Check for CVE-2024-1234`
*   BAD: `name: check stuff`
