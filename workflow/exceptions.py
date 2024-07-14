"""Exceptions and warnings for workflow."""


class WorkflowException(Exception):
    """Ambigous workflow exception."""


class WorkspaceError(WorkflowException):
    """Invalid workflow workspace."""


class HTTPContextError(WorkflowException):
    """Invalid HTTP context."""


# Workflow Warnings


class WorkflowWarning(Warning):
    """Base warning for workflow."""


class WorkWarning(WorkflowWarning):
    """Base warning for work."""
