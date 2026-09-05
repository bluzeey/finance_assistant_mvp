import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Button, ButtonLink } from './button';

describe('shadcn-style Button', () => {
  it('renders default and outline variants', () => {
    render(
      <>
        <Button>Primary</Button>
        <Button variant="outline">Outline</Button>
      </>,
    );

    expect(screen.getByRole('button', { name: 'Primary' })).toHaveClass('shadcn-btn-default');
    expect(screen.getByRole('button', { name: 'Outline' })).toHaveClass('shadcn-btn-outline');
  });

  it('renders ButtonLink with anchor role and link classes', () => {
    render(
      <ButtonLink href="/" variant="ghost">
        Export
      </ButtonLink>,
    );

    expect(screen.getByRole('link', { name: 'Export' })).toHaveClass('shadcn-btn-ghost');
    expect(screen.getByRole('link', { name: 'Export' })).toHaveAttribute('href', '/');
  });
});
