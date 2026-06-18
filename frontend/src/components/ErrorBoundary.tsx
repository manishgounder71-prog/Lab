'use client';

import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] Caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="min-h-[400px] flex items-center justify-center glass-panel m-4 p-8 rounded-xl">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center">
              <span className="text-red-400 text-2xl font-bold">!</span>
            </div>
            <h2 className="font-title-md font-bold text-white mb-2">Component crashed</h2>
            <p className="text-xs text-[var(--color-on-surface-variant)] mb-4 font-mono">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 bg-[var(--color-primary)] text-[var(--color-on-primary)] text-xs rounded hover:bg-white transition-all"
              aria-label="Retry rendering"
            >
              RETRY
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
