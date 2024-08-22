# Overview

The **Hosted Compiler** is a tool used to help [Remix Online IDE](https://remix-project.org/) to remotely compile contracts.

The Hosted Compiler is built by [ApeWorX LTD](https://www.apeworx.io/).

If you have any questions please ask in our discord [ApeWorX Discord server](https://discord.gg/apeworx).

## Documentation

The compiler is built with Ape and FastAPI.
It has multiple routes to engage the compiler in different parts of your journey to  compiler the contract.

## Quickstart with local contracts

To show that it works, clone this repo and deploy the local host server with:

```sh
uvicorn main:app
```

Using the post route: Send an EthPM v3 ([EIP-2678](https://eips.ethereum.org/EIPS/eip-2678)) compatible package manifest object
containing the sources and compiler configurations you wish to compile with to this hosted service.

Wait for it compile and while you wait, you can use the task ID to check the status of it.

Once the status says success, you can use the `get artifacts` route and return a package manifest containing all compilation artifacts for the sources that were provided.

**NOTE**: Only the supported compilers will appear in the resulting manifest.

### Supported Compilers

| Compiler Name | Supported |
| ------------- | --------- |
| Solidity      | No        |
| Vyper         | Yes       |
| ...           | ...       |

## Docker implementation

To use the docker implementation:

```sh
docker run -p 8000:8000  ghcr.io/apeworx/hosted-compiler:latest
```

## Dev instructions

Use the `uvicorn` and the example client to assist in developing the hosted compiler.

Start the dev server using `uvicorn`:

```sh
uvicorn main:app --reload
```

Then, run the example client, which compiles an example project:

```shell
ape run client
```
