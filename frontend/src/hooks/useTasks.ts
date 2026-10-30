import { useCallback, useEffect, useState } from 'react';
import { errorMessage } from '../api/errors';
import type { Task, TaskApi } from '../api/types';

export type LoadStatus = 'loading' | 'ready' | 'error';

export interface TasksState {
  tasks: Task[];
  loadStatus: LoadStatus;
  loadError: string | null;
  actionError: string | null;
  pendingIds: ReadonlySet<string>;
  isCreating: boolean;
  reload: () => void;
  createTask: (title: string) => Promise<boolean>;
  completeTask: (id: string) => Promise<void>;
}

// Local state is only changed after the API confirms a write, so a failed write never shows as done.
export function useTasks(api: TaskApi): TasksState {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadStatus, setLoadStatus] = useState<LoadStatus>('loading');
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [pendingIds, setPendingIds] = useState<ReadonlySet<string>>(new Set());
  const [isCreating, setIsCreating] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setTasks([]);
    setLoadStatus('loading');
    setLoadError(null);
    setActionError(null);

    api.listTasks().then(
      (loaded) => {
        if (!cancelled) {
          setTasks(loaded);
          setLoadStatus('ready');
        }
      },
      (error: unknown) => {
        if (!cancelled) {
          setLoadError(errorMessage(error));
          setLoadStatus('error');
        }
      },
    );

    return () => {
      cancelled = true;
    };
  }, [api, reloadToken]);

  const reload = useCallback(() => {
    setReloadToken((token) => token + 1);
  }, []);

  const createTask = useCallback(
    async (title: string): Promise<boolean> => {
      setIsCreating(true);
      setActionError(null);
      try {
        const created = await api.createTask(title);
        setTasks((current) => [...current, created]);
        return true;
      } catch (error) {
        setActionError(`Could not add the task. ${errorMessage(error)}`);
        return false;
      } finally {
        setIsCreating(false);
      }
    },
    [api],
  );

  const completeTask = useCallback(
    async (id: string): Promise<void> => {
      setActionError(null);
      setPendingIds((current) => new Set(current).add(id));
      try {
        const updated = await api.completeTask(id);
        setTasks((current) => current.map((task) => (task.id === id ? updated : task)));
      } catch (error) {
        setActionError(`Could not complete the task. ${errorMessage(error)}`);
      } finally {
        setPendingIds((current) => {
          const next = new Set(current);
          next.delete(id);
          return next;
        });
      }
    },
    [api],
  );

  return {
    tasks,
    loadStatus,
    loadError,
    actionError,
    pendingIds,
    isCreating,
    reload,
    createTask,
    completeTask,
  };
}
