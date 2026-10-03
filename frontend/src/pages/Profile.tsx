import { useState, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { useAuth } from "../hooks/useAuth";
import api, { APIError, type ProfileData, type UserData } from "../lib/api";
import LoadingSpinner from "../components/ui/LoadingSpinner";

export default function Profile() {
  const { user, updateUser } = useAuth();

  // Tab State
  const [activeTab, setActiveTab] = useState<"profile" | "security">("profile");

  // Profile Form State
  const [name, setName] = useState(user?.name || "");
  const [education, setEducation] = useState("");
  const [degree, setDegree] = useState("");
  const [graduationYear, setGraduationYear] = useState<string>("");
  const [experience, setExperience] = useState("");
  const [currentRole, setCurrentRole] = useState("");
  const [targetRole, setTargetRole] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [newSkillInput, setNewSkillInput] = useState("");
  const [preferredLocation, setPreferredLocation] = useState("");
  const [workPreference, setWorkPreference] = useState("Remote");
  const [careerGoal, setCareerGoal] = useState("");

  // Security Form State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Status & Feedback States
  const [isLoadingProfile, setIsLoadingProfile] = useState(true);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);
  const [profileErrorMsg, setProfileErrorMsg] = useState<string | null>(null);
  const [passwordSuccessMsg, setPasswordSuccessMsg] = useState<string | null>(null);
  const [passwordErrorMsg, setPasswordErrorMsg] = useState<string | null>(null);

  // Suggested skills for quick addition
  const suggestedSkills = [
    "Python",
    "JavaScript",
    "TypeScript",
    "React",
    "FastAPI",
    "Node.js",
    "SQL",
    "Docker",
    "AWS",
    "System Design",
    "Data Structures",
    "Machine Learning",
  ];

  // Fetch initial profile
  useEffect(() => {
    let isMounted = true;

    async function loadProfile() {
      try {
        const response = await api.get<ProfileData>("/api/v1/profile");
        if (response.data && isMounted) {
          const p = response.data;
          setEducation(p.education || "");
          setDegree(p.degree || "");
          setGraduationYear(p.graduation_year ? String(p.graduation_year) : "");
          setExperience(p.experience || "");
          setCurrentRole(p.current_role || "");
          setTargetRole(p.target_role || "");
          setSkills(p.skills || []);
          setPreferredLocation(p.preferred_location || "");
          setWorkPreference(p.work_preference || "Remote");
          setCareerGoal(p.career_goal || "");
        }
      } catch {
        if (isMounted) {
          setProfileErrorMsg("Failed to load profile details.");
        }
      } finally {
        if (isMounted) {
          setIsLoadingProfile(false);
        }
      }
    }

    void loadProfile();

    return () => {
      isMounted = false;
    };
  }, []);

  // Skill tag management
  const addSkill = (skillToAdd: string) => {
    const trimmed = skillToAdd.trim();
    if (trimmed && !skills.includes(trimmed)) {
      setSkills([...skills, trimmed]);
    }
    setNewSkillInput("");
  };

  const handleSkillKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addSkill(newSkillInput);
    }
  };

  const removeSkill = (skillToRemove: string) => {
    setSkills(skills.filter((s) => s !== skillToRemove));
  };

  // Submit Profile Update
  const handleProfileSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setProfileSuccessMsg(null);
    setProfileErrorMsg(null);
    setIsSavingProfile(true);

    try {
      const payload = {
        name: name.trim(),
        education: education.trim() || null,
        degree: degree.trim() || null,
        graduation_year: graduationYear ? parseInt(graduationYear, 10) : null,
        experience: experience.trim() || null,
        current_role: currentRole.trim() || null,
        target_role: targetRole.trim() || null,
        skills,
        preferred_location: preferredLocation.trim() || null,
        work_preference: workPreference || null,
        career_goal: careerGoal.trim() || null,
      };

      const response = await api.put<ProfileData>("/api/v1/profile", payload);
      if (response.data) {
        setProfileSuccessMsg("Profile saved successfully!");

        // Refresh user in context to update name across navigation
        if (user) {
          const updatedUserData: UserData = {
            ...user,
            name: name.trim(),
            profile: response.data,
          };
          updateUser(updatedUserData);
        }

        setTimeout(() => setProfileSuccessMsg(null), 4000);
      }
    } catch (err) {
      if (err instanceof APIError) {
        setProfileErrorMsg(err.message);
      } else {
        setProfileErrorMsg("Failed to save profile changes.");
      }
    } finally {
      setIsSavingProfile(false);
    }
  };

  // Submit Password Change
  const handlePasswordSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setPasswordSuccessMsg(null);
    setPasswordErrorMsg(null);

    if (newPassword.length < 6) {
      setPasswordErrorMsg("New password must be at least 6 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordErrorMsg("New passwords do not match.");
      return;
    }

    setIsChangingPassword(true);
    try {
      await api.put("/api/v1/profile/password", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      setPasswordSuccessMsg("Password changed successfully!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setPasswordSuccessMsg(null), 4000);
    } catch (err) {
      if (err instanceof APIError) {
        setPasswordErrorMsg(err.message);
      } else {
        setPasswordErrorMsg("Failed to update password.");
      }
    } finally {
      setIsChangingPassword(false);
    }
  };

  const getInitials = (fullName: string) => {
    return fullName
      .split(" ")
      .map((n) => n[0])
      .filter(Boolean)
      .slice(0, 2)
      .join("")
      .toUpperCase() || "U";
  };

  if (isLoadingProfile) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 animate-fade-in">
        <LoadingSpinner size="lg" />
        <p className="text-surface-200/60 text-sm animate-pulse">Loading your profile...</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 animate-fade-in">
      {/* Header Banner */}
      <div className="relative rounded-2xl glass border border-white/10 p-6 sm:p-8 mb-8 overflow-hidden bg-gradient-to-r from-surface-900/90 via-surface-900/60 to-brand-950/40">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 relative z-10">
          <div className="flex items-center gap-5">
            <div className="h-16 w-16 sm:h-20 sm:w-20 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center text-white text-xl sm:text-2xl font-bold shadow-xl shadow-brand-600/30 border border-white/20 flex-shrink-0">
              {getInitials(name || user?.name || "")}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                  {name || user?.name || "Career Profile"}
                </h1>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Active
                </span>
              </div>
              <p className="text-sm text-surface-200/70 mt-1 flex items-center gap-2">
                <svg className="w-4 h-4 text-surface-200/50" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 0 1-2.25 2.25h-15a2.25 2.25 0 0 1-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25m19.5 0v.243a2.25 2.25 0 0 1-1.07 1.916l-7.5 4.615a2.25 2.25 0 0 1-2.36 0L3.32 8.91a2.25 2.25 0 0 1-1.07-1.916V6.75" />
                </svg>
                {user?.email}
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex bg-surface-950/60 p-1.5 rounded-xl border border-white/5 self-stretch sm:self-auto">
            <button
              onClick={() => setActiveTab("profile")}
              className={`flex-1 sm:flex-initial px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === "profile"
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "text-surface-200/70 hover:text-white"
              }`}
            >
              Profile & Career
            </button>
            <button
              onClick={() => setActiveTab("security")}
              className={`flex-1 sm:flex-initial px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeTab === "security"
                  ? "bg-brand-600 text-white shadow-md shadow-brand-600/30"
                  : "text-surface-200/70 hover:text-white"
              }`}
            >
              Security
            </button>
          </div>
        </div>
      </div>

      {/* Main Tab Content */}
      {activeTab === "profile" ? (
        <form onSubmit={handleProfileSubmit} className="space-y-8 animate-fade-in">
          {/* Notifications */}
          {profileSuccessMsg && (
            <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 flex items-center gap-3 text-emerald-400 text-sm animate-fade-in">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
              <span>{profileSuccessMsg}</span>
            </div>
          )}

          {profileErrorMsg && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-center gap-3 text-red-400 text-sm animate-fade-in">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <span>{profileErrorMsg}</span>
            </div>
          )}

          {/* Section 1: Basic & Education Information */}
          <div className="glass rounded-2xl border border-white/10 p-6 sm:p-8 bg-surface-900/70 space-y-6">
            <div className="border-b border-white/5 pb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342" />
                </svg>
                Personal & Education
              </h2>
              <p className="text-xs text-surface-200/60 mt-1">Your core identity and academic background.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Full Name
                </label>
                <input
                  id="profile-name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Alex Mercer"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  disabled
                  value={user?.email || ""}
                  className="w-full rounded-xl bg-surface-950/60 border border-white/5 px-4 py-2.5 text-sm text-surface-200/50 cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Education / University
                </label>
                <input
                  id="profile-education"
                  type="text"
                  value={education}
                  onChange={(e) => setEducation(e.target.value)}
                  placeholder="e.g. Massachusetts Institute of Technology"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Degree / Major
                </label>
                <input
                  id="profile-degree"
                  type="text"
                  value={degree}
                  onChange={(e) => setDegree(e.target.value)}
                  placeholder="e.g. B.S. in Computer Science"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Graduation Year
                </label>
                <input
                  id="profile-graduation-year"
                  type="number"
                  min="1960"
                  max="2035"
                  value={graduationYear}
                  onChange={(e) => setGraduationYear(e.target.value)}
                  placeholder="e.g. 2025"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Experience Level
                </label>
                <input
                  id="profile-experience"
                  type="text"
                  value={experience}
                  onChange={(e) => setExperience(e.target.value)}
                  placeholder="e.g. 2 years / Entry-Level / Senior"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Career Targets & Preferences */}
          <div className="glass rounded-2xl border border-white/10 p-6 sm:p-8 bg-surface-900/70 space-y-6">
            <div className="border-b border-white/5 pb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6" />
                </svg>
                Career Targets & Preferences
              </h2>
              <p className="text-xs text-surface-200/60 mt-1">Specify your current status and target ambitions.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Current Role / Status
                </label>
                <input
                  id="profile-current-role"
                  type="text"
                  value={currentRole}
                  onChange={(e) => setCurrentRole(e.target.value)}
                  placeholder="e.g. Student / Junior Developer"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Target Role
                </label>
                <input
                  id="profile-target-role"
                  type="text"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  placeholder="e.g. Full Stack AI Engineer"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Preferred Location
                </label>
                <input
                  id="profile-location"
                  type="text"
                  value={preferredLocation}
                  onChange={(e) => setPreferredLocation(e.target.value)}
                  placeholder="e.g. San Francisco, CA / Remote Global"
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Work Preference
                </label>
                <select
                  id="profile-work-preference"
                  value={workPreference}
                  onChange={(e) => setWorkPreference(e.target.value)}
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                >
                  <option value="Remote">Remote</option>
                  <option value="Hybrid">Hybrid</option>
                  <option value="On-site">On-site</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                  Career Goal & Aspirations
                </label>
                <textarea
                  id="profile-career-goal"
                  rows={3}
                  value={careerGoal}
                  onChange={(e) => setCareerGoal(e.target.value)}
                  placeholder="Describe your 1-3 year career goals, target industries, or specific technical focus areas..."
                  className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-3 text-sm text-white focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
                />
              </div>
            </div>
          </div>

          {/* Section 3: Interactive Skills Manager */}
          <div className="glass rounded-2xl border border-white/10 p-6 sm:p-8 bg-surface-900/70 space-y-6">
            <div className="border-b border-white/5 pb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" />
                </svg>
                Skills & Tech Stack
              </h2>
              <p className="text-xs text-surface-200/60 mt-1">Add your core technical proficiencies and domain strengths.</p>
            </div>

            {/* Current Skills Tags */}
            <div>
              <div className="flex flex-wrap gap-2 min-h-12 p-3 rounded-xl bg-surface-800/50 border border-white/5">
                {skills.length === 0 ? (
                  <span className="text-xs text-surface-200/40 italic py-1">
                    No skills added yet. Type below or select from suggestions.
                  </span>
                ) : (
                  skills.map((skill) => (
                    <span
                      key={skill}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-brand-500/20 text-brand-300 border border-brand-500/30 group animate-fade-in"
                    >
                      {skill}
                      <button
                        type="button"
                        onClick={() => removeSkill(skill)}
                        className="hover:text-red-400 transition-colors p-0.5"
                        title={`Remove ${skill}`}
                      >
                        ×
                      </button>
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* Add Skill Input */}
            <div className="flex gap-2">
              <input
                id="profile-skill-input"
                type="text"
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={handleSkillKeyDown}
                placeholder="Type a skill and press Enter..."
                className="flex-1 rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
              />
              <button
                type="button"
                id="profile-add-skill-btn"
                onClick={() => addSkill(newSkillInput)}
                className="px-5 py-2.5 rounded-xl bg-brand-600/30 hover:bg-brand-600/50 text-brand-300 border border-brand-500/30 text-sm font-medium transition-all cursor-pointer"
              >
                + Add
              </button>
            </div>

            {/* Suggested Skills */}
            <div>
              <span className="text-xs text-surface-200/50 block mb-2 font-medium">Quick suggestions:</span>
              <div className="flex flex-wrap gap-1.5">
                {suggestedSkills
                  .filter((s) => !skills.includes(s))
                  .map((suggestion) => (
                    <button
                      type="button"
                      key={suggestion}
                      onClick={() => addSkill(suggestion)}
                      className="px-2.5 py-1 rounded-md text-xs bg-surface-800/60 hover:bg-surface-700/80 text-surface-200/70 hover:text-white border border-white/5 transition-colors cursor-pointer"
                    >
                      + {suggestion}
                    </button>
                  ))}
              </div>
            </div>
          </div>

          {/* Submit Action */}
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              id="profile-save-btn"
              disabled={isSavingProfile}
              className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-semibold text-sm shadow-lg shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 cursor-pointer"
            >
              {isSavingProfile ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>Saving changes...</span>
                </>
              ) : (
                <span>Save Profile Changes</span>
              )}
            </button>
          </div>
        </form>
      ) : (
        /* Security & Password Tab */
        <div className="glass rounded-2xl border border-white/10 p-6 sm:p-8 bg-surface-900/70 max-w-xl mx-auto space-y-6 animate-fade-in">
          <div className="border-b border-white/5 pb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <svg className="w-5 h-5 text-brand-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
              </svg>
              Change Password
            </h2>
            <p className="text-xs text-surface-200/60 mt-1">
              Ensure your account is using a strong, unique password.
            </p>
          </div>

          {passwordSuccessMsg && (
            <div className="rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-4 flex items-center gap-3 text-emerald-400 text-sm animate-fade-in">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 12.75 6 6 9-13.5" />
              </svg>
              <span>{passwordSuccessMsg}</span>
            </div>
          )}

          {passwordErrorMsg && (
            <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-4 flex items-center gap-3 text-red-400 text-sm animate-fade-in">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 3.75h.008v.008H12v-.008Z" />
              </svg>
              <span>{passwordErrorMsg}</span>
            </div>
          )}

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                Current Password
              </label>
              <input
                id="current-password"
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                New Password
              </label>
              <input
                id="new-password"
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min. 6 characters"
                className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-surface-200/80 mb-2">
                Confirm New Password
              </label>
              <input
                id="confirm-new-password"
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter new password"
                className="w-full rounded-xl bg-surface-800/80 border border-white/10 px-4 py-2.5 text-sm text-white placeholder:text-surface-200/30 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 transition-all"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                id="change-password-btn"
                disabled={isChangingPassword}
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-white font-semibold text-sm shadow-lg shadow-brand-600/30 hover:shadow-brand-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer"
              >
                {isChangingPassword ? (
                  <>
                    <LoadingSpinner size="sm" />
                    <span>Updating password...</span>
                  </>
                ) : (
                  <span>Update Password</span>
                )}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
