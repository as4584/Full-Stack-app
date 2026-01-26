# LexMakesIt Infrastructure

This repository contains the global infrastructure configurations for `lexmakesit.com`.

## Directory Structure

- `caddy/`: Global Caddyfile and security headers.
- `monitoring/`: Docker Compose for Loki, Promtail, and Grafana.
- `security/`: Security scripts (scanner, fail2ban).
- `scripts/`: Operational scripts (backup, prune, network init).
- `env/`: Environment variable templates.
- `iac/`: Infrastructure as Code (Terraform/Ansible) - *Future*.

## Getting Started

1.  **Initialize Network**:
    ```bash
    ./scripts/init_network.sh
    ```

2.  **Start Monitoring**:
    ```bash
    cd monitoring
    docker compose up -d
    ```

3.  **Deploy Caddy**:
    (Refer to Caddy deployment instructions in `caddy/README.md` - *To be created*)

## Security

- **Scanner**: Run `./security/scanner.sh` to audit dependencies.
- **Fail2Ban**: Configuration in `security/fail2ban.conf`.

## Operations

- **Backup**: `./scripts/backup.sh` (Run nightly via cron).
- **Prune**: `./scripts/prune.sh` (Run weekly via cron).
