import copy
from collections.abc import Mapping, Sequence

from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.permissions import (
    EDITOR_PERMISSIONS,
    PermissionResult,
    Permissions,
    _get_disabled_reason,
    get_user_permissions,
)
from dagster._core.workspace.workspace import CodeLocationEntry, CodeLocationStatusEntry


class SfAuthWorkspaceProcessContext(WorkspaceProcessContext):
    def create_request_context(self, source: object | None = None) -> WorkspaceRequestContext:
        return SfAuthWorkspaceRequestContext(
            instance=self._instance,
            current_workspace=self.get_current_workspace(),
            process_context=self,
            version=self.version,
            source=source,
            read_only=self._read_only,
        )


class SfAuthWorkspaceRequestContext(WorkspaceRequestContext):
    @property
    def user(self) -> str | None:
        """Reads the user email from the X-Email header set by the nginx ingress oauth2-proxy integration."""
        if self.source is None:
            return None

        email = self.source.headers.get("x-email")  # type: ignore[union-attr]
        if not email:
            return None

        return email.split("@")[0]

    def get_viewer_tags(self) -> dict[str, str]:
        return {"user": self.user} if self.user else {}
