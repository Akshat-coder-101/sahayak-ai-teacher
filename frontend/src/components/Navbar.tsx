"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { 
  Sparkles, 
  BookOpen, 
  UploadCloud, 
  User, 
  Compass, 
  LayoutDashboard, 
  Search, 
  LogOut, 
  ChevronDown, 
  Menu,
  X,
  GraduationCap
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useAuth, PRESET_USERS } from "@/context/AuthContext";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, switchUser, isAuthenticated } = useAuth();
  
  const [searchQuery, setSearchQuery] = useState("");
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  
  const dropdownRef = useRef<HTMLDivElement>(null);
  const mobileMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click or ESC
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsProfileOpen(false);
      }
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target as Node)) {
        // Only close if click is not on hamburger button
        const target = event.target as HTMLElement;
        if (!target.closest("#mobile-menu-btn")) {
          setIsMobileMenuOpen(false);
        }
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsProfileOpen(false);
        setIsMobileMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
    setIsProfileOpen(false);
  }, [pathname]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    router.push(`/learning-path/${encodeURIComponent(searchQuery.trim().toLowerCase().replace(/\s+/g, "-"))}`);
    setSearchQuery("");
    setIsMobileMenuOpen(false);
  };

  const navLinks = [
    { href: "/upload", label: "Upload Material", icon: UploadCloud },
    { href: "/topic", label: "Explore Topics", icon: BookOpen },
    { href: "/learning-path", label: "Learning Paths", icon: Compass },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-border h-16 shadow-2xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-full flex items-center justify-between gap-3">
        {/* Left: Brand Logo & Hamburger */}
        <div className="flex items-center gap-3 sm:gap-6 shrink-0">
          {/* Mobile Hamburger Button */}
          <button
            id="mobile-menu-btn"
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2.5 rounded-lg text-ink-secondary hover:text-black hover:bg-canvas-elevated border border-border min-h-[44px] min-w-[44px] flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-primary"
            aria-expanded={isMobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          <Link href="/" className="flex items-center gap-2 group min-h-[44px] py-1">
            <div className="w-8 h-8 rounded bg-primary text-white flex items-center justify-center font-black text-lg shadow-2xs group-hover:scale-105 transition-transform">
              S
            </div>
            <span className="font-extrabold text-xl tracking-tight text-primary">
              sahayak
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const isActive = pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-3 py-2 rounded text-sm font-semibold transition-colors min-h-[44px] flex items-center ${
                    isActive
                      ? "text-primary bg-primary-soft font-bold"
                      : "text-ink-secondary hover:text-primary hover:bg-canvas-elevated"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Center: Global Dynamic Search & DAG Generator (Desktop) */}
        <form onSubmit={handleSearchSubmit} className="hidden lg:flex flex-1 max-w-sm mx-4">
          <div className="relative w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search or generate curriculum path..."
              className="w-full text-xs pl-9 pr-3 py-2 rounded bg-white border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all font-medium min-h-[40px]"
            />
          </div>
        </form>

        {/* Right: User Authentication, Profile Dropdown & Primary Action */}
        <div className="flex items-center gap-2.5 sm:gap-3 shrink-0">
          {isAuthenticated && user ? (
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-canvas-elevated transition-colors border border-transparent hover:border-border min-h-[44px]"
                aria-expanded={isProfileOpen}
                aria-label="User profile options"
              >
                <div className="relative w-8 h-8 rounded-full overflow-hidden border border-border shrink-0">
                  <Image
                    src={user.avatar}
                    alt={user.name}
                    width={32}
                    height={32}
                    className="w-full h-full object-cover"
                    unoptimized
                  />
                </div>
                <div className="hidden sm:block text-left">
                  <span className="text-xs font-bold text-black block truncate max-w-[120px]">
                    {user.name}
                  </span>
                  <span className="text-[10px] text-primary font-semibold uppercase font-mono">
                    {user.level}
                  </span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-ink-muted" />
              </button>

              {/* Profile Dropdown Menu */}
              {isProfileOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl border border-border shadow-xl py-2 z-50 animate-in fade-in duration-150">
                  <div className="px-4 py-2.5 border-b border-border">
                    <p className="text-xs font-bold text-black">{user.name}</p>
                    <a
                      href={`mailto:${user.email}`}
                      className="text-[11px] text-ink-muted hover:text-primary transition-colors truncate block"
                    >
                      {user.email}
                    </a>
                    <span className="inline-block mt-1 text-[10px] px-2 py-0.5 rounded bg-[#E9F1FC] text-primary font-bold capitalize">
                      {user.level} Cognitive Tier
                    </span>
                  </div>

                  <div className="py-1">
                    <Link
                      href="/profile"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-2 px-4 py-2.5 text-xs text-ink-secondary hover:bg-canvas-elevated hover:text-black transition-colors"
                    >
                      <User className="w-3.5 h-3.5 text-primary" />
                      <span>Learner Profile</span>
                    </Link>
                    <Link
                      href="/dashboard"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-2 px-4 py-2.5 text-xs text-ink-secondary hover:bg-canvas-elevated hover:text-black transition-colors"
                    >
                      <LayoutDashboard className="w-3.5 h-3.5 text-[#0F7B3F]" />
                      <span>Progress Analytics</span>
                    </Link>
                    <Link
                      href="/learning-path"
                      onClick={() => setIsProfileOpen(false)}
                      className="flex items-center gap-2 px-4 py-2.5 text-xs text-ink-secondary hover:bg-canvas-elevated hover:text-black transition-colors"
                    >
                      <Compass className="w-3.5 h-3.5 text-accent" />
                      <span>Curriculum DAG</span>
                    </Link>
                  </div>

                  {/* Switch Persona Shortcuts */}
                  <div className="border-t border-border pt-2 pb-1 px-4">
                    <span className="text-[10px] uppercase font-bold text-ink-muted block mb-1">
                      Quick Switch Persona:
                    </span>
                    <div className="space-y-1">
                      {PRESET_USERS.map((p) => (
                        <button
                          key={p.id}
                          onClick={() => {
                            switchUser(p);
                            setIsProfileOpen(false);
                          }}
                          className={`w-full text-left text-xs py-1.5 px-2 rounded flex items-center justify-between transition-colors ${
                            user.id === p.id ? "bg-[#E9F1FC] text-primary font-bold" : "text-ink-secondary hover:bg-canvas-elevated"
                          }`}
                        >
                          <span className="truncate">{p.name.split(" ")[0]} ({p.level})</span>
                          {user.id === p.id && <span className="text-[10px] text-primary font-bold font-mono">Active</span>}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="border-t border-border pt-1">
                    <button
                      onClick={() => {
                        logout();
                        setIsProfileOpen(false);
                      }}
                      className="w-full flex items-center gap-2 px-4 py-2.5 text-xs text-[#C21E1E] hover:bg-rose-50 transition-colors font-semibold"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="text-sm font-semibold text-black hover:text-primary transition-colors min-h-[44px] flex items-center px-2"
            >
              Log In
            </Link>
          )}

          {/* Black Primary CTA Button */}
          <Link
            href="/topic"
            className="flex items-center gap-1.5 px-3.5 sm:px-4 py-2 rounded-lg bg-black hover:bg-neutral-800 text-white text-xs font-bold transition-all shadow-2xs hover:scale-[1.01] active:scale-[0.99] min-h-[44px]"
          >
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span className="hidden sm:inline">Start Free Lesson</span>
            <span className="sm:hidden">Start</span>
          </Link>
        </div>
      </div>

      {/* Mobile Drawer / Dropdown Menu */}
      {isMobileMenuOpen && (
        <div
          ref={mobileMenuRef}
          className="md:hidden bg-white border-b border-border shadow-xl px-4 py-4 space-y-4 animate-in slide-in-from-top-2 duration-150"
        >
          {/* Mobile Search Input */}
          <form onSubmit={handleSearchSubmit} className="w-full">
            <div className="relative w-full">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search curriculum topic..."
                className="w-full text-xs pl-9 pr-3 py-2.5 rounded-lg bg-canvas-elevated border border-border text-black placeholder-ink-muted focus:outline-none focus:border-primary font-medium min-h-[44px]"
              />
            </div>
          </form>

          {/* Mobile Links */}
          <nav className="flex flex-col gap-1">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3.5 py-3 rounded-lg text-sm font-semibold transition-colors min-h-[44px] ${
                    isActive
                      ? "text-primary bg-primary-soft font-bold"
                      : "text-ink-primary hover:bg-canvas-elevated"
                  }`}
                >
                  <Icon className="w-4 h-4 text-primary" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      )}
    </header>
  );
}
