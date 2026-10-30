# Backend

```shell
python -m venv .venv
```

Activate the virtual environment, then:

```shell
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Data is held in memory and resets when the server stops. The shared API contract is in `../docs/api-contract.md`.
