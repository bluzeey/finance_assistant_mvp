import type { DataHealthResponse, MetaResponse, ProblemDetails } from './generated-types';

const DEFAULT_API_BASE_URL = 'http://localhost:8000';

export const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL ?? DEFAULT_API_BASE_URL
).replace(/\/$/, '');

export class ApiProblem extends Error {
  readonly problem: ProblemDetails;

  constructor(problem: ProblemDetails) {
    super(problem.detail);
    this.name = 'ApiProblem';
    this.problem = problem;
  }
}

export async function apiGet<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    method: 'GET',
    signal,
    headers: { Accept: 'application/json' },
  });

  if (!response.ok) {
    const problem = (await response.json().catch(() => ({
      type: 'about:blank',
      title: 'Request failed',
      status: response.status,
      detail: 'The finance service returned an unexpected error.',
      trace_id: response.headers.get('X-Trace-Id') ?? 'unknown',
    }))) as ProblemDetails;
    throw new ApiProblem(problem);
  }

  return (await response.json()) as T;
}

export function getMeta(signal?: AbortSignal): Promise<MetaResponse> {
  return apiGet<MetaResponse>('/api/v1/meta', signal);
}

export function getDataHealth(signal?: AbortSignal): Promise<DataHealthResponse> {
  return apiGet<DataHealthResponse>('/api/v1/data-health', signal);
}
