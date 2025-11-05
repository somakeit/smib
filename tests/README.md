To get started:
- Refer to the [README](README.md) for overall setup instructions, to setup and run SMIB
- Run `uv pip install -e .` to install the required dependencies locally
- Run `docker compose up -d --build --force-recreate` to start SMIB
- Run `uv run pytest` to run the tests 

```bash
uv pip install -e .
docker compose up -d --build --force-recreate
uv run pytest
```