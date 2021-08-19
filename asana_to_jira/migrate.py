import asyncio
import logging

import typer
from aiohttp.client import ClientSession
from typer.params import Option

from asana_to_jira.asana_client import AsanaClient

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main(
    asana_project_id: str,
    jira_project_key: str,
    asana_token: str = Option(..., envvar="ASANA_TOKEN"),
    asana_url: str = Option("https://app.asana.com/api/1.0/", envvar="ASANA_URL"),
    jira_username: str = Option(..., envvar="JIRA_USERNAME"),
    jira_password: str = Option(..., envvar="JIRA_PASSWORD"),
    jira_url: str = Option(..., envvar="JIRA_URL")
):
    async def _main():
        asana = AsanaClient(base_url=asana_url, token=asana_token)
        async with ClientSession() as session:
            for t in asyncio.as_completed([
                asana.get_task(id, session)
                for id in await asana.get_incomplete_tasks(asana_project_id, session)
            ]):
                logger.info(await t)

    asyncio.run(_main())


if __name__ == "__main__":
    typer.run(main)
