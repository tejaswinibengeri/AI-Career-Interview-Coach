import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

interface Message {
  id: string;
  sender: "bot" | "user";
  text: string;
  links?: Array<{ label: string; to: string; icon?: string }>;
  timestamp: string;
}

interface QuickTopic {
  label: string;
  icon: string;
  query: string;
}

const QUICK_TOPICS: QuickTopic[] = [
  { label: "Check ATS Resume Score", icon: "📄", query: "how to check resume score" },
  { label: "Find & Apply to Jobs", icon: "💼", query: "how to find and apply in jobs" },
  { label: "Create / Edit Profile", icon: "👤", query: "how to create a profile" },
  { label: "Match Resume to Job (JD)", icon: "🎯", query: "how to match resume to job description" },
  { label: "Start AI Mock Interview", icon: "🎙️", query: "how to start mock interview" },
  { label: "Get AI Project Ideas", icon: "🚀", query: "how to get project recommendations" },
  { label: "Daily Personal Trainer", icon: "🧠", query: "how does personal trainer work" },
  { label: "Practice Coding Challenges", icon: "💻", query: "how to practice coding" },
  { label: "Company-Specific Prep", icon: "🏢", query: "how to prepare for specific company" },
  { label: "Email Notifications & Reminders", icon: "📧", query: "how to get email notifications" },
];

