"""
A demo client.
"""

from pathlib import Path

import requests
from ethpm_types import ContractType, PackageManifest, Source
from ethpm_types.source import Content
from requests import Response

URL = "http://127.0.0.1:8000"
CONTENT = Content(__root__=Path("ERC20.vy").read_text())
MANIFEST = PackageManifest(sources={"ERC20.vy": Source(content=CONTENT)})


class Client:
    def compile(self) -> str:
        response = self._post("compile", json=MANIFEST.dict())
        result = response.text.strip("'\"")
        if "{" in result:
            raise Exception(f"Error: {result}")

        # Str
        return result

    def get_compiled_artifact(self, task_id: str) -> PackageManifest:
        response = self._get(f"compiled_artifact/{task_id}")

        if "{" not in response.text:
            raise Exception(f"Error: {response.text}")

        data = response.json()
        return PackageManifest.parse_obj(data)

    @classmethod
    def _get(cls, url: str, **kwargs) -> Response:
        return requests.get(f"{URL}/{url}", **kwargs)

    @classmethod
    def _post(cls, url: str, **kwargs) -> Response:
        return requests.post(f"{URL}/{url}", **kwargs)


def main():
    client = Client()
    task_id = client.compile()
    print(f"Task ID is {task_id}")
    manifest = client.get_compiled_artifact(task_id)
    print(manifest)


if __name__ == "__main__":
    main()
