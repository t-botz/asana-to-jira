from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, Optional
from urllib.parse import urljoin

import aiohttp


@dataclass(frozen=True)
class AsanaTask:
    id: str
    title: str
    description: str
    link: str


@dataclass(frozen=True)
class AsanaClient:
    base_url: str
    token: str

    def _headers(self) -> Dict[str, str]:
        return {
            'Content-Type': r'application/json',
            'Authorization': fr'Bearer {self.token}',
        }

    async def get_incomplete_tasks(
            self,
            project_id: str,
            session: aiohttp.ClientSession) -> Iterable[int]:
        async with session.get(
            urljoin(self.base_url, "tasks"),
            headers=self._headers(),
            raise_for_status=True,
            params={"project": project_id,
                    "completed_since": datetime.utcnow().isoformat()},
        ) as resp:
            j = await resp.json()
            return (d["gid"] for d in j["data"])

    async def get_task(
            self,
            task_id: str,
            session: aiohttp.ClientSession) -> Optional[AsanaTask]:
        async with session.get(
            urljoin(self.base_url, f"tasks/{task_id}"),
            raise_for_status=True,
            headers=self._headers(),
        ) as resp:
            json = await resp.json()
            return AsanaTask(
                id=json["data"]["gid"],
                title=json["data"]["name"],
                description=json["data"]["notes"],
                link=json['data']['permalink_url'],
            )
