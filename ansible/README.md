# NetMonitor Ansible Deployment

This folder contains a production-ready Ansible playbook for deploying the full NetMonitor observability stack.

## Features
- Installs and configures Docker
- Deploys InfluxDB and Grafana as robust Docker containers
- Deploys the NetMonitor backend and frontend as Docker containers (recommended for production)
- Uses persistent Docker volumes for data
- All configuration is via variables in `group_vars/all.yml`
- Sensitive secrets (e.g., INFLUX_TOKEN) should be managed with Ansible Vault

## Usage
1. **Edit `inventory.ini`** to set your target host(s).
2. **Edit `group_vars/all.yml`** for your environment and secrets.
3. **Encrypt secrets** with `ansible-vault` (see below).
4. **Run the playbook:**
   ```sh
   ansible-playbook -i inventory.ini playbook.yml
   ```

## Security
- Never commit secrets in plain text. Use `ansible-vault` for `influx_token` and other sensitive values.
- Example to encrypt:
  ```sh
  ansible-vault encrypt group_vars/all.yml
  ```

## Structure
- `roles/docker` — Docker installation
- `roles/influxdb` — InfluxDB container
- `roles/grafana` — Grafana container
- `roles/backend` — NetMonitor backend (Dockerized)
- `roles/frontend` — NetMonitor frontend (Dockerized)

---
This playbook is designed for clarity, maintainability, and real-world deployment. See each role for details.
