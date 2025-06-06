import pytest
import responses
from dagster import AssetSpec, EnvVar
from dagster._core.definitions.tags import has_kind
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.test_utils import environ
from dagster_airbyte import (
    AirbyteCloudWorkspace,
    airbyte_assets,
    build_airbyte_assets_definitions,
    load_airbyte_cloud_asset_specs,
)
from dagster_airbyte.translator import (
    AirbyteConnectionTableProps,
    AirbyteMetadataSet,
    DagsterAirbyteTranslator,
)

from dagster_airbyte_tests.beta.conftest import (
    TEST_ANOTHER_WORKSPACE_ID,
    TEST_CLIENT_ID,
    TEST_CLIENT_SECRET,
    TEST_CONNECTION_ID,
    TEST_DESTINATION_TYPE,
    TEST_WORKSPACE_ID,
)


def test_fetch_airbyte_workspace_data(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    resource = AirbyteCloudWorkspace(
        workspace_id=TEST_WORKSPACE_ID,
        client_id=TEST_CLIENT_ID,
        client_secret=TEST_CLIENT_SECRET,
    )

    actual_workspace_data = resource.fetch_airbyte_workspace_data()
    assert len(actual_workspace_data.connections_by_id) == 1
    assert len(actual_workspace_data.destinations_by_id) == 1


def test_translator_spec(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        resource = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        all_assets = load_airbyte_cloud_asset_specs(resource)
        all_assets_keys = [asset.key for asset in all_assets]

        # 1 table for the connection
        assert len(all_assets) == 2
        assert len(all_assets_keys) == 2

        # Test the asset key for the connection table
        the_asset_key = next(iter(all_assets_keys))
        assert the_asset_key.path == ["test_prefix_test_stream"]

        first_asset_metadata = next(asset.metadata for asset in all_assets)
        assert AirbyteMetadataSet.extract(first_asset_metadata).connection_id == TEST_CONNECTION_ID


def test_connection_selector(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        # Test with no selector (should include all connections)
        all_assets = load_airbyte_cloud_asset_specs(workspace=workspace)
        assert len(all_assets) == 2  # Based on the mock data

        # Test with selector that matches the connection
        matching_assets = load_airbyte_cloud_asset_specs(
            workspace=workspace,
            connection_selector_fn=lambda connection: connection.name == "Postgres To Snowflake",
        )
        assert len(matching_assets) == 2  # Should still get all assets from the matching connection

        # Test with selector that doesn't match any connections
        no_matching_assets = load_airbyte_cloud_asset_specs(
            workspace=workspace,
            connection_selector_fn=lambda connection: connection.name == "non_existent_connection",
        )
        assert len(no_matching_assets) == 0  # Should get no assets


def test_cached_load_spec_single_resource(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        # load asset specs, calls are made
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs another time, no additional calls are made
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4


def test_cached_load_spec_multiple_resources(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        another_workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_ANOTHER_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        # load asset specs with a resource
        workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4

        # load asset specs with another resource,
        # additional calls are made to load its specs
        another_workspace.load_asset_specs()
        assert len(fetch_workspace_data_api_mocks.calls) == 4 + 4


def test_cached_load_spec_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        # build_airbyte_assets_definitions calls workspace.load_asset_specs to get the connection IDs,
        # then workspace.load_asset_specs is called once per connection ID in airbyte_assets,
        # but the four calls to the API are only made once.
        build_airbyte_assets_definitions(workspace=workspace)
        assert len(fetch_workspace_data_api_mocks.calls) == 4


class MyCustomTranslator(DagsterAirbyteTranslator):
    def get_asset_spec(self, data: AirbyteConnectionTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(
            key=default_spec.key.with_prefix("test_connection"),
        ).merge_attributes(metadata={"custom": "metadata"})


def test_translator_custom_metadata(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )
        all_asset_specs = workspace.load_asset_specs(
            dagster_airbyte_translator=MyCustomTranslator()
        )
        asset_spec = next(spec for spec in all_asset_specs)

        assert "custom" in asset_spec.metadata
        assert asset_spec.metadata["custom"] == "metadata"
        assert asset_spec.key.path == ["test_connection", "test_prefix_test_stream"]
        assert has_kind(asset_spec.tags, "airbyte")
        assert has_kind(asset_spec.tags, TEST_DESTINATION_TYPE)


class MyCustomTranslatorWithGroupName(DagsterAirbyteTranslator):
    def get_asset_spec(self, data: AirbyteConnectionTableProps) -> AssetSpec:  # pyright: ignore[reportIncompatibleMethodOverride]
        default_spec = super().get_asset_spec(data)
        return default_spec.replace_attributes(group_name="my_group_name")


def test_translator_custom_group_name_with_asset_factory(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        my_airbyte_assets = build_airbyte_assets_definitions(
            workspace=workspace, dagster_airbyte_translator=MyCustomTranslatorWithGroupName()
        )

        first_assets_def = next(assets_def for assets_def in my_airbyte_assets)
        first_asset_spec = next(asset_spec for asset_spec in first_assets_def.specs)
        assert first_asset_spec.group_name == "my_group_name"


def test_translator_invariant_group_name_with_asset_decorator(
    fetch_workspace_data_api_mocks: responses.RequestsMock,
) -> None:
    with environ(
        {"AIRBYTE_CLIENT_ID": TEST_CLIENT_ID, "AIRBYTE_CLIENT_SECRET": TEST_CLIENT_SECRET}
    ):
        workspace = AirbyteCloudWorkspace(
            workspace_id=TEST_WORKSPACE_ID,
            client_id=EnvVar("AIRBYTE_CLIENT_ID"),
            client_secret=EnvVar("AIRBYTE_CLIENT_SECRET"),
        )

        with pytest.raises(
            DagsterInvariantViolationError,
            match="Cannot set group_name parameter on airbyte_assets",
        ):

            @airbyte_assets(
                connection_id=TEST_CONNECTION_ID,
                workspace=workspace,
                group_name="my_asset_decorator_group_name",
                dagster_airbyte_translator=MyCustomTranslatorWithGroupName(),
            )
            def my_airbyte_assets(): ...
