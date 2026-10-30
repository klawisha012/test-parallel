# test-parallel

Тест параллельной работы Codex и Claude Code через GitHub Issues. Цель — небольшой список задач с FastAPI и React. Контракт: [docs/api-contract.md](docs/api-contract.md).

Проектные скиллы находятся в `.agents/skills`, обёртки для Claude Code — в `.claude/skills`. Распределение заданий описано в `.agents/workflow/distribution.md`. Данные в приложении хранятся в памяти.

## Подготовка

- Python 3 и Node.js с npm.
- GitHub CLI `gh` в `PATH`, авторизованный для `klawisha012/test-parallel`.
- API: следуйте [backend/README.md](backend/README.md) и запустите сервер на порту 8000.
- UI: `cd frontend`, `npm install`, затем `npm run dev`. Откройте адрес Vite и выберите **Real API**.

Frontend и backend разрабатывались в отдельных ветках по общему контракту. Чтобы проверить реальный путь через Vite proxy после запуска обоих серверов, из корня выполните `python integration/smoke.py`. Проверка создаёт одну временную задачу в памяти backend.
