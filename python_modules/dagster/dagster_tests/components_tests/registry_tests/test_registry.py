import os
import re
import subprocess
import tempfile
import textwrap
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Optional

import pytest
from dagster import Component
from dagster._core.test_utils import ensure_dagster_tests_import
from dagster._utils import pushd
from dagster.components.core.package_entry import discover_entry_point_package_objects
from dagster.components.core.snapshot import get_package_entry_snap
from dagster_dg_core.utils import get_venv_executable
from dagster_shared.error import SerializableErrorInfo
from dagster_shared.serdes.objects import PluginObjectKey
from dagster_shared.serdes.objects.package_entry import PluginManifest
from dagster_shared.serdes.serdes import deserialize_value

ensure_dagster_tests_import()

from dagster_tests.components_tests.utils import modify_toml, set_toml_value


@contextmanager
def _temp_venv(install_args: Sequence[str]) -> Iterator[Path]:
    # Create venv
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_dir = Path(tmpdir) / ".venv"
        subprocess.check_call(["uv", "venv", str(venv_dir)])
        subprocess.check_call(
            [
                "uv",
                "pip",
                "install",
                "--python",
                str(get_venv_executable(venv_dir, "python")),
                *install_args,
            ]
        )
        yield venv_dir


def _get_component_print_script_result(venv_root: Path) -> subprocess.CompletedProcess:
    assert venv_root.exists()
    dagster_components_path = get_venv_executable(venv_root, "dagster-components")
    assert dagster_components_path.exists()
    result = subprocess.run(
        [str(dagster_components_path), "list", "plugins"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result


def _get_component_types_in_python_environment(venv_root: Path) -> Sequence[str]:
    result = _get_component_print_script_result(venv_root)
    return [
        obj.key.to_typename() for obj in deserialize_value(result.stdout, PluginManifest).objects
    ]


def _find_repo_root():
    current = Path(__file__).parent
    while not (current / ".git").exists():
        if current == Path("/"):
            raise Exception("Could not find the repository root.")
        current = current.parent
    return current


def _generate_test_component_source(number: int) -> str:
    return textwrap.dedent(f"""
    from dagster import Component

    class TestComponent{number}(Component):
        def build_defs(self, context):
            pass
    """)


_repo_root = _find_repo_root()


def _get_editable_package_root(pkg_name: str) -> str:
    possible_locations = [
        _repo_root / "python_modules" / pkg_name,
        _repo_root / "python_modules" / "libraries" / pkg_name,
    ]
    return next(str(loc) for loc in possible_locations if loc.exists())


# ########################
# ##### TESTS
# ########################


def test_components_from_dagster():
    common_deps: list[str] = []
    for pkg_name in ["dagster", "dagster-pipes", "dagster-shared"]:
        common_deps.extend(["-e", _get_editable_package_root(pkg_name)])

    dbt_root = _get_editable_package_root("dagster-dbt")
    sling_root = _get_editable_package_root("dagster-sling")

    # No extras
    with _temp_venv(
        [
            *common_deps,
        ]
    ) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster.PipesSubprocessScriptCollectionComponent" in component_types
        assert "dagster_dbt.DbtProjectComponent" not in component_types
        assert "dagster_sling.SlingReplicationCollectionComponent" not in component_types

    with _temp_venv([*common_deps, "-e", dbt_root]) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster.PipesSubprocessScriptCollectionComponent" in component_types
        assert "dagster_dbt.DbtProjectComponent" in component_types
        assert "dagster_sling.SlingReplicationCollectionComponent" not in component_types

    with _temp_venv([*common_deps, "-e", sling_root]) as python_executable:
        component_types = _get_component_types_in_python_environment(python_executable)
        assert "dagster.PipesSubprocessScriptCollectionComponent" in component_types
        assert "dagster_dbt.DbtProjectComponent" not in component_types
        assert "dagster_sling.SlingReplicationCollectionComponent" in component_types


def test_all_components_have_defined_summary():
    registry = discover_entry_point_package_objects()
    for component_name, component_type in registry.items():
        if isinstance(component_type, type) and issubclass(component_type, Component):
            assert get_package_entry_snap(PluginObjectKey("a", "a"), component_type).summary, (
                f"Component {component_name} has no summary defined"
            )


# Our pyproject.toml installs local dagster components
DAGSTER_FOO_PYPROJECT_TOML = """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dagster-foo"
version = "0.1.0"
description = "A simple example package"
authors = [
    { name = "Your Name", email = "your.email@example.com" }
]
dependencies = [
    "dagster",
]

[project.entry-points]
"<ENTRY_POINT_GROUP>" = { dagster_foo = "dagster_foo.lib"}
"""

DAGSTER_FOO_LIB_ROOT = f"""
{_generate_test_component_source(1)}

from dagster_foo.lib.sub import TestComponent2
"""


@contextmanager
def isolated_venv_with_component_lib_dagster_foo(
    entry_point_group: str,
    pre_install_hook: Optional[Callable[[], None]] = None,
):
    with tempfile.TemporaryDirectory() as tmpdir:
        with pushd(tmpdir):
            # Create test package that defines some components
            os.makedirs("dagster-foo")

            pyproject_toml_content = re.sub(
                r"<ENTRY_POINT_GROUP>", entry_point_group, DAGSTER_FOO_PYPROJECT_TOML
            )

            with open("dagster-foo/pyproject.toml", "w") as f:
                f.write(pyproject_toml_content)

            os.makedirs("dagster-foo/dagster_foo/lib/sub")

            with open("dagster-foo/dagster_foo/lib/__init__.py", "w") as f:
                f.write(DAGSTER_FOO_LIB_ROOT)

            with open("dagster-foo/dagster_foo/lib/sub/__init__.py", "w") as f:
                f.write(_generate_test_component_source(2))

            if pre_install_hook:
                pre_install_hook()

            # Need pipes because dependency of dagster
            deps = [
                "-e",
                _get_editable_package_root("dagster"),
                "-e",
                _get_editable_package_root("dagster-pipes"),
                "-e",
                _get_editable_package_root("dagster-shared"),
                "-e",
                "dagster-foo",
            ]

            with _temp_venv(deps) as venv_root:
                yield venv_root


@pytest.mark.parametrize(
    "entry_point_group", ["dagster_dg_cli.plugin", "dagster_dg.plugin", "dagster_dg.library"]
)
def test_components_from_third_party_lib(entry_point_group: str):
    with isolated_venv_with_component_lib_dagster_foo(entry_point_group) as venv_root:
        component_types = _get_component_types_in_python_environment(venv_root)
        assert "dagster_foo.lib.TestComponent1" in component_types
        assert "dagster_foo.lib.TestComponent2" in component_types


@pytest.mark.parametrize(
    "entry_point_group", ["dagster_dg_cli.plugin", "dagster_dg.plugin", "dagster_dg.library"]
)
def test_bad_entry_point_error_message(entry_point_group: str):
    # Modify the entry point to point to a non-existent module. This has to be done before the
    # package is installed, which is why we use a pre-install hook.
    def pre_install_hook():
        with modify_toml(Path("dagster-foo/pyproject.toml")) as toml:
            set_toml_value(
                toml,
                ("project", "entry-points", entry_point_group, "dagster_foo"),
                "fake.module",
            )

    with isolated_venv_with_component_lib_dagster_foo(
        entry_point_group, pre_install_hook=pre_install_hook
    ) as venv_root:
        result = _get_component_print_script_result(venv_root)
        error = deserialize_value(result.stdout, SerializableErrorInfo)
        assert (
            f"Error loading entry point `fake.module` in group `{entry_point_group}`"
            in error.message
        )
        assert result.returncode == 0
