import copy
from collections.abc import Mapping
from functools import cached_property

from dagster._core.workspace.context import WorkspaceProcessContext, WorkspaceRequestContext
from dagster._core.workspace.permissions import (
    EDITOR_PERMISSIONS,
    PermissionResult,
    Permissions,
    _get_disabled_reason,
    get_user_permissions,
)
from starlette.requests import HTTPConnection


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
    @cached_property
    def user(self) -> str | None:
        """Reads the username from the X-Email header set by the nginx ingress oauth2-proxy integration."""
        if self.source is None:
            return None
        conn = self.source
        assert isinstance(conn, HTTPConnection)
        email = conn.headers.get("x-email")
        return email.split("@")[0] if email else None

    def get_viewer_tags(self) -> dict[str, str]:
        """Returns tags automatically applied to every run and backfill launched by this user.
        The "user" tag is picked up by the Dagster UI to display the run author.
        Called from launch_execution.py and backfill.py before submitting the run.
        """
        return {"user": self.user} if self.user else {}

    # Permission RBAC — three levels of granularity:
    #
    # 1. Global          → has_permission(permission)
    # 2. Per location    → has_permission_for_location(permission, location_name)
    #                      Only LOCATION_SCOPED_PERMISSIONS (14 of 17) support this level.
    # 3. Per definition  → has_permission_for_selector() — stub in OSS, fully implemented in Dagster+
    #
    # IMPORTANT: Both has_permission_for_selector() (non-asset jobs, sensors, schedules) and
    # has_permission_for_asset_graph() (asset jobs) check has_permission() globally first and
    # short-circuit if it returns True. The global permissions property must therefore return
    # read_only=True so that per-location checks are actually reached.
    #
    # Permission check call sites:
    #
    # Via has_permission_for_selector (global check short-circuits):
    #   - Job launch/re-execution  launch_execution.py:113 → assert_permission_for_run
    #   - Sensor start/stop        fetch_sensors.py:124    → assert_permission_for_sensor
    #   - Schedule start/stop      fetch_schedules.py:71   → assert_permission_for_schedule
    #
    # Via has_permission_for_location (location check works directly):
    #   - Dynamic partitions       dynamic_partitions.py:71,111
    #   - Backfill (partition set) backfill.py:157
    #
    # Via has_permission_for_asset_graph (global check short-circuits):
    #   - Asset job launch         backfill.py:251,291
    #   - Delete run               __init__.py:202 → assert_permission_for_run
    #
    # Global-only assert_permission (location is never checked):
    #   - Schedule reload          fetch_schedules.py:75
    #   - Sensor cursor reset      fetch_sensors.py:130
    #   - Delete run (no selector) __init__.py:199

    @property
    def permissions(self) -> Mapping[str, PermissionResult]:
        # Always return read_only=True globally so that per-location checks in
        # has_permission_for_selector() and has_permission_for_asset_graph() are reached.
        # Special users are fully read-only; regular users get editor access per location.
        return get_user_permissions(read_only=True)

    @staticmethod
    def _to_permission_result_map(
        permissions: Mapping[str, bool],
    ) -> dict[str, PermissionResult]:
        return {
            perm: PermissionResult(enabled=enabled, disabled_reason=_get_disabled_reason(enabled))
            for perm, enabled in permissions.items()
        }

    @property
    def restricted_users(self) -> set[str]:
        return {"hynek.blaha", "tomas.hegr"}

    def permissions_for_location(self, *, location_name: str) -> dict[str, PermissionResult]:
        # Special users have restricted permissions on certain locations.
        # All other users get full editor access on all locations.
        permissions = copy.copy(EDITOR_PERMISSIONS)
        if self.user in self.restricted_users:
            if location_name == "market-data-backtest":
                permissions[Permissions.LAUNCH_PIPELINE_EXECUTION] = False
                permissions[Permissions.LAUNCH_PIPELINE_REEXECUTION] = False
                permissions[Permissions.TERMINATE_PIPELINE_EXECUTION] = False
                permissions[Permissions.DELETE_PIPELINE_RUN] = False
            elif location_name == "market-data-ingest":
                permissions[Permissions.START_SCHEDULE] = False
                permissions[Permissions.STOP_RUNNING_SCHEDULE] = False
                permissions[Permissions.EDIT_SENSOR] = False
                permissions[Permissions.UPDATE_SENSOR_CURSOR] = False
                permissions[Permissions.TOGGLE_AUTO_MATERIALIZE] = False
            elif location_name == "market-data-processing":
                permissions[Permissions.LAUNCH_PARTITION_BACKFILL] = False
                permissions[Permissions.CANCEL_PARTITION_BACKFILL] = False
        return self._to_permission_result_map(permissions)
