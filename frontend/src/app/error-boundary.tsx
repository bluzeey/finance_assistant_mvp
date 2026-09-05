import type { ErrorInfo, PropsWithChildren, ReactNode } from 'react';
import { Component } from 'react';

import { Button } from '../components/ui/button';

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Do not log raw finance records here. The browser console receives only the
    // component stack in local development.
    if (import.meta.env.DEV) {
      console.error(error, info.componentStack);
    }
  }

  render(): ReactNode {
    if (this.state.error) {
      return (
        <main className="error-boundary" role="alert">
          <h1>Something went wrong</h1>
          <p>The finance workspace hit a UI error. No financial number was changed.</p>
          <Button type="button" onClick={() => this.setState({ error: null })}>
            Try again
          </Button>
        </main>
      );
    }
    return this.props.children;
  }
}
