import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/layout/Layout";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Profile from "./pages/Profile";
import Dashboard from "./pages/Dashboard";
import PersonalTrainer from "./pages/PersonalTrainer";
import CareerIntelligence from "./pages/CareerIntelligence";
import Resumes from "./pages/Resumes";
import ResumeAnalysis from "./pages/ResumeAnalysis";
import Roadmap from "./pages/Roadmap";
import Jobs from "./pages/Jobs";
import QuestionBank from "./pages/QuestionBank";
import InterviewSetup from "./pages/InterviewSetup";
import InterviewSession from "./pages/InterviewSession";
import InterviewResults from "./pages/InterviewResults";
import PerformanceAnalytics from "./pages/PerformanceAnalytics";
import CodingDirectory from "./pages/CodingDirectory";
import CodingEnvironment from "./pages/CodingEnvironment";
import CompanyPreparation from "./pages/CompanyPreparation";
import LearningResources from "./pages/LearningResources";
import ProjectRecommendations from "./pages/ProjectRecommendations";
import Achievements from "./pages/Achievements";
import NotificationsCenter from "./pages/NotificationsCenter";
import NotificationPreferences from "./pages/NotificationPreferences";
import AdminLayout from "./pages/admin/AdminLayout";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminUsers from "./pages/admin/AdminUsers";
import AdminQuestions from "./pages/admin/AdminQuestions";
import AdminResources from "./pages/admin/AdminResources";
import NotFound from "./pages/NotFound";

/**
 * Application root — defines routing, authentication context, and layout.
 */
export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route
              path="/personal-trainer"
              element={
                <ProtectedRoute>
                  <PersonalTrainer />
                </ProtectedRoute>
              }
            />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/career-intelligence"
              element={
                <ProtectedRoute>
                  <CareerIntelligence />
                </ProtectedRoute>
              }
            />

            <Route
              path="/resumes"
              element={
                <ProtectedRoute>
                  <Resumes />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resume-analysis/:id"
              element={
                <ProtectedRoute>
                  <ResumeAnalysis />
                </ProtectedRoute>
              }
            />
            {/* Legacy career paths redirect smoothly to Career Intelligence workspace */}
            <Route path="/career" element={<Navigate to="/career-intelligence?tab=match" replace />} />
            <Route path="/career/skill-gap" element={<Navigate to="/career-intelligence?tab=match" replace />} />
            <Route
              path="/roadmap"
              element={
                <ProtectedRoute>
                  <Roadmap />
                </ProtectedRoute>
              }
            />
            <Route
              path="/jobs"
              element={
                <ProtectedRoute>
                  <Jobs />
                </ProtectedRoute>
              }
            />
            <Route
              path="/question-bank"
              element={
                <ProtectedRoute>
                  <QuestionBank />
                </ProtectedRoute>
              }
            />
            <Route
              path="/interview"
              element={
                <ProtectedRoute>
                  <InterviewSetup />
                </ProtectedRoute>
              }
            />
            <Route
              path="/interview/:id"
              element={
                <ProtectedRoute>
                  <InterviewSession />
                </ProtectedRoute>
              }
            />
            <Route
              path="/interview/:id/results"
              element={
                <ProtectedRoute>
                  <InterviewResults />
                </ProtectedRoute>
              }
            />
            <Route
              path="/performance"
              element={
                <ProtectedRoute>
                  <PerformanceAnalytics />
                </ProtectedRoute>
              }
            />
            <Route
              path="/coding"
              element={
                <ProtectedRoute>
                  <CodingDirectory />
                </ProtectedRoute>
              }
            />
            <Route
              path="/coding/:slug"
              element={
                <ProtectedRoute>
                  <CodingEnvironment />
                </ProtectedRoute>
              }
            />
            <Route
              path="/company-preparation"
              element={
                <ProtectedRoute>
                  <CompanyPreparation />
                </ProtectedRoute>
              }
            />
            <Route
              path="/learning-resources"
              element={
                <ProtectedRoute>
                  <LearningResources />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects"
              element={
                <ProtectedRoute>
                  <ProjectRecommendations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/achievements"
              element={
                <ProtectedRoute>
                  <Achievements />
                </ProtectedRoute>
              }
            />
            <Route
              path="/notifications"
              element={
                <ProtectedRoute>
                  <NotificationsCenter />
                </ProtectedRoute>
              }
            />
            <Route
              path="/notifications/preferences"
              element={
                <ProtectedRoute>
                  <NotificationPreferences />
                </ProtectedRoute>
              }
            />

            {/* Admin Routes */}
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<AdminDashboard />} />
              <Route path="statistics" element={<AdminDashboard />} />
              <Route path="users" element={<AdminUsers />} />
              <Route path="questions" element={<AdminQuestions />} />
              <Route path="resources" element={<AdminResources />} />
            </Route>

            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>








    </AuthProvider>
  );
}
