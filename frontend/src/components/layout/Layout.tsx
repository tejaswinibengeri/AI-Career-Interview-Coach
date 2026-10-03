import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import ErrorBoundary from "../ui/ErrorBoundary";
import PlatformHelpChatbot from "../chat/PlatformHelpChatbot";

/**
 * Root layout — wraps all pages with navigation, content area, and footer.
 */
export default function Layout() {
  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-1">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
      <Footer />
      {/* Floating Interactive Platform Help & Q&A Assistant */}
      <PlatformHelpChatbot />
    </div>
  );
}
