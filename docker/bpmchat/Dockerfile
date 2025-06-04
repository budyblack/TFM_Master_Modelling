FROM python:3.12-slim

ARG BPM_GID
ARG BPM_UID

# Install required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Create user and group
RUN groupadd -g $BPM_GID -o chat && \
    useradd -m -u $BPM_UID -g $BPM_GID -o -s /bin/bash chat

# Set up cron log
RUN touch /var/log/cron.log && \
    chown chat:chat /var/log/cron.log

# Set working directory
WORKDIR /home/chat/MinkaAnalyst

# Expose the required port
EXPOSE 8080

# Run as root to start cron and switch to chat user
CMD sh -c "\
  cron && \
  su - chat -c 'cd /home/chat/MinkaAnalyst && ./bin/start-services.sh' & \
  tail -f /var/log/cron.log"