const KNOWLEDGE_BASE: Array<{
  keywords: string[];
  response: string;
  links?: Array<{ label: string; to: string; icon?: string }>;
}> = [
  {
    keywords: ["resume", "score", "ats", "upload resume", "re-analyze", "resume score", "analysis", "strength", "weakness"],
    response:
      "**Checking Your Resume ATS Score & Feedback:**\n\n1. Go to **Resume Studio**.\n2. Click **'Upload New Resume'** to upload your `.pdf` or `.docx` file.\n3. Open the resume to view your transparent **ATS Score (0–100%)** broken down across Structure (20%), Skills (30%), Experience (25%), Education (15%), and Formatting (10%).\n4. Review your **Key Strengths**, **Areas for Improvement**, and **Formatting/Grammar Suggestions**.\n5. Click **'Re-Analyze with AI'** anytime to refresh evaluations!",
    links: [{ label: "Open Resume Studio", to: "/resumes", icon: "📁" }],
  },
  {
    keywords: ["apply", "job", "jobs", "find job", "search job", "career openings", "apply job", "job match"],
    response:
      "**Finding & Applying to Jobs:**\n\n1. Navigate to the **Jobs Hub**.\n2. Search by job title, location, or toggle **'Remote Only'**.\n3. Click on any job to view role requirements and salary details.\n4. Click **'Match with Resume'** to see an AI match score (0–100%) and missing skill recommendations.\n5. Click **'Apply on Provider Site'** to jump straight to the live job application.",
    links: [{ label: "Browse Job Openings", to: "/jobs", icon: "💼" }],
  },
  {
    keywords: ["profile", "create profile", "edit profile", "target role", "skills", "experience", "education", "career goal"],
    response:
      "**Creating & Updating Your Career Profile:**\n\n1. Go to **Profile Details**.\n2. Fill in your **Degree**, **Graduation Year**, and **Current Role**.\n3. Select your **Target Career Role** (e.g. Full Stack Engineer, AI/ML Specialist, Data Scientist).\n4. Add your **Key Technical & Soft Skills**.\n5. Your profile automatically personalizes all job match scores, roadmap phases, and project recommendations across the platform!",
    links: [{ label: "Manage Profile", to: "/profile", icon: "👤" }],
  },
  {
    keywords: ["jd", "job description", "career intelligence", "cover letter", "cold email", "match jd", "outreach"],
    response:
      "**Career Intelligence & JD Matcher:**\n\n1. Visit **Career Intelligence Hub**.\n2. **JD Analyzer**: Paste any external job posting to extract required skills, qualifications, and keywords.\n3. **Resume → JD Match**: Compare your resume against the JD to get alignment percentages.\n4. **Cover Letter Generator**: Create tailored, role-specific cover letters.\n5. **Cold Email Generator**: Generate high-converting outreach emails to recruiters and hiring managers!",
    links: [{ label: "Open Career Intelligence", to: "/career-intelligence", icon: "🧠" }],
  },
  {
    keywords: ["interview", "mock interview", "voice", "speech", "practice interview", "rubric", "behavioral"],
    response:
      "**Interactive AI Mock Interviews:**\n\n1. Go to **Mock Interview**.\n2. Select your target role (Software Engineer, Backend, Frontend, Full Stack) and difficulty (Entry, Mid, Senior).\n3. Choose Technical, HR, or Behavioral interview focus.\n4. Answer turn-by-turn using **Voice Speech Input (Microphone)** or text.\n5. After each answer, receive transparent scoring rubrics (Relevance, Correctness, Clarity) with detailed ideal answers and improvement coaching!",
    links: [{ label: "Start Mock Interview", to: "/interview", icon: "🎙️" }],
  },
  {
    keywords: ["project", "projects", "portfolio", "recommendation", "build project", "ideas"],
    response:
      "**Personalized AI Project Recommendations:**\n\n1. Head to **Projects**.\n2. Click **'Generate New Recommendations 🪄'**.\n3. Placement AI reviews your candidate profile, target career role, and missing skill gaps.\n4. Get **4 to 6 comprehensive project architectures** across Beginner, Intermediate, and Advanced tiers with complete tech stacks and expected deliverables.\n5. Bookmark projects as **'Saved'** or track execution with **'In Progress'** and **'Completed'** status buttons.",
    links: [{ label: "Explore AI Projects", to: "/projects", icon: "🚀" }],
  },
  {
    keywords: ["trainer", "personal trainer", "daily", "daily plan", "learning plan", "streak", "schedule"],
    response:
      "**AI Personal Trainer & Daily Roadmap:**\n\n1. Open the **Personal Trainer** (Module 15).\n2. Generate a custom day-by-day learning plan based on your target role and available daily hours.\n3. Work through today's structured **Theory**, **Practice**, and **Project** tasks.\n4. Easily mark tasks as complete or reschedule workloads.\n5. Receive automated morning briefings and evening progress summaries!",
    links: [{ label: "Open Personal Trainer", to: "/personal-trainer", icon: "🧠" }],
  },
  {
    keywords: ["coding", "code", "python", "sql", "dsa", "challenge", "sandbox", "algorithm"],
    response:
      "**In-Browser Coding Practice Sandbox:**\n\n1. Navigate to **Coding Practice**.\n2. Select a challenge (Two Sum, Binary Search, SQL Aggregations, etc.) filtered by Easy, Medium, or Hard.\n3. Write your solution in the browser with starter templates.\n4. Run your code against automated test cases in a sandboxed Pyodide/SQLite environment.\n5. Request AI hints if you get stuck!",
    links: [{ label: "Start Coding Practice", to: "/coding", icon: "💻" }],
  },
  {
    keywords: ["company", "company prep", "google", "amazon", "microsoft", "meta", "target company", "strategy"],
    response:
      "**Company-Specific Interview Prep:**\n\n1. Go to **Company Preparation**.\n2. Enter the company name (e.g. Amazon, Google, Microsoft, Adobe) and target job role.\n3. The AI generates core required competencies, system architecture priorities, behavioral questions, and practice scenarios customized for that organization.",
    links: [{ label: "Company Prep Studio", to: "/company-preparation", icon: "🏢" }],
  },
  {
    keywords: ["email", "notification", "mail", "gmail", "smtp", "reminders", "alert"],
    response:
      "**Email Notifications & Settings:**\n\n1. Go to **Notification Preferences** to toggle reminder types (Roadmap, Mock Interviews, Coding).\n2. Real emails are sent for task completions, morning daily briefings, and evening check-ins.\n3. Configure your SMTP in `.env` (using your Gmail Address + Google App Password) to receive all notifications directly in your personal Gmail inbox!",
    links: [{ label: "Notification Preferences", to: "/notifications/preferences", icon: "⚙️" }],
  },
  {
    keywords: ["roadmap", "milestone", "career path", "phases"],
    response:
      "**Career Roadmap & Learning Milestones:**\n\n1. Go to **Career Roadmap**.\n2. Generate an actionable, phase-by-phase curriculum tailored to your target occupation.\n3. Track your overall completion percentage as you master each core milestone.",
    links: [{ label: "View Career Roadmap", to: "/roadmap", icon: "🗺️" }],
  },
  {
    keywords: ["resource", "courses", "learning", "youtube", "docs", "tutorials", "freecodecamp"],
    response:
      "**Curated Learning Resources:**\n\n1. Visit **Learning Hub**.\n2. Search verified tutorials, YouTube courses, and official documentation filtered by skill name and difficulty.\n3. Bookmark resources or filter by 'Missing Skill Gaps' to accelerate targeted learning.",
    links: [{ label: "Browse Learning Hub", to: "/learning-resources", icon: "📖" }],
  },
  {
    keywords: ["question bank", "questions", "interview questions", "dsa questions", "hr questions"],
    response:
      "**Question Bank & Bookmarks:**\n\n1. Visit **Question Bank**.\n2. Filter hundreds of curated and AI-generated interview questions by Technical, Behavioral, and HR categories.\n3. Bookmark questions to build your personal revision bank for upcoming interviews.",
    links: [{ label: "Explore Question Bank", to: "/question-bank", icon: "📚" }],
  },
  {
    keywords: ["dashboard", "home", "stats", "readiness", "overview"],
    response:
      "**Placement Readiness Dashboard:**\n\n1. Go to your **Dashboard**.\n2. Check your overall **Placement Readiness Score**, resume status, interview performance progression, and pending daily roadmap items.",
    links: [{ label: "Go to Dashboard", to: "/dashboard", icon: "🏠" }],
  },
];

