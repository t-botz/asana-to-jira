import asyncio
import logging

import aiohttp
import typer
from aiohttp.client import ClientSession
from jira import JIRA
from typer.params import Option

from asana_to_jira.asana_client import AsanaClient, AsanaTask

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def main(
    asana_project_id: str,
    jira_project_key: str,
    asana_token: str = Option(..., envvar="ASANA_TOKEN"),
    asana_url: str = Option("https://app.asana.com/api/1.0/", envvar="ASANA_URL"),
    asana_label_migrated_gid: str = Option(...),
    jira_username: str = Option(..., envvar="JIRA_USERNAME"),
    jira_password: str = Option(..., envvar="JIRA_PASSWORD"),
    jira_url: str = Option(..., envvar="JIRA_URL")
):
    async def _main():
        asana = AsanaClient(base_url=asana_url, token=asana_token)
        jira = JIRA(jira_url, basic_auth=(jira_username, jira_password))
        connector = aiohttp.TCPConnector(force_close=True)
        async with ClientSession(connector=connector) as session:
            logger.info("Retrieving Tasks")
            tasks = await asana.get_incomplete_tasks(asana_project_id, session)
            for t in tasks:
                await process_asana_task(asana, jira, t, asana_label_migrated_gid, jira_project_key, session)

    asyncio.run(_main())


async def process_asana_task(
        asana_client: AsanaClient,
        jira: JIRA,
        task_id: str,
        asana_label_migrated_gid: str,
        jira_project_key: str,
        session: ClientSession):
    logger.info("[Task %s] Fetching", task_id)
    task = await asana_client.get_task(task_id, session)
    if asana_label_migrated_gid not in task.tags:
        issue_key = create_jira(task, jira, jira_project_key)
        logger.info("[Task %s] Creating Comment on asana", task_id)
        comment = f"<body>Migrated to Jira as <a href='{jira.server_url}/browse/{issue_key}'>{issue_key}</a></body>"
        await asana_client.add_comment(task_id, comment, session)
        logger.info("[Task %s] Creating Label on asana", task_id)
        await asana_client.add_label(task_id, asana_label_migrated_gid, session)
    else:
        logger.info("[Task %s] Already Migrated", task_id)
    logger.info("[Task %s] Done!", task_id)


def create_jira(t: AsanaTask, jira: JIRA, project_key: str) -> str:
    logger.info("[Task %s] Creating Jira", t.id)
    issue = jira.create_issue(project=project_key, summary=t.title,
                              description=t.description, issuetype={'name': 'Story'})
    logger.info("[Task %s] Jira issue created : %s",  t.id, issue)
    jira.add_comment(issue.key, f'Migrated from  Asana : {t.link}')
    logger.info("[Task %s] Jira comment created", t.id)

    return issue.key


if __name__ == "__main__":
    typer.run(main)
