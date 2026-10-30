export const TITLE_MAX_LENGTH = 120;

export type TitleValidation = { ok: true; title: string } | { ok: false; message: string };

// Same rules as the backend (trimmed, required, at most 120 characters), so the form can
// explain a problem before a request is sent. The server still validates on its own.
export function validateTitle(rawTitle: string): TitleValidation {
  const title = rawTitle.trim();
  if (title === '') {
    return { ok: false, message: 'Enter a title before adding the task.' };
  }
  if (Array.from(title).length > TITLE_MAX_LENGTH) {
    return { ok: false, message: `Titles can be at most ${TITLE_MAX_LENGTH} characters.` };
  }
  return { ok: true, title };
}
