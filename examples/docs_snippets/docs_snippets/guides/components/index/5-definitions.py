import jaffle_platform.defs

from dagster import definitions, load_defs


@definitions
def defs():
    return load_defs(defs_root=jaffle_platform.defs)
