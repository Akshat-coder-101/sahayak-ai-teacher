"use client";

import React, { useState, useEffect } from "react";
import Image from "next/image";
import { api, RelatedVideo, RelatedVideosResponse } from "@/lib/api";
import { CollapsibleDisclosure } from "./ui";
import { usePrefersReducedMotion } from "./ui/use-reduced-motion";
import { 
  Tv, 
  Play, 
  ExternalLink, 
  Search, 
  Sparkles, 
  Clock, 
  AlertCircle,
  Video
} from "lucide-react";

interface RelatedVideosProps {
  topic: string;
  language?: string;
  segmentId?: number;
  sessionId?: string;
  context?: string;
}

export default function RelatedVideos({
  topic,
  language = "en",
  segmentId,
  sessionId,
  context,
}: RelatedVideosProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasFetched, setHasFetched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<RelatedVideosResponse | null>(null);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const prefersReducedMotion = usePrefersReducedMotion();

  // Lazy fetch triggered only upon opening the disclosure
  useEffect(() => {
    if (isOpen && !hasFetched) {
      setHasFetched(true);
      setIsLoading(true);
      setError(null);
      
      api.getRelatedVideos(topic, language, {
        segment_id: segmentId,
        session_id: sessionId,
        context,
      })
        .then((res) => {
          setData(res);
        })
        .catch((err: any) => {
          setError(err.message || "Unable to load video recommendations.");
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [isOpen, hasFetched, topic, language, segmentId, sessionId, context]);

  // Reset fetch state if topic or language change
  useEffect(() => {
    setHasFetched(false);
    setData(null);
    setActiveVideoId(null);
    setError(null);
  }, [topic, language]);

  const searchUrl = data?.search_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(topic)}`;

  return (
    <div className="w-full mt-4">
      <CollapsibleDisclosure
        title="Curated Video Explanations"
        subtitle="Real, embeddable YouTube deep-dives with zero hallucinations"
        icon={<Tv className="w-4 h-4 text-primary" />}
        badge="YouTube Data API"
        variant="bordered"
        defaultOpen={false}
        onToggle={(open) => setIsOpen(open)}
      >
        <div className="space-y-4 pt-1">
          {/* Loading Skeleton */}
          {isLoading && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className={`bg-canvas-elevated rounded-lg border border-border p-3 space-y-3 ${
                    prefersReducedMotion ? "" : "animate-pulse"
                  }`}
                >
                  <div className="w-full h-36 bg-neutral-200 rounded-md" />
                  <div className="h-4 bg-neutral-200 rounded w-4/5" />
                  <div className="h-3 bg-neutral-200 rounded w-1/2" />
                </div>
              ))}
            </div>
          )}

          {/* Error Message */}
          {error && !isLoading && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <p className="font-semibold text-red-800">Could not retrieve video suggestions</p>
                <p>{error}</p>
                <a
                  href={searchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 font-bold text-primary hover:underline mt-2 min-h-[44px] py-2"
                >
                  <Search className="w-3.5 h-3.5" />
                  <span>Search "{topic}" on YouTube directly</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}

          {/* Fallback Zero-Key or Empty State */}
          {!isLoading && !error && data && data.videos.length === 0 && (
            <div className="p-5 rounded-lg bg-white border border-border text-center space-y-3 shadow-2xs">
              <div className="w-10 h-10 rounded-full bg-[#E9F1FC] text-primary flex items-center justify-center mx-auto">
                <Search className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-black">Explore topic on YouTube</h4>
                <p className="text-xs text-ink-muted mt-1 max-w-md mx-auto">
                  Direct educational search query curated for "{topic}". No synthetic or broken embeds are displayed.
                </p>
              </div>
              <a
                href={searchUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded bg-black hover:bg-neutral-800 text-white font-bold text-xs transition-colors min-h-[44px] shadow-2xs"
              >
                <Search className="w-3.5 h-3.5" />
                <span>Search "{topic}" on YouTube</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          )}

          {/* Valid Real Videos Grid */}
          {!isLoading && !error && data && data.videos.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-ink-muted pb-1 border-b border-border">
                <span className="flex items-center gap-1.5 font-semibold text-black">
                  <Sparkles className="w-3.5 h-3.5 text-primary" />
                  <span>{data.videos.length} Verified Educational Explanations</span>
                </span>
                <span className="text-[11px] uppercase tracking-wider font-mono">
                  Source: {data.source}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {data.videos.map((vid: RelatedVideo) => {
                  const isPlayingThis = activeVideoId === vid.video_id;

                  return (
                    <div
                      key={vid.video_id}
                      className="bg-white rounded-lg border border-border overflow-hidden shadow-2xs flex flex-col group hover:border-primary/50 transition-all"
                    >
                      {/* Video Container (Lite Facade Embed or Active Iframe) */}
                      <div className="relative aspect-video w-full bg-black overflow-hidden">
                        {isPlayingThis ? (
                          <iframe
                            src={`${vid.embed_url}?autoplay=1&rel=0&modestbranding=1`}
                            title={vid.title}
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                            className="w-full h-full border-0"
                          />
                        ) : (
                          <div
                            onClick={() => setActiveVideoId(vid.video_id)}
                            className="relative w-full h-full cursor-pointer group/facade"
                            role="button"
                            tabIndex={0}
                            aria-label={`Play video: ${vid.title}`}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                setActiveVideoId(vid.video_id);
                              }
                            }}
                          >
                            <Image
                              src={vid.thumbnail_url}
                              alt={vid.title}
                              fill
                              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                              className="object-cover group-hover/facade:scale-105 transition-transform duration-300"
                            />
                            {/* Dark Gradient Overlay */}
                            <div className="absolute inset-0 bg-black/30 group-hover/facade:bg-black/40 transition-colors" />

                            {/* Play Button Overlay (min 44x44 tap target) */}
                            <div className="absolute inset-0 flex items-center justify-center">
                              <div className="w-12 h-12 rounded-full bg-red-600 group-hover/facade:bg-red-700 text-white flex items-center justify-center shadow-lg transform group-hover/facade:scale-110 transition-transform">
                                <Play className="w-5 h-5 fill-current ml-0.5" />
                              </div>
                            </div>

                            {/* Duration Badge */}
                            {vid.duration && (
                              <div className="absolute bottom-2 right-2 px-1.5 py-0.5 rounded bg-black/80 text-white font-mono text-[10px] font-bold">
                                {vid.duration}
                              </div>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Video Details */}
                      <div className="p-3 flex-1 flex flex-col justify-between space-y-2">
                        <div>
                          <h4
                            className="text-xs font-bold text-black line-clamp-2 leading-tight"
                            title={vid.title}
                          >
                            {vid.title}
                          </h4>
                          <p className="text-[11px] text-ink-muted font-medium mt-1">
                            {vid.channel}
                          </p>
                        </div>

                        <div className="pt-2 border-t border-border flex items-center justify-between text-[11px]">
                          <button
                            type="button"
                            onClick={() => setActiveVideoId(vid.video_id)}
                            className="text-primary font-bold hover:underline flex items-center gap-1 min-h-[32px]"
                          >
                            <Play className="w-3 h-3 fill-current" />
                            <span>{isPlayingThis ? "Playing" : "Watch Inside"}</span>
                          </button>

                          <a
                            href={vid.watch_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-ink-muted hover:text-black font-semibold flex items-center gap-1 min-h-[32px]"
                            title="Open on YouTube in new tab"
                          >
                            <span>Open</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Extra Search Link */}
              <div className="text-right pt-1">
                <a
                  href={searchUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary font-bold hover:underline inline-flex items-center gap-1 py-1"
                >
                  <span>More videos on YouTube</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          )}
        </div>
      </CollapsibleDisclosure>
    </div>
  );
}
