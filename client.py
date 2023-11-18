import requests
from ethpm_types import ContractType, PackageManifest, Source
from ethpm_types.source import Content
from pathlib import Path

URL = "http://127.0.0.1:8000"
CONTENT = Content(__root__=Path("contracts/Contract.vy").read_text())
MANIFEST = PackageManifest(sources={"Contract.vy": Source(content=CONTENT)})


class Client:
    def compile(self) -> str:
        response = requests.post(f"{URL}/compile", json=MANIFEST.dict())
        result = response.text.strip("'\"")
        if "{" in result:
            raise Exception(f"YOU BADDDDD {result}")

        return result

    def get_compiled_artifact(self, task_id: str):
        response = requests.get(f"{URL}/compiled_artifact/{task_id}")

        if "{" not in response.text:
            raise Exception(f"YOU BADDDDD {response.text}")

        return response.json()


def main():
    client = Client()
    task_id = client.compile()
    print(f"Task ID is {task_id}")
    manifest = client.get_compiled_artifact(task_id)
    print(manifest)


if __name__ == "__main__":
    main()
