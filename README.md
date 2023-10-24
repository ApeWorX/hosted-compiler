# Overview

**Vyper Compiler** is a tool used to help [Remix Online IDE](https://remix-project.org/) compile Vyper contracts.

Vyper Compiler is built by [ApeWorX LTD](https://www.apeworx.io/).

If you have any questions please ask in our discord [ApeWorX Discord server](https://discord.gg/apeworx).

## Documentation

The compiler is built with Ape and fastAPI. It has multiple routes to engage the compiler in different parts of your journey to  compiler the contract.


## Quickstart with local contracts

To show that it works. Clone this repo and deploy the local host server with `uvicorn main:app --reload`

Using the post route: Upload the contract file and version number of vyper.

Wait for it compile and while you wait, you can use the temporary directory name is the task ID to check the status of it.

Once it says success, you can use the `get compiled artifact` route and return the manifest of the contract.


## Docker implementation

To use the docker implementation: `docker run -p 8000:8000  ghcr.io/apeworx/hosted-compiler:latest`.
