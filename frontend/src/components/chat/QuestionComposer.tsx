import { useId, useState } from 'react';

interface QuestionComposerProps {
  onSubmit: (message: string) => void;
  isPending?: boolean;
  onCancel?: () => void;
  placeholder?: string;
}

const MAX_MESSAGE_LENGTH = 4_000;

export function QuestionComposer({
  onSubmit,
  isPending = false,
  onCancel,
  placeholder = 'Ask about payouts, spend, reconciliation, or data health…',
}: QuestionComposerProps) {
  const [message, setMessage] = useState('');
  const textareaId = useId();
  const trimmed = message.trim();
  const canSubmit = trimmed.length > 0 && !isPending;

  function submit() {
    if (!canSubmit) {
      return;
    }
    onSubmit(trimmed);
    setMessage('');
  }

  return (
    <form
      className="composer"
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <label htmlFor={textareaId}>Finance question</label>
      <textarea
        id={textareaId}
        rows={3}
        maxLength={MAX_MESSAGE_LENGTH}
        value={message}
        placeholder={placeholder}
        onChange={(event) => setMessage(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            submit();
          }
        }}
      />
      <div className="composer-footer">
        <span>{message.length}/{MAX_MESSAGE_LENGTH} · Enter sends, Shift+Enter adds a line</span>
        <div className="button-row">
          {isPending ? (
            <button type="button" className="secondary" onClick={onCancel}>
              Stop
            </button>
          ) : null}
          <button type="submit" disabled={!canSubmit}>
            Send
          </button>
        </div>
      </div>
    </form>
  );
}
