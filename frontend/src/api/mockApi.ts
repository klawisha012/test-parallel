import { ApiError } from './errors';
import type { Task, TaskApi } from './types';
import { validateTitle } from './validation';

// Long enough for the loading state to be visible during development.
const MOCK_LATENCY_MS = 400;

function wait(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, MOCK_LATENCY_MS));
}

// In-memory store that starts empty and resets on page reload, like the backend on restart.
export function createMockTaskApi(): TaskApi {
  let tasks: Task[] = [];
  let nextId = 1;

  return {
    async listTasks() {
      await wait();
      return tasks.map((task) => ({ ...task }));
    },

    async createTask(rawTitle) {
      await wait();
      const validation = validateTitle(rawTitle);
      if (!validation.ok) {
        throw new ApiError(validation.message, 422);
      }
      const task: Task = { id: `mock-${nextId}`, title: validation.title, completed: false };
      nextId += 1;
      tasks = [...tasks, task];
      return { ...task };
    },

    async completeTask(id) {
      await wait();
      const existing = tasks.find((task) => task.id === id);
      if (!existing) {
        throw new ApiError('Task not found.', 404);
      }
      const updated: Task = { ...existing, completed: true };
      tasks = tasks.map((task) => (task.id === id ? updated : task));
      return { ...updated };
    },
  };
}
