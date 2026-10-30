import { useState } from 'react';
import { DEFAULT_API_MODE, getTaskApi, type ApiMode } from './api';
import { TaskForm } from './components/TaskForm';
import { TaskList } from './components/TaskList';
import { useTasks } from './hooks/useTasks';

export function App() {
  const [mode, setMode] = useState<ApiMode>(DEFAULT_API_MODE);
  const tasks = useTasks(getTaskApi(mode));
  const isReady = tasks.loadStatus === 'ready';

  return (
    <main className="app">
      <header className="app__header">
        <h1>Todo demo</h1>
        <label className="mode-switch">
          Data source
          <select
            value={mode}
            onChange={(event) => setMode(event.target.value === 'real' ? 'real' : 'mock')}
          >
            <option value="mock">Mock (in browser)</option>
            <option value="real">Real API (/api)</option>
          </select>
        </label>
      </header>

      <TaskForm disabled={!isReady || tasks.isCreating} onCreate={tasks.createTask} />

      {tasks.actionError && (
        <p className="status status--error" role="alert">
          {tasks.actionError}
        </p>
      )}

      <TaskList
        tasks={tasks.tasks}
        loadStatus={tasks.loadStatus}
        loadError={tasks.loadError}
        pendingIds={tasks.pendingIds}
        onComplete={tasks.completeTask}
        onRetry={tasks.reload}
      />
    </main>
  );
}
