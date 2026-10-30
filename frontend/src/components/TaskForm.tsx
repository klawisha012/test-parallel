import { useState, type FormEvent } from 'react';
import { TITLE_MAX_LENGTH, validateTitle } from '../api/validation';

interface TaskFormProps {
  disabled: boolean;
  onCreate: (title: string) => Promise<boolean>;
}

export function TaskForm({ disabled, onCreate }: TaskFormProps) {
  const [title, setTitle] = useState('');
  const [validationMessage, setValidationMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validation = validateTitle(title);
    if (!validation.ok) {
      setValidationMessage(validation.message);
      return;
    }
    setValidationMessage(null);
    const created = await onCreate(validation.title);
    // Keep the typed text when the write fails so the user can retry without retyping.
    if (created) {
      setTitle('');
    }
  }

  return (
    <form className="task-form" onSubmit={handleSubmit} noValidate>
      <label htmlFor="new-task-title">New task</label>
      <div className="task-form__row">
        <input
          id="new-task-title"
          type="text"
          value={title}
          placeholder={`What needs doing? (max ${TITLE_MAX_LENGTH} characters)`}
          aria-invalid={validationMessage !== null}
          aria-describedby={validationMessage ? 'new-task-title-error' : undefined}
          disabled={disabled}
          onChange={(event) => setTitle(event.target.value)}
        />
        <button type="submit" disabled={disabled}>
          Add task
        </button>
      </div>
      {validationMessage && (
        <p id="new-task-title-error" className="task-form__error" role="alert">
          {validationMessage}
        </p>
      )}
    </form>
  );
}
