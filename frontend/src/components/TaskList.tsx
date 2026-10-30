import type { Task } from '../api/types';
import type { LoadStatus } from '../hooks/useTasks';

interface TaskListProps {
  tasks: Task[];
  loadStatus: LoadStatus;
  loadError: string | null;
  pendingIds: ReadonlySet<string>;
  onComplete: (id: string) => void;
  onRetry: () => void;
}

export function TaskList({
  tasks,
  loadStatus,
  loadError,
  pendingIds,
  onComplete,
  onRetry,
}: TaskListProps) {
  if (loadStatus === 'loading') {
    return <p className="status" role="status">Loading tasks…</p>;
  }

  if (loadStatus === 'error') {
    return (
      <div className="status status--error" role="alert">
        <p>Could not load tasks. {loadError}</p>
        <button type="button" onClick={onRetry}>
          Retry
        </button>
      </div>
    );
  }

  if (tasks.length === 0) {
    return <p className="status" role="status">No tasks yet. Add one above.</p>;
  }

  return (
    <ul className="task-list">
      {tasks.map((task) => {
        const isPending = pendingIds.has(task.id);
        return (
          <li key={task.id} className="task-item">
            <label>
              <input
                type="checkbox"
                checked={task.completed}
                disabled={task.completed || isPending}
                onChange={() => onComplete(task.id)}
              />
              <span className={task.completed ? 'task-item__title task-item__title--done' : 'task-item__title'}>
                {task.title}
              </span>
            </label>
            {isPending && <span className="task-item__pending">Saving…</span>}
          </li>
        );
      })}
    </ul>
  );
}
