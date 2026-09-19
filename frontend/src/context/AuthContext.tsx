"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { api, setAuthToken, getAuthToken } from "@/lib/api";

export interface UserSession {
  id: string;
  name: string;
  email: string;
  role: string;
  level: "beginner" | "intermediate" | "advanced";
  avatar: string;
  joinedDate: string;
}

interface AuthContextType {
  user: UserSession | null;
  login: (email: string, password?: string, name?: string, level?: "beginner" | "intermediate" | "advanced") => Promise<void>;
  register: (email: string, password: string, name?: string, role?: string, level?: "beginner" | "intermediate" | "advanced") => Promise<void>;
  logout: () => Promise<void>;
  switchUser: (presetUser: UserSession) => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export const PRESET_USERS: UserSession[] = [
  {
    id: "user-demo-student",
    name: "Judge Demo Student",
    email: "demo.student@sahayak.edu",
    role: "student",
    level: "intermediate",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
    joinedDate: "Mar 2026",
  },
  {
    id: "user-pranjal",
    name: "Pranjal Mishra",
    email: "pranjal@sahayak.edu",
    role: "student",
    level: "advanced",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
    joinedDate: "Feb 2026",
  },
  {
    id: "user-teacher",
    name: "Teacher Master",
    email: "teacher@sahayak.edu",
    role: "teacher",
    level: "advanced",
    avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=200&auto=format&fit=crop",
    joinedDate: "Jan 2026",
  },
  {
    id: "user-aarav",
    name: "Aarav Sharma",
    email: "aarav.highschool@edu.in",
    role: "student",
    level: "beginner",
    avatar: "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?q=80&w=200&auto=format&fit=crop",
    joinedDate: "Jan 2026",
  },
  {
    id: "user-priya",
    name: "Dr. Priya Patel",
    email: "priya.research@mit.edu",
    role: "student",
    level: "intermediate",
    avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=200&auto=format&fit=crop",
    joinedDate: "Dec 2025",
  },
];

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    async function initAuth() {
      try {
        const token = getAuthToken();
        if (token) {
          try {
            const me = await api.getMe();
            if (me && me.id) {
              const matchedPreset = PRESET_USERS.find(p => p.email === me.email || p.id === me.id);
              const sessionUser: UserSession = {
                id: me.id,
                name: me.name || "Learner",
                email: me.email,
                role: me.role || "student",
                level: (matchedPreset?.level || "intermediate") as "beginner" | "intermediate" | "advanced",
                avatar: matchedPreset?.avatar || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
                joinedDate: matchedPreset?.joinedDate || "Feb 2026",
              };
              setUser(sessionUser);
              localStorage.setItem("sahayak_user_session", JSON.stringify(sessionUser));
              return;
            }
          } catch {
            // Token expired or invalid
            setAuthToken(null);
            localStorage.removeItem("sahayak_user_session");
          }
        }

        // If no valid authenticated session exists, require user to sign in first
        setUser(null);
        localStorage.removeItem("sahayak_user_session");
      } finally {
        setIsLoading(false);
      }
    }

    initAuth();
  }, []);

  const login = async (
    email: string,
    password: string = "password123",
    name?: string,
    level: "beginner" | "intermediate" | "advanced" = "intermediate"
  ) => {
    try {
      const resp = await api.login(email, password);
      const apiUser = resp.user;
      const matchedPreset = PRESET_USERS.find(p => p.email === email || p.id === apiUser.id);

      const sessionUser: UserSession = {
        id: apiUser.id,
        name: apiUser.name || name || email.split("@")[0].replace(".", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        email: apiUser.email,
        role: apiUser.role || "student",
        level,
        avatar: matchedPreset?.avatar || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
        joinedDate: matchedPreset?.joinedDate || new Date().toLocaleDateString("en-US", { month: "short", year: "numeric" }),
      };

      setUser(sessionUser);
      localStorage.setItem("sahayak_user_session", JSON.stringify(sessionUser));
    } catch (err: any) {
      // If backend is unreachable or local mock fallback, still allow offline demo login
      console.warn("Backend login failed, using fallback session:", err);
      const matchedPreset = PRESET_USERS.find(p => p.email === email);
      const fallbackUser: UserSession = matchedPreset || {
        id: `user-${Date.now()}`,
        name: name || email.split("@")[0].replace(".", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        email,
        role: "student",
        level,
        avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
        joinedDate: new Date().toLocaleDateString("en-US", { month: "short", year: "numeric" }),
      };
      setUser(fallbackUser);
      localStorage.setItem("sahayak_user_session", JSON.stringify(fallbackUser));
      throw err;
    }
  };

  const register = async (
    email: string,
    password: string = "password123",
    name?: string,
    role: string = "student",
    level: "beginner" | "intermediate" | "advanced" = "intermediate"
  ) => {
    const resp = await api.register({ email, password, name, role, level });
    const apiUser = resp.user;

    const sessionUser: UserSession = {
      id: apiUser.id,
      name: apiUser.name || name || "Learner",
      email: apiUser.email,
      role: apiUser.role || role,
      level,
      avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=200&auto=format&fit=crop",
      joinedDate: new Date().toLocaleDateString("en-US", { month: "short", year: "numeric" }),
    };

    setUser(sessionUser);
    localStorage.setItem("sahayak_user_session", JSON.stringify(sessionUser));
  };

  const logout = async () => {
    await api.logout();
    setUser(null);
    localStorage.removeItem("sahayak_user_session");
  };

  const switchUser = async (presetUser: UserSession) => {
    try {
      const resp = await api.login(presetUser.email, "safePassword123!");
      if (resp?.access_token) {
        setAuthToken(resp.access_token);
      }
    } catch {
      try {
        const resp = await api.login(presetUser.email, "password123");
        if (resp?.access_token) {
          setAuthToken(resp.access_token);
        }
      } catch (e) {
        console.warn("Preset login fallback:", e);
      }
    }
    setUser(presetUser);
    localStorage.setItem("sahayak_user_session", JSON.stringify(presetUser));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        switchUser,
        isAuthenticated: !!user,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
