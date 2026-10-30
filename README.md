# test-parallel

Тест параллельной работы Codex и Claude Code через GitHub Issues. Цель — небольшой список задач с FastAPI и React. Контракт: [docs/api-contract.md](docs/api-contract.md).

Проектные скиллы находятся в `.agents/skills`, обёртки для Claude Code — в `.claude/skills`. Распределение заданий описано в `.agents/workflow/distribution.md`. Данные в приложении хранятся в памяти.

## Подготовка

- Python 3 и Node.js с npm.
- GitHub CLI `gh` в `PATH`, авторизованный для `klawisha012/test-parallel`.
- API: `cd backend`, затем установите `requirements.txt` и запустите `uvicorn app:app --reload`.
- UI: `cd frontend`, `npm install`, затем `npm run dev`.

Frontend и backend разрабатываются в отдельных ветках по общему контракту. Команды запуска будут уточнены после их реализации.
