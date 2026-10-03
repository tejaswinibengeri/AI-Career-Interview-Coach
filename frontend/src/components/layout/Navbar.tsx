import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";
import api, { type NotificationData } from "../../lib/api";

/**
 * Premium, full-width dynamic navigation header with slide-over drawer sidebar.
 * All navigation buttons, features, and logout are seamlessly housed in the
 * dynamic sidebar accessible via the 3-bars menu beside the user profile.
 */
export default function Navbar() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [recentNotifs, setRecentNotifs] = useState<NotificationData[]>([]);

  const notifRef = useRef<HTMLDivElement>(null);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, logout } = useAuth();

  // Close sidebar and notifications when route changes
  useEffect(() => {
    setSidebarOpen(false);
    setNotifOpen(false);
  }, [location.pathname]);

  // Lock body scroll when sidebar drawer is open
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [sidebarOpen]);

  // Handle escape key to close sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSidebarOpen(false);
        setNotifOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Fetch notifications for authenticated users
  useEffect(() => {
    if (isAuthenticated) {
      fetchNotifSummary();
    }
  }, [isAuthenticated, location.pathname]);

  // Click outside listener for notification popup
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (notifRef.current && !notifRef.current.contains(target)) {
        setNotifOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const fetchNotifSummary = async () => {
    try {
      const res = await api.getNotifications();
      if (res.data) {
        setUnreadCount(res.data.unread_count);
        setRecentNotifs(res.data.notifications.slice(0, 5));
      }
    } catch {
      // Ignore notification fetch error
    }
  };

  const handleLogout = async () => {
    setSidebarOpen(false);
    await logout();
    navigate("/");
  };

  const getInitials = (name: string) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  const isActive = (path: string) => location.pathname === path;

  // Sidebar navigation sections
  const careerLinks = [
    { to: "/jobs", label: "Jobs", icon: "💼", desc: "AI matched openings" },
    { to: "/resumes", label: "Resume Studio", icon: "📁", badge: "ATS Scored", desc: "ATS analysis & revision history" },
    { to: "/projects", label: "Projects", icon: "🚀", desc: "Portfolio project ideas" },
  ];

  const coreLinks = [
    { to: "/dashboard", label: "Dashboard", icon: "🏠", desc: "Overview & readiness stats" },
    { to: "/roadmap", label: "Career Roadmap", icon: "🗺️", desc: "Milestone-driven path" },
  ];

  const prepLinks = [
    { to: "/company-preparation", label: "Company Prep", icon: "🏢", badge: "25+ Qs", desc: "Targeted company questions & strategy" },
    { to: "/question-bank", label: "Question Bank", icon: "📚", badge: "AI Powered", desc: "Technical, DSA, SQL & HR items" },
    { to: "/coding", label: "Coding Practice", icon: "💻", desc: "Python & SQL challenge runner" },
    { to: "/interview", label: "Mock Interview", icon: "🎙️", badge: "Live Rubric", desc: "AI speech & behavioral evaluation" },
  ];

  const growthLinks = [
    { to: "/learning-resources", label: "Learning Hub", icon: "📖", desc: "Courses, docs & roadmaps" },
    { to: "/performance", label: "Analytics", icon: "📈", desc: "Score breakdown & radar metrics" },
    { to: "/achievements", label: "Badges & Streaks", icon: "🏆", badge: "Trophies", desc: "Achievements & milestones" },
  ];

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-surface-950/90 backdrop-blur-xl border-b border-white/10 shadow-lg shadow-black/20 transition-all">
        <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-10">
          <div className="flex items-center justify-between h-16">

            {/* LEFT: 3 BARS (HAMBURGER) SIDEBAR TOGGLE, Profile Pill & Notifications */}
            <div className="flex items-center gap-3 shrink-0">
              {isAuthenticated ? (
                <div className="flex items-center gap-2 sm:gap-3">

                  {/* 3 BARS (HAMBURGER) ICON */}
                  <button
                    type="button"
                    onClick={() => setSidebarOpen(true)}
                    className="relative p-2.5 rounded-xl bg-surface-900/90 hover:bg-surface-800 border border-white/10 hover:border-brand-500/40 text-white transition-all cursor-pointer shadow-md group flex items-center justify-center"
                    title="Open Navigation Menu"
                    aria-label="Open Navigation Sidebar"
                  >
                    <div className="w-5 h-4 flex flex-col justify-between items-center">
                      <span className="w-5 h-0.5 bg-surface-200 group-hover:bg-brand-400 rounded-full transition-all duration-200" />
                      <span className="w-4 h-0.5 bg-surface-200 group-hover:bg-brand-400 rounded-full transition-all duration-200 self-start group-hover:w-5" />
                      <span className="w-5 h-0.5 bg-surface-200 group-hover:bg-brand-400 rounded-full transition-all duration-200" />
                    </div>
                  </button>

                  {/* Notification Bell */}
                  <div className="relative" ref={notifRef}>
                    <button
                      type="button"
                      onClick={() => setNotifOpen(!notifOpen)}
                      className="relative p-2.5 rounded-xl bg-surface-900/90 hover:bg-surface-800 border border-white/10 text-surface-200 hover:text-white transition-all cursor-pointer shadow-sm"
                      title="Notifications"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
                        />
                      </svg>

                      {unreadCount > 0 && (
                        <span className="absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full bg-red-500 text-white text-[9px] font-black shadow-md animate-pulse">
                          {unreadCount}
                        </span>
                      )}
                    </button>

                    {/* Notification Dropdown Panel */}
                    {notifOpen && (
                      <div className="absolute left-0 mt-2 w-80 sm:w-96 rounded-2xl bg-surface-900 border border-white/10 shadow-2xl p-4 space-y-3 z-50 animate-fade-in">
                        <div className="flex items-center justify-between border-b border-white/5 pb-2">
                          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                            Notifications ({unreadCount} Unread)
                          </h4>
                          <Link
                            to="/notifications"
                            onClick={() => setNotifOpen(false)}
                            className="text-[11px] text-brand-300 hover:text-white font-semibold transition-colors"
                          >
                            View All →
                          </Link>
                        </div>

                        {recentNotifs.length === 0 ? (
                          <p className="text-xs text-surface-200/60 py-4 text-center">No notifications available.</p>
                        ) : (
                          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                            {recentNotifs.map((n) => (
                              <div
                                key={n.id}
                                onClick={() => {
                                  setNotifOpen(false);
                                  if (n.link_url) navigate(n.link_url);
                                }}
                                className={`p-2.5 rounded-xl border text-xs cursor-pointer transition-colors space-y-1 ${
                                  !n.is_read
                                    ? "bg-surface-800/90 border-brand-500/30 hover:bg-surface-800"
                                    : "bg-surface-800/40 border-white/5 opacity-70 hover:opacity-100"
                                }`}
                              >
                                <div className="flex items-center justify-between font-bold text-white">
                                  <span className="truncate">{n.title}</span>
                                  {!n.is_read && <span className="w-1.5 h-1.5 rounded-full bg-red-400" />}
                                </div>
                                <p className="text-surface-200/80 text-[11px] line-clamp-2">{n.message}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Profile Icon Pill */}
                  <Link
                    to="/profile"
                    className="flex items-center gap-2.5 pl-2 pr-3 py-1.5 rounded-xl bg-surface-900/90 hover:bg-surface-800 border border-white/10 text-xs text-surface-200 hover:text-white transition-all cursor-pointer shadow-sm group"
                    title="View Profile"
                  >
                    <div className="h-7 w-7 rounded-lg bg-gradient-to-tr from-brand-600 to-indigo-500 flex items-center justify-center text-white font-black text-xs shadow-sm group-hover:scale-105 transition-transform">
                      {getInitials(user?.name || "")}
                    </div>
                    <span className="font-semibold max-w-[110px] truncate text-white hidden sm:inline-block">
                      {user?.name}
                    </span>
                  </Link>

                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    to="/login"
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold text-surface-200/90 hover:text-white hover:bg-white/5 transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    className="px-4 py-2 rounded-xl text-xs font-semibold text-white bg-brand-600 hover:bg-brand-500 shadow-md shadow-brand-600/30 transition-all"
                  >
                    Get Started →
                  </Link>
                </div>
              )}
            </div>

            {/* CENTER: Minimal Clean Status Indicator / Quick Route Badge */}
            <div className="hidden md:flex items-center gap-2 text-xs font-semibold text-surface-200/60">
              {isAuthenticated && (
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-900/60 border border-white/5 text-surface-200/80">
                  <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                  <span className="text-xs font-medium">Active Workspace</span>
                </div>
              )}
            </div>

            {/* RIGHT: Branding Logo & Site Name */}
            <Link to="/" className="flex items-center gap-3 shrink-0 group">
              <div className="flex flex-col text-right">
                <span className="font-extrabold text-base tracking-tight text-white leading-none group-hover:text-brand-300 transition-colors">
                  Placement AI
                </span>
                <span className="text-[10px] text-surface-200/60 font-medium tracking-wider uppercase mt-0.5">
                  Career & Interview Coach
                </span>
              </div>
              <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-brand-600 via-brand-500 to-indigo-400 flex items-center justify-center font-black text-white text-sm shadow-md shadow-brand-600/30 group-hover:scale-105 transition-transform duration-200">
                CP
              </div>
            </Link>

          </div>
        </div>
      </header>

      {/* DYNAMIC SLIDE-OVER SIDEBAR DRAWER */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          {/* Backdrop Blur Overlay */}
          <div
            className="fixed inset-0 bg-black/65 backdrop-blur-sm transition-opacity duration-300 animate-fade-in cursor-pointer"
            onClick={() => setSidebarOpen(false)}
            aria-hidden="true"
          />

          <div className="fixed inset-y-0 left-0 max-w-full flex pr-10">
            {/* Sidebar Container */}
            <aside
              ref={sidebarRef}
              className="w-screen max-w-md bg-surface-950 border-r border-white/10 shadow-2xl flex flex-col justify-between transform transition-transform duration-300 ease-in-out animate-slide-in-left"
            >
              {/* TOP HEADER: User Profile Card & Close Button */}
              <div className="p-5 border-b border-white/10 bg-surface-900/60 backdrop-blur-md">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-11 w-11 rounded-2xl bg-gradient-to-tr from-brand-600 via-brand-500 to-indigo-500 flex items-center justify-center text-white font-black text-base shadow-lg shadow-brand-600/30">
                      {getInitials(user?.name || "")}
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-bold text-white truncate">{user?.name || "Test User"}</h3>
                      <p className="text-xs text-surface-200/60 truncate">{user?.email || "user@example.com"}</p>
                      <span className="inline-block mt-1 px-2 py-0.5 rounded text-[9px] font-extrabold uppercase tracking-wider bg-brand-500/20 text-brand-300 border border-brand-500/30">
                        {user?.role === "admin" ? "👑 Administrator" : "🚀 Active Candidate"}
                      </span>
                    </div>
                  </div>

                  {/* Close 'X' Button */}
                  <button
                    type="button"
                    onClick={() => setSidebarOpen(false)}
                    className="p-2 rounded-xl bg-surface-800 hover:bg-surface-700 text-surface-200 hover:text-white border border-white/10 transition-colors cursor-pointer"
                    title="Close Sidebar"
                    aria-label="Close Sidebar"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* MIDDLE SCROLLABLE NAVIGATION: All Feature Buttons */}
              <div className="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar">

                {/* 1. PERSONAL TRAINER (Topmost Primary Feature - BEFORE Dashboard) */}
                <div className="space-y-2">
                  <div className="p-3.5 rounded-2xl bg-gradient-to-b from-brand-950/80 via-surface-900/95 to-indigo-950/60 border-2 border-brand-500/50 shadow-xl shadow-brand-900/30 space-y-2 relative overflow-hidden group">
                    <div className="absolute -right-8 -top-8 w-24 h-24 bg-brand-500/15 rounded-full blur-xl group-hover:bg-brand-500/25 transition-all pointer-events-none" />
                    <Link
                      to="/personal-trainer"
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 p-2 rounded-xl transition-all ${
                        isActive("/personal-trainer")
                          ? "bg-brand-600/40 text-white font-bold border border-brand-400/50"
                          : "text-white hover:bg-white/5"
                      }`}
                    >
                      <span className="text-2xl p-2 rounded-xl bg-gradient-to-tr from-brand-600 to-indigo-500 text-white shadow-md shadow-brand-600/40 shrink-0 group-hover:scale-105 transition-transform">
                        🧠
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-extrabold text-white tracking-tight">Personal Trainer</span>
                          <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-gradient-to-r from-brand-500/30 to-indigo-500/30 text-brand-300 border border-brand-400/40 shadow-sm animate-pulse">
                            Primary
                          </span>
                        </div>
                        <span className="text-[11px] text-surface-200/70 block truncate mt-0.5">
                          Personalized day-by-day learning journey
                        </span>
                      </div>
                    </Link>
                  </div>
                </div>

                {/* 2. CORE DASHBOARD Section */}
                <div className="space-y-2">
                  <div className="grid grid-cols-1 gap-1.5">
                    {coreLinks.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                          isActive(item.to)
                            ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-sm"
                            : "hover:bg-white/5 text-surface-200/90 hover:text-white"
                        }`}
                      >
                        <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">
                          {item.icon}
                        </span>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-bold text-white block">{item.label}</span>
                          <span className="text-[11px] text-surface-200/60 block truncate">{item.desc}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>

                {/* 3. CAREER INTELLIGENCE Section (Primary Workspace) */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-brand-400 px-2 flex items-center gap-1.5">
                    <span>🧠</span>
                    <span>Career Intelligence</span>
                  </p>
                  <div className="p-3 rounded-2xl bg-gradient-to-b from-brand-950/40 to-surface-900/90 border border-brand-500/30 space-y-2">
                    <Link
                      to="/career-intelligence"
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 p-2 rounded-xl transition-all ${
                        isActive("/career-intelligence")
                          ? "bg-brand-600/30 text-white font-bold"
                          : "text-white hover:bg-white/5"
                      }`}
                    >
                      <span className="text-xl p-1.5 rounded-lg bg-surface-950 border border-brand-500/20 shrink-0">
                        🧠
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white">Career Intelligence Hub</span>
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                            Primary
                          </span>
                        </div>
                        <span className="text-[10px] text-surface-200/60 block truncate">
                          Dedicated career-analysis workspace
                        </span>
                      </div>
                    </Link>

                    {/* Sub-items branch */}
                    <div className="pl-5 border-l-2 border-brand-500/30 ml-4 space-y-1 pt-1">
                      <Link
                        to="/career-intelligence?tab=analyzer"
                        onClick={() => setSidebarOpen(false)}
                        className="flex items-center gap-2 py-1.5 px-2 rounded-lg text-xs text-surface-200/80 hover:text-white hover:bg-white/5 transition-colors"
                      >
                        <span className="text-sm">📋</span>
                        <span className="font-medium">Job Description Analyzer</span>
                      </Link>

                      <Link
                        to="/career-intelligence?tab=match"
                        onClick={() => setSidebarOpen(false)}
                        className="flex items-center gap-2 py-1.5 px-2 rounded-lg text-xs text-surface-200/80 hover:text-white hover:bg-white/5 transition-colors"
                      >
                        <span className="text-sm">🎯</span>
                        <span className="font-medium">Resume → JD Match</span>
                      </Link>

                      <Link
                        to="/career-intelligence?tab=cover-letter"
                        onClick={() => setSidebarOpen(false)}
                        className="flex items-center gap-2 py-1.5 px-2 rounded-lg text-xs text-surface-200/80 hover:text-white hover:bg-white/5 transition-colors"
                      >
                        <span className="text-sm">✍️</span>
                        <span className="font-medium">Cover Letter Generator</span>
                      </Link>

                      <Link
                        to="/career-intelligence?tab=cold-email"
                        onClick={() => setSidebarOpen(false)}
                        className="flex items-center gap-2 py-1.5 px-2 rounded-lg text-xs text-surface-200/80 hover:text-white hover:bg-white/5 transition-colors"
                      >
                        <span className="text-sm">📧</span>
                        <span className="font-medium">Cold Email Generator</span>
                      </Link>
                    </div>
                  </div>
                </div>

                {/* 2. CAREER & OPPORTUNITIES Section (Independent Modules) */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-surface-200/50 px-2">
                    Career & Opportunities
                  </p>
                  <div className="grid grid-cols-1 gap-1.5">
                    {careerLinks.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                          isActive(item.to)
                            ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-sm"
                            : "hover:bg-white/5 text-surface-200/90 hover:text-white"
                        }`}
                      >
                        <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">
                          {item.icon}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-white">{item.label}</span>
                            {item.badge && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                                {item.badge}
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-surface-200/60 block truncate">{item.desc}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>

                {/* 3. Interview & Practice Section */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-surface-200/50 px-2">
                    Interview & Practice
                  </p>
                  <div className="grid grid-cols-1 gap-1.5">
                    {prepLinks.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                          isActive(item.to)
                            ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-sm"
                            : "hover:bg-white/5 text-surface-200/90 hover:text-white"
                        }`}
                      >
                        <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">
                          {item.icon}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-white">{item.label}</span>
                            {item.badge && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-brand-500/20 text-brand-300 border border-brand-500/30">
                                {item.badge}
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-surface-200/60 block truncate">{item.desc}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
                {/* 4. Learning & Growth Section */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-surface-200/50 px-2">
                    Learning & Analytics
                  </p>
                  <div className="grid grid-cols-1 gap-1.5">
                    {growthLinks.map((item) => (
                      <Link
                        key={item.to}
                        to={item.to}
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                          isActive(item.to)
                            ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-sm"
                            : "hover:bg-white/5 text-surface-200/90 hover:text-white"
                        }`}
                      >
                        <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">
                          {item.icon}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-white">{item.label}</span>
                            {item.badge && (
                              <span className="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                {item.badge}
                              </span>
                            )}
                          </div>
                          <span className="text-[11px] text-surface-200/60 block truncate">{item.desc}</span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>

                {/* 5. Account Settings Section */}
                <div className="space-y-2">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-surface-200/50 px-2">
                    Account & Preferences
                  </p>
                  <div className="grid grid-cols-1 gap-1.5">
                    <Link
                      to="/profile"
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                        isActive("/profile")
                          ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-sm"
                          : "hover:bg-white/5 text-surface-200/90 hover:text-white"
                      }`}
                    >
                      <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">👤</span>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-bold text-white block">Profile Details</span>
                        <span className="text-[11px] text-surface-200/60 block truncate">Education, skills & career target</span>
                      </div>
                    </Link>

                    <Link
                      to="/notifications/preferences"
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                        isActive("/notifications/preferences")
                          ? "bg-brand-600/20 text-brand-300 border border-brand-500/40 shadow-sm"
                          : "hover:bg-white/5 text-surface-200/90 hover:text-white"
                      }`}
                    >
                      <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">⚙️</span>
                      <div className="flex-1 min-w-0">
                        <span className="text-xs font-bold text-white block">Notification Preferences</span>
                        <span className="text-[11px] text-surface-200/60 block truncate">Alerts & email triggers</span>
                      </div>
                    </Link>

                    {(user?.role === "admin" || user?.is_superuser) && (
                      <Link
                        to="/admin"
                        onClick={() => setSidebarOpen(false)}
                        className={`flex items-center gap-3 p-2.5 rounded-xl transition-all ${
                          isActive("/admin")
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm"
                            : "hover:bg-white/5 text-amber-300/90 hover:text-amber-200"
                        }`}
                      >
                        <span className="text-xl p-1.5 rounded-lg bg-surface-900 border border-white/5 shrink-0">👑</span>
                        <div className="flex-1 min-w-0">
                          <span className="text-xs font-bold text-white block">Admin Dashboard</span>
                          <span className="text-[11px] text-amber-300/60 block truncate">User & resource administration</span>
                        </div>
                      </Link>
                    )}
                  </div>
                </div>

              </div>

              {/* BOTTOM FOOTER: LOGOUT BUTTON IN THE SIDEBAR ONLY */}
              <div className="p-5 border-t border-white/10 bg-surface-900/80 backdrop-blur-md space-y-2">
                <button
                  type="button"
                  id="sidebar-logout-btn"
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-xs font-bold text-red-400 hover:text-white bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 hover:border-red-500/50 shadow-sm transition-all cursor-pointer group"
                >
                  <svg
                    className="w-4 h-4 text-red-400 group-hover:translate-x-0.5 transition-transform"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  <span>Log Out of Session</span>
                </button>
                <p className="text-[10px] text-center text-surface-200/40">Placement AI v2.0 • AI Career Platform</p>
              </div>
            </aside>
          </div>
        </div>
      )}
    </>
  );
}
