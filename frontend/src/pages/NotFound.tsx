import { Link } from "react-router-dom";

/**
 * 404 — Not Found page.
 */
export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <div className="text-center space-y-6 animate-fade-in">
        <h1 className="text-8xl font-black gradient-text">404</h1>
        <h2 className="text-2xl font-semibold text-white">Page not found</h2>
        <p className="text-surface-200/50 max-w-sm mx-auto">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link to="/" className="btn-primary inline-block">
          Go Home
        </Link>
      </div>
    </div>
  );
}
