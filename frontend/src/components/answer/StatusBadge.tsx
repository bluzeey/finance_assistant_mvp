import type { AnswerStatus } from '../../api/generated-types';

const statusCopy: Record<AnswerStatus, { label: string; className: string; description: string }> = {
  verified: {
    label: 'Verified',
    className: 'status-verified',
    description: 'Executed query and required validations passed.',
  },
  qualified: {
    label: 'Qualified',
    className: 'status-qualified',
    description: 'Computed result has a material caveat.',
  },
  needs_clarification: {
    label: 'Needs clarification',
    className: 'status-blocked',
    description: 'Multiple interpretations could materially change the result.',
  },
  not_answerable: {
    label: 'Not in the data',
    className: 'status-blocked',
    description: 'Required field or domain is absent from the dataset.',
  },
  no_matching_rows: {
    label: 'No matching records',
    className: 'status-qualified',
    description: 'The query was valid, but no source rows matched.',
  },
  error: {
    label: "Couldn't verify",
    className: 'status-error',
    description: 'A technical or validation failure blocked the number.',
  },
};

interface StatusBadgeProps {
  status: AnswerStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const copy = statusCopy[status];
  return (
    <span className={`status-badge ${copy.className}`} title={copy.description}>
      <span aria-hidden="true">●</span>
      {copy.label}
    </span>
  );
}
