import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <section className="page-section" tabIndex={-1}>
      <p className="eyebrow">404</p>
      <h2>Page not found</h2>
      <p>This route is not part of the finance assistant demo.</p>
      <Link to="/ask">Return to Ask</Link>
    </section>
  );
}
