import os

import numpy as np
import pandas as pd

import dagster as dg

from .asset_input_managers import (
    load_numpy_array,
    load_pandas_dataframe,
    store_pandas_dataframe,
)

# start_numpy_example


class PandasAssetIOManager(dg.ConfigurableIOManager):
    def handle_output(self, context: dg.OutputContext, obj):
        file_path = self._get_path(context)
        store_pandas_dataframe(name=file_path, table=obj)

    def _get_path(self, context):
        return os.path.join(
            "storage",
            f"{context.asset_key.path[-1]}.csv",
        )

    def load_input(self, context: dg.InputContext) -> pd.DataFrame:
        file_path = self._get_path(context)
        return load_pandas_dataframe(name=file_path)


class NumpyAssetIOManager(PandasAssetIOManager):
    def load_input(self, context: dg.InputContext) -> np.ndarray:  # pyright: ignore[reportIncompatibleMethodOverride]
        file_path = self._get_path(context)
        return load_numpy_array(name=file_path)


@dg.asset(io_manager_key="pandas_manager")
def upstream_asset() -> pd.DataFrame:
    return pd.DataFrame([1, 2, 3])


@dg.asset(
    ins={"upstream": dg.AssetIn(key_prefix="public", input_manager_key="numpy_manager")}
)
def downstream_asset(upstream: np.ndarray) -> tuple:
    return upstream.shape


defs = dg.Definitions(
    assets=[upstream_asset, downstream_asset],
    resources={
        "pandas_manager": PandasAssetIOManager(),
        "numpy_manager": NumpyAssetIOManager(),
    },
)

# end_numpy_example
