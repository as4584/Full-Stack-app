# Server Hardening Guide

## 1. SSH Hardening
Edit `/etc/ssh/sshd_config`:

```bash
# Disable root login
PermitRootLogin no

# Disable password authentication
PasswordAuthentication no
ChallengeResponseAuthentication no

# Use SSH keys only
PubkeyAuthentication yes
```

Restart SSH: `sudo systemctl restart sshd`

## 2. Firewall (UFW)
Enforce default deny policy:

```bash
# Reset to default
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow essential ports
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Enable firewall
sudo ufw enable
```

## 3. Fail2Ban
Install and configure:

```bash
sudo apt install fail2ban
sudo cp security/fail2ban.conf /etc/fail2ban/jail.d/custom.conf
sudo systemctl restart fail2ban
```

## 4. Automatic Updates
Enable unattended upgrades:

```bash
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```
