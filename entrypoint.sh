#!/usr/bin/env bash

# Look for the environment variable named WORKFLOW_WORKSPACE
if [ -z "$WORKFLOW_WORKSPACE" ]; then
    echo "WORKFLOW_WORKSPACE not set, skipping workspace set"
fi

# If WORKFLOW_WORKSPACE is set, set the workflow workspace
if [ -n "$WORKFLOW_WORKSPACE" ]; then
    echo "Setting workspace to $WORKFLOW_WORKSPACE"
    workflow workspace set $WORKFLOW_WORKSPACE
    # Check if the workspace was set successfully
    if [ $? -ne 0 ]; then
        echo "Failed to set workspace to $WORKFLOW_WORKSPACE. Exiting."
        exit 1
    fi
fi
exec "$@"
