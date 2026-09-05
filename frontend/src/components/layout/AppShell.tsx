import { useQuery } from '@tanstack/react-query';
import { NavLink, Outlet } from 'react-router-dom';

import { getMeta } from '../../api/client';
import { DatasetFreshnessChip } from './DatasetFreshnessChip';

const navItems = [
  { to: '/ask', label: 'Ask' },
  { to: '/explorer', label: 'Explorer' },
  { to: '/reconciliation', label: 'Reconcile' },
  { to: '/data-health', label: 'Data health' },
  { to: '/glossary', label: 'Glossary' },
  { to: '/evaluation', label: 'Evaluation' },
  { to: '/about', label: 'About' },
];

export function AppShell() {
  const metaQuery = useQuery({ queryKey: ['meta'], queryFn: ({ signal }) => getMeta(signal) });
  const companyLabel = metaQuery.data?.company.display_name ?? 'Northstar Labs';

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">LP</span>
          <div>
            <strong>LedgerProof</strong>
            <span>Finance assistant</span>
          </div>
        </div>
        <nav className="primary-nav">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? 'active' : undefined)}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <p className="demo-note">Synthetic demo data · no live ERP connection</p>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">{companyLabel}</span>
            <h1>Auditable finance answers</h1>
          </div>
          <div className="topbar-actions" aria-label="Dataset status">
            <span className="chip chip-muted">Synthetic data</span>
            <DatasetFreshnessChip
              meta={metaQuery.data}
              isLoading={metaQuery.isLoading}
              isError={metaQuery.isError}
            />
          </div>
        </header>
        <main id="main-content" className="content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
