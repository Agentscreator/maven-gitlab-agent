import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Hexagon, Mail, Briefcase, Shield, Search, Newspaper, ArrowRight, Send, Bot, Radar, Reply, DollarSign, MapPin, Calendar, UserPlus, Twitter, GitMerge } from "lucide-react";
import TopBar from "@/components/TopBar";
import type { LucideIcon } from "lucide-react";
import { agentsApi } from "@/api/agents";
import type { DiscoverEntry } from "@/api/types";

// --- Icon and color maps (backend can't serve icons) ---

const AGENT_ICONS: Record<string, LucideIcon> = {
  email_inbox_management: Mail,
  job_hunter: Briefcase,
  vulnerability_assessment: Shield,
  deep_research_agent: Search,
  tech_news_reporter: Newspaper,
  competitive_intel_agent: Radar,
  email_reply_agent: Reply,
  hubspot_revenue_leak_detector: DollarSign,
  local_business_extractor: MapPin,
  meeting_scheduler: Calendar,
  sdr_agent: UserPlus,
  twitter_news_agent: Twitter,
};

const AGENT_COLORS: Record<string, string> = {
  email_inbox_management: "hsl(38,80%,55%)",
  job_hunter: "hsl(30,85%,58%)",
  vulnerability_assessment: "hsl(15,70%,52%)",
  deep_research_agent: "hsl(210,70%,55%)",
  tech_news_reporter: "hsl(270,60%,55%)",
  competitive_intel_agent: "hsl(190,70%,45%)",
  email_reply_agent: "hsl(45,80%,55%)",
  hubspot_revenue_leak_detector: "hsl(145,60%,42%)",
  local_business_extractor: "hsl(350,65%,55%)",
  meeting_scheduler: "hsl(220,65%,55%)",
  sdr_agent: "hsl(165,55%,45%)",
  twitter_news_agent: "hsl(200,85%,55%)",
};

function agentSlug(path: string): string {
  return path.replace(/\/$/, "").split("/").pop() || path;
}

// --- Generic prompt hints (not tied to specific agents) ---

const promptHints = [
  "Fix the failing pipeline in my GitLab project",
  "Triage open issues and assign to the right owners",
  "Scan for vulnerabilities and open a patch MR",
  "Review open MRs for compliance violations",
];

