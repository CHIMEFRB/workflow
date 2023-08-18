#!/bin/sh

# Send echo to stderr
echoerr() { echo "$@" 1>&2; }

# Start tmate session
tmate -S /tmp/tmate.sock new-session -d

# Wait for session to be ready
tmate -S /tmp/tmate.sock wait tmate-ready

# Print connection info
SSH_CMD=$(tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}')
echo "SSH Command: $SSH_CMD"

# Wait for session to end
tmate -S /tmp/tmate.sock wait tmate-exit
