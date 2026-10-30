# Todo demo frontend

React + TypeScript + Vite client for the Todo demo. It lists tasks, adds a task, and marks a task complete. It follows [`docs/api-contract.md`](../docs/api-contract.md).

## Prerequisites

- Node.js 20 or newer, with npm.
- For real mode: the backend running on `http://127.0.0.1:8000`. This frontend doesn't start it.

## Install

```powershell
cd frontend
npm install
```

## Run with the mock (default)

```powershell
npm run dev
```

Open the URL Vite prints (usually `http://localhost:5173`). The app starts in **Mock (in browser)** mode. Mock data lives in memory and resets on page reload, matching the backend's in-memory state. Mock calls take about 400 ms so the loading state is visible.

## Run against the real API

1. Start the backend on port 8000 (for example `uvicorn ... --port 8000`).
2. Start the frontend:

   ```powershell
   npm run dev
   ```

3. In the page header, change **Data source** to **Real API (/api)**.

Requests go to `/api/...` on the Vite dev server. Vite forwards them to `http://127.0.0.1:8000`, so no CORS setup is needed.

To make real mode the default at startup, create `frontend/.env.local` (see `.env.example`):

```text
VITE_API_MODE=real
```

If the backend isn't running, the task list shows an error with a **Retry** button. Adding and completing tasks also show an error and do not change the list.

## Build and type-check

```powershell
npm run typecheck   # tsc for the app and for vite.config.ts
npm run build       # typecheck, then production build into dist/
npm run preview     # serve dist/ locally; /api is proxied the same way
```

## UI states

| Situation | What you see |
| --- | --- |
| Loading tasks | "Loading tasks…" status message |
| No tasks | "No tasks yet. Add one above." |
| Load fails | Error message with **Retry** |
| Add fails | Error banner above the list; the typed title stays in the input |
| Complete in progress | "Saving…" next to the task; checkbox disabled |
| Complete fails | Error banner; the task stays unchecked |
| Title empty or over 120 characters | Inline message; no request is sent |

A task is only shown as complete after the API returns the updated task.

## Project layout

```text
src/
  api/
    types.ts       Task model and TaskApi interface
    validation.ts  Title rules (trim, required, max 120)
    realApi.ts     fetch client for /api/tasks
    mockApi.ts     In-memory, contract-compatible mock
    index.ts       DEFAULT_API_MODE and getTaskApi(mode)
    errors.ts      ApiError and user-facing error messages
    guards.ts      Runtime checks for API responses
  hooks/useTasks.ts       Load, create, and complete state
  components/TaskForm.tsx
  components/TaskList.tsx
  App.tsx, main.tsx, styles.css
vite.config.ts     /api proxy to 127.0.0.1:8000
```

## Manual check

With either mode:

1. The loading message appears, then either the empty message or the list.
2. Add a task. Blank titles and titles over 120 characters are rejected in the form.
3. Check a task. Its title is struck through and its checkbox is locked.
4. Switch to real mode with the backend stopped. An error appears and **Retry** works once the backend is running.

There are no automated tests yet.
