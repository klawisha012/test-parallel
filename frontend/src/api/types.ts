export interface Task {
  id: string;
  title: string;
  completed: boolean;
}

// Mirrors docs/api-contract.md. Both the real client and the mock implement this.
export interface TaskApi {
  listTasks(): Promise<Task[]>;
  createTask(title: string): Promise<Task>;
  completeTask(id: string): Promise<Task>;
}