function getBotReply(userQuery: string): {
  text: string;
  links?: Array<{ label: string; to: string; icon?: string }>;
} {
  const query = userQuery.toLowerCase().trim();

  // Search Knowledge Base for keyword matches
  let bestMatch = null;
  let highestMatchCount = 0;

  for (const item of KNOWLEDGE_BASE) {
    let matchCount = 0;
    for (const kw of item.keywords) {
      if (query.includes(kw.toLowerCase())) {
        matchCount++;
      }
    }
    if (matchCount > highestMatchCount) {
      highestMatchCount = matchCount;
      bestMatch = item;
    }
  }

  if (bestMatch && highestMatchCount > 0) {
    return {
      text: bestMatch.response,
      links: bestMatch.links,
    };
  }

  // Helpful Guided Fallback
  return {
    text: `I'm your **Placement AI Platform Coach**! Here is how you can use the main features of our platform:\n\n• **📄 Resume Studio**: Upload your resume to calculate a 0–100% ATS score, get strengths, weaknesses, and keyword suggestions.\n• **💼 Jobs Hub**: Browse real-time listings, check resume-job match scores, and apply directly.\n• **🧠 Career Intelligence**: Paste external job descriptions to get match scores, tailored cover letters, and cold emails.\n• **🎙️ Mock Interview**: Practice speech and text interviews with instant AI scoring rubrics.\n• **🚀 Project Coach**: Generate multi-tiered portfolio projects to close your skill gaps.\n• **🧠 Personal Trainer**: Follow daily structured learning tasks and receive email briefings.\n\n*Click any quick shortcut below or ask a specific question!*`,
    links: [
      { label: "Resume Studio", to: "/resumes", icon: "📁" },
      { label: "Jobs Hub", to: "/jobs", icon: "💼" },
      { label: "Career Intelligence", to: "/career-intelligence", icon: "🧠" },
      { label: "Mock Interview", to: "/interview", icon: "🎙️" },
      { label: "Personal Trainer", to: "/personal-trainer", icon: "🧠" },
    ],
  };
}

