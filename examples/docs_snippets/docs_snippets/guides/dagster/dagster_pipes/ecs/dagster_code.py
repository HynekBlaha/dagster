# start_asset_marker
import os

# dagster_glue_pipes.py
import boto3
from dagster_aws.pipes import PipesECSClient
from docutils.nodes import entry

from dagster import AssetExecutionContext, asset



@asset
def ecs_pipes_asset(context: AssetExecutionContext, pipes_ecs_client: PipesECSClient):
    return pipes_ecs_client.run(
        context=context,
        task_definition="dagster-pipes",
        launch_type="FARGATE",
        network_configuration={
            "awsvpcConfiguration": {
                "subnets": [
                    "subnet-a96acdc0"
                ],
                "securityGroups": ["sg-028d32553728591b2"],
                "assignPublicIp": "ENABLED",
            }
        },
    ).get_materialize_result()


# end_asset_marker

# start_definitions_marker

from dagster import Definitions  # noqa
from dagster_aws.pipes import PipesS3MessageReader


defs = Definitions(
    assets=[ecs_pipes_asset],
    resources={
        "pipes_ecs_client": PipesECSClient(
            client=boto3.client("ecs"),
        )
    },
)

# end_definitions_marker
