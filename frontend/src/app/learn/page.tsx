'use client';

import { useState } from 'react';
import { api, YouTubeSearchResponse } from '@/lib/api';
import { Search, PlaySquare, ArrowLeft, PlayCircle, Flame } from 'lucide-react';
import Link from 'next/link';

export default function LearnPage() {
  const [query, setQuery] = useState('');
  const [video, setVideo] = useState<YouTubeSearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsSearching(true);
    setVideo(null);
    try {
      const res = await api.searchYouTube(query.trim());
      if (res.error) {
        alert(res.error);
      } else {
        setVideo(res);
      }
    } catch (err) {
      console.error(err);
      alert('Failed to search YouTube. Make sure the backend yt-dlp is configured properly.');
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="h-screen bg-[#0a0a0f] text-[#E0E0E0] font-sans overflow-y-auto custom-scrollbar pb-20">
      
      {/* Header */}
      <header className="sticky top-0 z-10 bg-[#0a0a0f]/90 backdrop-blur-md border-b border-[#222] px-10 py-6 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="p-2 bg-[#1A1A1A] hover:bg-[#222] rounded-xl transition-colors border border-[#2A2A2A]">
            <ArrowLeft size={20} className="text-[#888]" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <PlaySquare className="text-[#EF4444]" /> Video Teacher
            </h1>
            <p className="text-sm text-[#888] mt-1">Learn anything from the highest-viewed videos on YouTube.</p>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-10 py-12">
        <form onSubmit={handleSearch} className="mb-12 relative group">
          <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
            <Search className="text-[#555] group-focus-within:text-[#EF4444] transition-colors" size={24} />
          </div>
          <input 
            type="text" 
            placeholder="What do you want to learn today? (e.g., Dynamic Programming, Calculus...)" 
            className="w-full bg-[#141414] border-2 border-[#333] group-focus-within:border-[#EF4444] rounded-3xl py-6 pl-16 pr-32 text-white placeholder-[#555] outline-none transition-all text-xl shadow-lg"
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          <button 
            type="submit" 
            disabled={isSearching || !query}
            className="absolute right-3 top-3 bottom-3 bg-[#EF4444] hover:bg-red-500 text-white px-8 rounded-2xl font-bold text-lg transition-all disabled:opacity-50 hover:scale-105 active:scale-95 shadow-md flex items-center gap-2"
          >
            {isSearching ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <><PlayCircle size={20} /> Learn</>}
          </button>
        </form>

        {video && video.id && (
          <div className="animate-in fade-in slide-in-from-bottom-8 duration-700">
            <div className="bg-[#111] border border-[#222] rounded-3xl overflow-hidden shadow-[0_0_50px_rgba(239,68,68,0.05)]">
              {/* Video Player */}
              <div className="relative w-full aspect-video bg-black">
                <iframe 
                  src={`https://www.youtube.com/embed/${video.id}?autoplay=1`}
                  className="absolute inset-0 w-full h-full border-0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              </div>

              {/* Video Info */}
              <div className="p-8">
                <h2 className="text-2xl font-bold text-white mb-2 leading-tight">{video.title}</h2>
                <div className="flex items-center gap-6 mt-4 text-sm text-[#888]">
                  <div className="flex items-center gap-2 bg-[#1A1A1A] px-4 py-2 rounded-xl border border-[#2A2A2A]">
                    <span className="font-bold text-white">{video.uploader}</span>
                  </div>
                  {video.view_count && (
                    <div className="flex items-center gap-2">
                      <Flame size={16} className="text-[#EF4444]" />
                      <span className="font-medium">{(video.view_count).toLocaleString()} views</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {!video && !isSearching && query && (
          <div className="text-center py-20 text-[#666]">
            No video found. Try a different topic.
          </div>
        )}

      </main>

      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar { width: 8px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background-color: #333; border-radius: 20px; border: 2px solid #111; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background-color: #555; }
      `}} />
    </div>
  );
}