export default function PlatformHelpChatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-msg",
      sender: "bot",
      text: "👋 Hi there! I'm your **AI Platform Assistant & Career Guide**.\n\nHow can I help you today? Ask me anything about how to use the site (e.g. *how to check resume score*, *how to apply to jobs*, *how to update profile*, etc.) or click a quick topic below!",
      links: [
        { label: "Check Resume ATS Score", to: "/resumes", icon: "📄" },
        { label: "Find & Apply to Jobs", to: "/jobs", icon: "💼" },
        { label: "Daily Personal Trainer", to: "/personal-trainer", icon: "🧠" },
      ],
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Listen to custom window events so other components (Navbar, buttons) can open the chatbot
  useEffect(() => {
    const handleOpenChat = () => setIsOpen(true);
    window.addEventListener("open-ai-coach-chat", handleOpenChat);
    return () => window.removeEventListener("open-ai-coach-chat", handleOpenChat);
  }, []);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isOpen, isTyping]);

  const handleSend = (textToSend?: string) => {
    const text = (textToSend || input).trim();
    if (!text) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: text,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);

    // Simulate natural AI thinking delay
    setTimeout(() => {
      const reply = getBotReply(text);
      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        text: reply.text,
        links: reply.links,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMessage]);
      setIsTyping(false);
    }, 450);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleLinkClick = (to: string) => {
    navigate(to);
  };

  const renderFormattedText = (text: string) => {
    // Process markdown-like formatting: **bold**, *italic*, • bullets
    const lines = text.split("\n");
    return lines.map((line, idx) => {
      const formatted = line;

      // Replace bold **text**
      const parts = formatted.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={idx} className={line === "" ? "h-2" : "leading-relaxed my-0.5"}>
          {parts.map((part, pIdx) => {
            if (part.startsWith("**") && part.endsWith("**")) {
              return (
                <strong key={pIdx} className="font-bold text-white">
                  {part.slice(2, -2)}
                </strong>
              );
            }
            if (part.startsWith("*") && part.endsWith("*")) {
              return (
                <em key={pIdx} className="text-surface-200/70 italic">
                  {part.slice(1, -1)}
                </em>
              );
            }
            return part;
          })}
        </p>
      );
    });
  };

  return (
    <>
      {/* Floating Chatbot Toggle Launcher Button — Ultra High Visibility & Prominence */}
      <div className="fixed bottom-6 right-6 z-[9999] flex flex-col items-end gap-2.5 select-none pointer-events-auto">
        
        {/* Floating Attention Callout Bubble when Chat is Closed */}
        {!isOpen && (
          <div 
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2.5 px-4 py-2 rounded-2xl bg-slate-900/95 border-2 border-brand-400 text-white shadow-[0_6px_30px_rgba(99,102,241,0.55)] cursor-pointer hover:scale-105 transition-all animate-bounce-subtle group"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping" />
            <span className="text-xs font-bold text-slate-100 group-hover:text-brand-300">
              Need help with Resume, Jobs or Prep? Click here! 👋
            </span>
          </div>
        )}

        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`flex items-center gap-3 px-5 py-3.5 rounded-full font-black text-xs text-white shadow-[0_0_35px_rgba(99,102,241,0.65)] hover:shadow-[0_0_50px_rgba(99,102,241,0.95)] transition-all duration-300 cursor-pointer border-2 active:scale-95 ${
            isOpen
              ? "bg-slate-900 border-brand-400 text-white rotate-0"
              : "bg-gradient-to-r from-brand-500 via-indigo-600 to-purple-600 border-white/80 hover:scale-105 ring-4 ring-brand-400/30"
          }`}
          title="Placement AI Help & Navigation Assistant"
          aria-label="Toggle Help Chatbot"
        >
          {isOpen ? (
            <>
              <svg className="w-5 h-5 text-brand-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
              <span className="tracking-wider uppercase font-black text-xs">Close Assistant</span>
            </>
          ) : (
            <>
              <div className="relative flex items-center justify-center">
                <span className="text-xl">🤖</span>
                <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-950 animate-ping" />
                <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-emerald-400 border-2 border-slate-950" />
              </div>
              <div className="flex flex-col text-left">
                <span className="tracking-wider uppercase font-black text-xs drop-shadow-md text-white">
                  Ask AI Platform Coach 💬
                </span>
                <span className="text-[10px] font-semibold text-brand-200/90 -mt-0.5">
                  Instant Q&A • Site Navigation
                </span>
              </div>
            </>
          )}
        </button>
      </div>

      {/* Interactive Chat Window — High Contrast & Clarity */}
      {isOpen && (
        <div className="fixed bottom-24 right-4 sm:right-6 z-[9999] w-[94vw] sm:w-[460px] max-h-[660px] h-[84vh] flex flex-col rounded-3xl bg-slate-950 border-2 border-brand-500/80 shadow-[0_0_80px_rgba(99,102,241,0.5)] overflow-hidden animate-slide-in-up">
          {/* Header */}
          <div className="p-4 bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-700 border-b border-white/20 flex items-center justify-between text-white shadow-lg">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-12 h-12 rounded-2xl bg-white/15 backdrop-blur-md flex items-center justify-center text-white font-black text-2xl shadow-inner border border-white/40">
                  🤖
                </div>
                <span className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-slate-950" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-black tracking-tight text-white">Placement AI Coach</h3>
                  <span className="px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-emerald-400/25 text-emerald-200 border border-emerald-400/50">
                    Online 24/7
                  </span>
                </div>
                <p className="text-[11px] text-white/90 font-semibold">How-to guide, feature walkthroughs & instant help</p>
              </div>
            </div>

            <div className="flex items-center gap-1.5">
              <button
                onClick={() =>
                  setMessages([
                    {
                      id: "cleared-msg",
                      sender: "bot",
                      text: "Conversation cleared! How can I help you navigate or use the platform?",
                      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    },
                  ])
                }
                className="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs transition-colors cursor-pointer"
                title="Clear Conversation"
              >
                🗑️
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
                title="Minimize Window"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs custom-scrollbar bg-slate-950">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
              >
                <div
                  className={`max-w-[92%] p-4 rounded-2xl space-y-2 shadow-xl ${
                    m.sender === "user"
                      ? "bg-gradient-to-r from-brand-600 to-indigo-600 text-white font-medium rounded-br-none"
                      : "bg-slate-900/95 border border-slate-700 text-slate-100 rounded-bl-none shadow-black/40"
                  }`}
                >
                  <div className="text-xs space-y-1.5 leading-relaxed text-slate-100 font-normal">
                    {renderFormattedText(m.text)}
                  </div>

                  {/* Interactive Deep Links */}
                  {m.links && m.links.length > 0 && (
                    <div className="pt-2.5 flex flex-wrap gap-2 border-t border-slate-700/80 mt-2">
                      {m.links.map((link, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleLinkClick(link.to)}
                          className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-bold text-xs border border-white/25 hover:border-white/50 transition-all cursor-pointer flex items-center gap-1.5 shadow-md hover:shadow-brand-500/50 active:scale-95"
                        >
                          {link.icon && <span>{link.icon}</span>}
                          <span>{link.label} →</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-[10px] text-slate-400 font-semibold px-1 mt-1">{m.timestamp}</span>
              </div>
            ))}

            {isTyping && (
              <div className="flex items-center gap-2 p-3.5 rounded-2xl bg-slate-900 border border-slate-700 w-fit">
                <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 rounded-full bg-brand-400 animate-bounce [animation-delay:0.4s]" />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Topic Chips */}
          <div className="px-3 py-2.5 bg-slate-900 border-t border-slate-800 overflow-x-auto custom-scrollbar flex items-center gap-2 shrink-0">
            <span className="text-[10px] text-brand-300 font-black uppercase whitespace-nowrap pl-1 mr-0.5">
              💡 Quick Help:
            </span>
            {QUICK_TOPICS.map((topic, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(topic.query)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-brand-600 text-slate-100 hover:text-white text-xs font-bold border border-slate-700 hover:border-brand-400 whitespace-nowrap transition-all cursor-pointer shrink-0 active:scale-95 shadow-sm"
              >
                {topic.icon} {topic.label}
              </button>
            ))}
          </div>

          {/* Text Input Area */}
          <div className="p-3.5 bg-slate-900 border-t border-slate-800 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything (e.g., 'How to check resume score?')..."
              className="flex-1 bg-slate-950 border-2 border-slate-700 focus:border-brand-500 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-400 outline-none transition-all shadow-inner"
            />

            <button
              onClick={() => handleSend()}
              disabled={!input.trim()}
              className="px-4 py-2.5 rounded-xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 disabled:opacity-40 text-white font-bold shadow-lg shadow-brand-600/40 transition-all cursor-pointer flex items-center justify-center gap-1.5 shrink-0"
              title="Send Message"
            >
              <span>Ask</span>
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
