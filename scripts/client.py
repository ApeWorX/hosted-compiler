"""
A demo client.
"""

from pathlib import Path

import click
import requests  # type: ignore[import-untyped]
from ape.logging import logger
from ethpm_types import PackageManifest, Source
from ethpm_types.source import Content
from requests import Response

URL = "http://127.0.0.1:8000"
CONTENT = Content(root=Path("contracts/ERC20.vy").read_text())
MANIFEST = PackageManifest(sources={"contracts/ERC20.vy": Source(content=CONTENT)})


class Client:
    def compile(self) -> str:
        response = self._post("compile", json=MANIFEST.model_dump())
        result = response.text.strip("'\"")
        if "{" in result:
            raise Exception(f"Error: {result}")

        # Str
        return result

    def get_compiled_artifact(self, task_id: str) -> PackageManifest:
        response = self._get(f"artifacts/{task_id}")

        if "{" not in response.text:
            raise Exception(f"Error: {response.text}")

        data = response.json()
        return PackageManifest.model_validate(data)

    @classmethod
    def _get(cls, url: str, **kwargs) -> Response:
        return requests.get(f"{URL}/{url}", **kwargs)

    @classmethod
    def _post(cls, url: str, **kwargs) -> Response:
        return requests.post(f"{URL}/{url}", **kwargs)


@click.command()
def cli():
    client = Client()
    task_id = client.compile()
    logger.info(f"Task ID is '{task_id}'.")

    manifest = client.get_compiled_artifact(task_id)
    if contract_types := manifest.contract_types:
        for ct in contract_types:
            logger.success(f"Contract '{ct}' compiled!")

    else:
        logger.error("No contract types returned.")