export default function Home() {
  const navigate = useNavigate();
  const [inputValue, setInputValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showAgents, setShowAgents] = useState(false);
  const [agents, setAgents] = useState<DiscoverEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch agents on mount so data is ready when user toggles
  useEffect(() => {
    setLoading(true);
    agentsApi
      .discover()
      .then((result) => {
        const examples = result["Examples"] || [];
        setAgents(examples);
      })
      .catch((err) => {
        setError(err.message || "Failed to load agents");
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const handleSelect = (agentPath: string) => {
    navigate(`/workspace?agent=${encodeURIComponent(agentPath)}`);
  };

  const handlePromptHint = (text: string) => {
    navigate(`/workspace?agent=new-agent&prompt=${encodeURIComponent(text)}`);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      navigate(`/workspace?agent=new-agent&prompt=${encodeURIComponent(inputValue.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <TopBar />

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-2xl">
          {/* Maven greeting */}
          <div className="text-center mb-10">
            <div
              className="inline-flex w-14 h-14 rounded-2xl items-center justify-center mb-5"
              style={{
                background: "linear-gradient(135deg, hsl(28,60%,18%,0.6) 0%, hsl(20,8%,10%,0.8) 100%)",
                border: "1.5px solid hsl(28,82%,54%,0.3)",
                boxShadow: "0 0 32px hsl(28,82%,54%,0.12), 0 0 8px hsl(28,82%,54%,0.06)",
              }}
            >
              <Hexagon className="w-7 h-7 text-primary" />
            </div>
            <h1 className="text-2xl font-bold tracking-tight text-foreground mb-2">
              What needs to be done?
            </h1>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto leading-relaxed">
              Maven's Queen coordinates a swarm of DevSecOps workers that watch and fix your GitLab projects — automatically.
            </p>
          </div>

          {/* Chat input */}
          <form onSubmit={handleSubmit} className="mb-6">
            <div
              className="relative rounded-xl transition-all duration-200"
              style={{
                background: "hsl(20 8% 7% / 0.9)",
                border: "1px solid hsl(20 10% 14%)",
                boxShadow: "0 1px 0 hsl(30 20% 30% / 0.05) inset, 0 4px 20px hsl(20 8% 2% / 0.35)",
              }}
              onFocus={() => {}}
            >
              <textarea
                ref={textareaRef}
                rows={1}
                value={inputValue}
                onChange={(e) => {
                  setInputValue(e.target.value);
                  const ta = e.target;
                  ta.style.height = "auto";
                  ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="Describe a DevSecOps task for Maven..."
                className="w-full bg-transparent px-5 py-4 pr-14 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none rounded-xl resize-none overflow-y-auto"
              />
              <div className="absolute right-3 bottom-2.5">
                <button
                  type="submit"
                  disabled={!inputValue.trim()}
                  className="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-150 disabled:opacity-25 disabled:cursor-not-allowed"
                  style={{
                    background: "linear-gradient(135deg, hsl(28,82%,60%) 0%, hsl(22,75%,48%) 100%)",
                    boxShadow: inputValue.trim() ? "0 2px 8px hsl(28,82%,54%,0.35)" : "none",
                    color: "hsl(20 8% 4%)",
                  }}
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </form>

          {/* Action buttons */}
          <div className="flex items-center justify-center gap-3 mb-6">
            <button
              onClick={() => setShowAgents(!showAgents)}
              className="inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition-all duration-150"
              style={{
                background: "hsl(20 8% 8% / 0.8)",
                border: "1px solid hsl(20 10% 16%)",
                color: "hsl(25 10% 52%)",
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(28 82% 54% / 0.35)";
                (e.currentTarget as HTMLButtonElement).style.color = "hsl(30 15% 82%)";
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(20 10% 16%)";
                (e.currentTarget as HTMLButtonElement).style.color = "hsl(25 10% 52%)";
              }}
            >
              <GitMerge className="w-4 h-4 text-primary/60" />
              <span>Try a sample worker</span>
              <ArrowRight className={`w-3.5 h-3.5 transition-transform duration-200 ${showAgents ? "rotate-90" : ""}`} />
            </button>
            <button
              onClick={() => navigate("/my-agents")}
              className="inline-flex items-center gap-2 text-sm font-medium px-4 py-2 rounded-lg transition-all duration-150"
              style={{
                background: "hsl(20 8% 8% / 0.8)",
                border: "1px solid hsl(20 10% 16%)",
                color: "hsl(25 10% 52%)",
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(28 82% 54% / 0.35)";
                (e.currentTarget as HTMLButtonElement).style.color = "hsl(30 15% 82%)";
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(20 10% 16%)";
                (e.currentTarget as HTMLButtonElement).style.color = "hsl(25 10% 52%)";
              }}
            >
              <Bot className="w-4 h-4 text-primary/60" />
              <span>My Workers</span>
            </button>
          </div>

          {/* Prompt hint pills */}
          <div className="flex flex-wrap justify-center gap-2 mb-6">
            {promptHints.map((hint) => (
              <button
                key={hint}
                onClick={() => handlePromptHint(hint)}
                className="text-xs rounded-full px-3.5 py-1.5 transition-all duration-150"
                style={{
                  color: "hsl(25 10% 48%)",
                  border: "1px solid hsl(20 10% 14%)",
                  background: "hsl(20 8% 7% / 0.6)",
                }}
                onMouseEnter={e => {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(28 82% 54% / 0.3)";
                  (e.currentTarget as HTMLButtonElement).style.color = "hsl(30 15% 78%)";
                }}
                onMouseLeave={e => {
                  (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(20 10% 14%)";
                  (e.currentTarget as HTMLButtonElement).style.color = "hsl(25 10% 48%)";
                }}
              >
                {hint}
              </button>
            ))}
          </div>

          {/* Agent cards — revealed on toggle */}
          {showAgents && (
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
              {loading && (
                <div className="text-center py-8 text-sm text-muted-foreground">Loading agents...</div>
              )}
              {error && (
                <div className="text-center py-8 text-sm text-destructive">{error}</div>
              )}
              {!loading && !error && agents.length === 0 && (
                <div className="text-center py-8 text-sm text-muted-foreground">No sample agents found.</div>
              )}
              {!loading && !error && agents.length > 0 && (
                <div className="grid grid-cols-3 gap-3">
                  {agents.map((agent) => {
                    const slug = agentSlug(agent.path);
                    const Icon = AGENT_ICONS[slug] || Hexagon;
                    const color = AGENT_COLORS[slug] || "hsl(45,95%,58%)";
                    return (
                      <button
                        key={agent.path}
                        onClick={() => handleSelect(agent.path)}
                        className="text-left rounded-xl p-4 transition-all duration-200 group relative overflow-hidden h-full flex flex-col"
                        style={{
                          background: "hsl(20 8% 7% / 0.8)",
                          border: "1px solid hsl(20 10% 14%)",
                          boxShadow: "0 1px 0 hsl(30 20% 30% / 0.04) inset",
                        }}
                        onMouseEnter={e => {
                          (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(28 82% 54% / 0.28)";
                          (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 1px 0 hsl(30 20% 30% / 0.04) inset, 0 4px 20px hsl(28 82% 54% / 0.06)";
                        }}
                        onMouseLeave={e => {
                          (e.currentTarget as HTMLButtonElement).style.borderColor = "hsl(20 10% 14%)";
                          (e.currentTarget as HTMLButtonElement).style.boxShadow = "0 1px 0 hsl(30 20% 30% / 0.04) inset";
                        }}
                      >
                        <div className="flex flex-col flex-1">
                          <div className="flex items-center gap-3 mb-2.5">
                            <div
                              className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                              style={{
                                backgroundColor: `${color}15`,
                                border: `1.5px solid ${color}30`,
                              }}
                            >
                              <Icon className="w-4 h-4" style={{ color }} />
                            </div>
                            <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                              {agent.name}
                            </h3>
                          </div>
                          <p className="text-xs text-muted-foreground leading-relaxed mb-3 line-clamp-2">
                            {agent.description}
                          </p>
                          <div className="flex gap-1.5 flex-wrap mt-auto">
                            {agent.tags.length > 0 ? (
                              agent.tags.map((tag) => (
                                <span
                                  key={tag}
                                  className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground"
                                >
                                  {tag}
                                </span>
                              ))
                            ) : (
                              <>
                                {agent.node_count > 0 && (
                                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground">
                                    {agent.node_count} nodes
                                  </span>
                                )}
                                {agent.tool_count > 0 && (
                                  <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-muted/60 text-muted-foreground">
                                    {agent.tool_count} tools
                                  </span>
                                )}
                              </>
                            )}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
