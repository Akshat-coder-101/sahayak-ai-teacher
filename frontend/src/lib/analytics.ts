export interface RecordedSession {
  topic: string;
  domain?: string;
  score: number;
  timeMinutes: number;
  misconceptionsCount: number;
  status: string;
  date: string;
}

export interface WeeklyActivityPoint {
  day: string;
  score: number;
}

export interface DomainCompetency {
  subject: string;
  pct: number;
  color: string;
}

export interface UserAnalytics {
  totalStudyMinutes: number;
  averageScore: number;
  nodesMastered: number;
  misconceptionsResolved: number;
  recentSessions: RecordedSession[];
  weeklyActivity: WeeklyActivityPoint[];
  domainCompetencies: DomainCompetency[];
}

const STORAGE_KEY_PREFIX = "sahayak_analytics_";

function getSubjectForTopic(topic: string): string {
  const lower = topic.toLowerCase();
  if (lower.includes("physics") || lower.includes("quantum") || lower.includes("gravity") || lower.includes("motion") || lower.includes("energy")) return "Physics";
  if (lower.includes("math") || lower.includes("calculus") || lower.includes("algebra") || lower.includes("geometry")) return "Mathematics";
  if (lower.includes("bio") || lower.includes("cell") || lower.includes("gene") || lower.includes("organ")) return "Biology";
  if (lower.includes("chem") || lower.includes("reaction") || lower.includes("atom") || lower.includes("molecule")) return "Chemistry";
  if (lower.includes("code") || lower.includes("python") || lower.includes("algorithm") || lower.includes("cs") || lower.includes("computer")) return "Computer Science";
  return "General STEM";
}

export function getUserAnalytics(userId: string): UserAnalytics {
  if (typeof window === "undefined") {
    return getEmptyAnalytics();
  }

  try {
    const raw = localStorage.getItem(`${STORAGE_KEY_PREFIX}${userId}`);
    const sessions: RecordedSession[] = raw ? JSON.parse(raw) : [];

    if (!sessions || sessions.length === 0) {
      return getEmptyAnalytics();
    }

    const totalStudyMinutes = sessions.reduce((acc, s) => acc + (s.timeMinutes || 15), 0);
    const avgScore = Math.round(sessions.reduce((acc, s) => acc + s.score, 0) / sessions.length);
    const misconceptionsResolved = sessions.reduce((acc, s) => acc + (s.misconceptionsCount || 0), 0);
    const nodesMastered = sessions.filter((s) => s.score >= 60).length;

    const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const weeklyActivity: WeeklyActivityPoint[] = days.map((day, idx) => {
      const match = sessions[idx % sessions.length];
      return {
        day,
        score: match ? match.score : 0,
      };
    });

    const domainCounts: Record<string, { totalScore: number; count: number }> = {};
    sessions.forEach((s) => {
      const domain = s.domain || getSubjectForTopic(s.topic);
      if (!domainCounts[domain]) {
        domainCounts[domain] = { totalScore: 0, count: 0 };
      }
      domainCounts[domain].totalScore += s.score;
      domainCounts[domain].count += 1;
    });

    const colors = ["bg-[#0056D2]", "bg-[#0F7B3F]", "bg-[#B45309]", "bg-[#7C3AED]", "bg-[#DB2777]"];
    const domainCompetencies: DomainCompetency[] = Object.keys(domainCounts).map((subj, i) => ({
      subject: subj,
      pct: Math.round(domainCounts[subj].totalScore / domainCounts[subj].count),
      color: colors[i % colors.length],
    }));

    return {
      totalStudyMinutes,
      averageScore: avgScore,
      nodesMastered,
      misconceptionsResolved,
      recentSessions: sessions.map((s) => ({
        ...s,
        domain: s.domain || getSubjectForTopic(s.topic),
      })),
      weeklyActivity,
      domainCompetencies,
    };
  } catch (e) {
    console.error("Failed to load analytics:", e);
    return getEmptyAnalytics();
  }
}

export function recordSessionCompletion(userId: string, session: RecordedSession): void {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem(`${STORAGE_KEY_PREFIX}${userId}`);
    const existing: RecordedSession[] = raw ? JSON.parse(raw) : [];
    const domain = session.domain || getSubjectForTopic(session.topic);
    const updated = [{ ...session, domain }, ...existing].slice(0, 50);
    localStorage.setItem(`${STORAGE_KEY_PREFIX}${userId}`, JSON.stringify(updated));
  } catch (e) {
    console.error("Failed to record session completion:", e);
  }
}

export function clearUserSessions(userId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(`${STORAGE_KEY_PREFIX}${userId}`);
  } catch (e) {
    console.error("Failed to clear sessions:", e);
  }
}

function getEmptyAnalytics(): UserAnalytics {
  return {
    totalStudyMinutes: 0,
    averageScore: 0,
    nodesMastered: 0,
    misconceptionsResolved: 0,
    recentSessions: [],
    weeklyActivity: [
      { day: "Mon", score: 0 },
      { day: "Tue", score: 0 },
      { day: "Wed", score: 0 },
      { day: "Thu", score: 0 },
      { day: "Fri", score: 0 },
      { day: "Sat", score: 0 },
      { day: "Sun", score: 0 },
    ],
    domainCompetencies: [],
  };
}
