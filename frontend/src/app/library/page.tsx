'use client';

import { useState } from 'react';
import { api, LibraryBook } from '@/lib/api';
import { Search, BookOpen, ExternalLink, HelpCircle, ArrowLeft, Send, Sparkles } from 'lucide-react';
import Link from 'next/link';

export default function LibraryPage() {
  const [activeTab, setActiveTab] = useState<'books' | 'doubt'>('books');
  
  const [bookQuery, setBookQuery] = useState('');
  const [books, setBooks] = useState<LibraryBook[]>([]);
  const [isSearchingBooks, setIsSearchingBooks] = useState(false);
  
  const [doubtQuery, setDoubtQuery] = useState('');
  const [doubtAnswer, setDoubtAnswer] = useState('');
  const [isAskingDoubt, setIsAskingDoubt] = useState(false);

  const handleSearchBooks = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!bookQuery.trim()) return;
    setIsSearchingBooks(true);
    try {
      const res = await api.searchLibrary(bookQuery.trim());
      setBooks(res.books);
    } catch (err) {
      console.error(err);
      alert('Failed to search books.');
    } finally {
      setIsSearchingBooks(false);
    }
  };

  const handleAskDoubt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!doubtQuery.trim()) return;
    setIsAskingDoubt(true);
    setDoubtAnswer('');
    try {
      const res = await api.askLibraryDoubt(doubtQuery.trim());
      setDoubtAnswer(res.answer);
    } catch (err) {
      console.error(err);
      setDoubtAnswer('Failed to get an answer. Please try again later.');
    } finally {
      setIsAskingDoubt(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#111111] text-[#E0E0E0] font-sans overflow-y-auto custom-scrollbar pb-20">
      
      {/* Header */}
      <header className="sticky top-0 z-10 bg-[#111111]/90 backdrop-blur-md border-b border-[#222] px-10 py-6 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Link href="/dashboard" className="p-2 bg-[#1A1A1A] hover:bg-[#222] rounded-xl transition-colors border border-[#2A2A2A]">
            <ArrowLeft size={20} className="text-[#888]" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <BookOpen className="text-[#FDE68A]" /> World Library
            </h1>
            <p className="text-sm text-[#888] mt-1">Access millions of free books and ask expert doubts.</p>
          </div>
        </div>
        
        <div className="flex bg-[#1A1A1A] p-1 rounded-xl border border-[#2A2A2A]">
          <button 
            onClick={() => setActiveTab('books')}
            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'books' ? 'bg-[#2A2A2A] text-white shadow-sm' : 'text-[#888] hover:text-[#CCC]'}`}
          >
            Find Books
          </button>
          <button 
            onClick={() => setActiveTab('doubt')}
            className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'doubt' ? 'bg-[#2A2A2A] text-white shadow-sm' : 'text-[#888] hover:text-[#CCC]'}`}
          >
            Ask a Doubt
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-10 py-12">
        {activeTab === 'books' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <form onSubmit={handleSearchBooks} className="mb-12 max-w-2xl mx-auto relative group">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className="text-[#555] group-focus-within:text-[#FDE68A] transition-colors" size={20} />
              </div>
              <input 
                type="text" 
                placeholder="Search for subjects, authors, or book titles..." 
                className="w-full bg-[#141414] border border-[#333] group-focus-within:border-[#FDE68A] rounded-2xl py-4 pl-12 pr-32 text-white placeholder-[#555] outline-none transition-all text-lg shadow-sm"
                value={bookQuery}
                onChange={e => setBookQuery(e.target.value)}
              />
              <button 
                type="submit" 
                disabled={isSearchingBooks || !bookQuery}
                className="absolute right-2 top-2 bottom-2 bg-[#FDE68A] hover:bg-white text-[#111] px-6 rounded-xl font-bold text-sm transition-colors disabled:opacity-50"
              >
                {isSearchingBooks ? 'Searching...' : 'Search'}
              </button>
            </form>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {books.map(book => (
                <a 
                  key={book.key} 
                  href={`https://openlibrary.org${book.key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex flex-col bg-[#141414] border border-[#222] hover:border-[#444] rounded-2xl overflow-hidden transition-all hover:-translate-y-1 hover:shadow-lg"
                >
                  <div className="aspect-[2/3] bg-[#1A1A1A] relative flex items-center justify-center border-b border-[#222]">
                    {book.cover_url ? (
                      <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                    ) : (
                      <BookOpen size={48} className="text-[#333]" />
                    )}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <div className="bg-[#FDE68A] text-[#111] p-3 rounded-full translate-y-4 group-hover:translate-y-0 transition-transform">
                        <ExternalLink size={20} />
                      </div>
                    </div>
                  </div>
                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <h3 className="font-bold text-white text-lg line-clamp-2 leading-tight mb-1 group-hover:text-[#FDE68A] transition-colors">{book.title}</h3>
                      <p className="text-sm text-[#888] line-clamp-1">{book.author}</p>
                    </div>
                    {book.year && <p className="text-xs font-medium text-[#555] mt-4 uppercase tracking-wider">{book.year}</p>}
                  </div>
                </a>
              ))}
            </div>

            {books.length === 0 && !isSearchingBooks && bookQuery && (
              <div className="text-center py-20 text-[#666]">
                No books found. Try a different search term.
              </div>
            )}
          </div>
        )}

        {activeTab === 'doubt' && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 max-w-4xl mx-auto">
            <div className="bg-[#141414] border border-[#222] rounded-3xl p-8 shadow-xl">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-[#FDE68A]/10 rounded-2xl flex items-center justify-center border border-[#FDE68A]/20">
                  <HelpCircle className="text-[#FDE68A]" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Ask the Librarian</h2>
                  <p className="text-[#888] text-sm">Get accurate answers with specific textbook & page citations.</p>
                </div>
              </div>

              <form onSubmit={handleAskDoubt} className="relative mb-8 group">
                <textarea 
                  placeholder="e.g., Explain the difference between meiosis and mitosis, and where can I read more about it?" 
                  className="w-full bg-[#1A1A1A] border border-[#333] group-focus-within:border-[#FDE68A] rounded-2xl p-5 min-h-[120px] text-white placeholder-[#555] outline-none transition-all resize-none shadow-inner"
                  value={doubtQuery}
                  onChange={e => setDoubtQuery(e.target.value)}
                  onKeyDown={e => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAskDoubt(e); } }}
                />
                <button 
                  type="submit" 
                  disabled={isAskingDoubt || !doubtQuery}
                  className="absolute right-4 bottom-4 bg-[#FDE68A] hover:bg-white text-[#111] p-3 rounded-xl font-bold transition-all shadow-md disabled:opacity-50 hover:scale-105 active:scale-95"
                >
                  <Send size={18} />
                </button>
              </form>

              {isAskingDoubt && (
                <div className="py-12 flex flex-col items-center justify-center gap-4">
                  <div className="w-8 h-8 border-4 border-[#333] border-t-[#FDE68A] rounded-full animate-spin"></div>
                  <p className="text-[#888] font-medium animate-pulse">Searching through textbooks and generating citations...</p>
                </div>
              )}

              {doubtAnswer && (
                <div className="bg-[#1A1A1A] border border-[#333] rounded-2xl p-8 relative overflow-hidden mt-8">
                  <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
                    <Sparkles size={120} />
                  </div>
                  <div className="prose prose-invert max-w-none relative z-10" dangerouslySetInnerHTML={{ __html: doubtAnswer.replace(/\n/g, '<br/>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/### (.*?)\n/g, '<h3>$1</h3>') }} />
                </div>
              )}
            </div>
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
