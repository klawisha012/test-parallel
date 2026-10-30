import { ApiError } from './errors';
import { isRecord, isTask } from './guards';
import type { Task, TaskApi } from './types';

const TASKS_PATH = '/api/tasks';
const UNREACHABLE_MESSAGE =
  'Could not reach the API. Check that the backend is running on 127.0.0.1:8000.';
const MALFORMED_MESSAGE = 'The API returned an unexpected response.';

async function readErrorDetail(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json();
    if (isRecord(body) && typeof body.detail === 'string') {
      return body.detail;
    }
  } catch {
    // Non-JSON error bodies fall through to the status-based message below.
  }
  return `Request failed with HTTP ${response.status}.`;
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    });
  } catch {
    throw new ApiError(UNREACHABLE_MESSAGE, null);
  }

  if (!response.ok) {
    throw new ApiError(await readErrorDetail(response), response.status);
  }

  try {
    return await response.json();
  } catch {
    throw new ApiError(MALFORMED_MESSAGE, response.status);
  }
}

function expectTask(body: unknown): Task {
  if (!isTask(body)) {
    throw new ApiError(MALFORMED_MESSAGE, null);
  }
  return body;
}

export const realTaskApi: TaskApi = {
  async listTasks() {
    const body = await request(TASKS_PATH);
    if (!isRecord(body) || !Array.isArray(body.tasks) || !body.tasks.every(isTask)) {
      throw new ApiError(MALFORMED_MESSAGE, null);
    }
    return body.tasks;
  },

  async createTask(title) {
    const body = await request(TASKS_PATH, { method: 'POST', body: JSON.stringify({ title }) });
    return expectTask(body);
  },

  async completeTask(id) {
    const body = await request(`${TASKS_PATH}/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      body: JSON.stringify({ completed: true }),
    });
    return expectTask(body);
  },
};
