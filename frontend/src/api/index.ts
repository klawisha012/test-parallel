import { createMockTaskApi } from './mockApi';
import { realTaskApi } from './realApi';
import type { TaskApi } from './types';

export type ApiMode = 'mock' | 'real';

export const DEFAULT_API_MODE: ApiMode = import.meta.env.VITE_API_MODE === 'real' ? 'real' : 'mock';

// One mock instance per page load, so its tasks survive switching modes back and forth.
const mockTaskApi = createMockTaskApi();

export function getTaskApi(mode: ApiMode): TaskApi {
  return mode === 'real' ? realTaskApi : mockTaskApi;
}
