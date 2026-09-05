import type { RouteObject } from 'react-router-dom';
import { Navigate, createBrowserRouter } from 'react-router-dom';

import { AppShell } from '../components/layout/AppShell';
import { AboutPage } from '../features/about/AboutPage';
import { AskPage } from '../features/ask/AskPage';
import { ConversationPage } from '../features/ask/ConversationPage';
import { DataHealthPage } from '../features/data-health/DataHealthPage';
import { EvaluationPage } from '../features/evaluation/EvaluationPage';
import { ExplorerPage } from '../features/explorer/ExplorerPage';
import { GlossaryPage } from '../features/glossary/GlossaryPage';
import { NotFoundPage } from '../features/about/NotFoundPage';
import { ReconciliationPage } from '../features/reconciliation/ReconciliationPage';

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/ask" replace /> },
      { path: 'ask', element: <AskPage /> },
      { path: 'ask/:conversationId', element: <ConversationPage /> },
      { path: 'explorer', element: <ExplorerPage /> },
      { path: 'reconciliation', element: <ReconciliationPage /> },
      { path: 'data-health', element: <DataHealthPage /> },
      { path: 'glossary', element: <GlossaryPage /> },
      { path: 'evaluation', element: <EvaluationPage /> },
      { path: 'about', element: <AboutPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
];

export const router = createBrowserRouter(routes);
