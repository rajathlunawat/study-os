'use client';

import { useState, useEffect, useRef } from 'react';
import { api, Subject, ChatMessage } from '@/lib/api';
import { Home, Book, FileText, Send, Zap, BookOpen, Target, ArrowLeft, ArrowRight, X, Layout } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function NotebookPage() {
  const router = useRouter();
  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Study Mode State
  const [studyMode, setStudyMode] = useState<'none' | 'quiz' | 'flashcards'>('none');
  const [studyItems, setStudyItems] = useState<any[]>([]);
  const [studyIndex, setStudyIndex] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  
  // Flashcard specific
  const [isFlipped, setIsFlipped] = useState(false);
  
  // Quiz specific
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizScore, setQuizScore] = useState(0);
  const [showExplanation, setShowExplanation] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('studyos_token');
    if (!token) {
      router.push('/login');
      return;
    }
    const sid = localStorage.getItem('studyos_subject_id');
    if (sid) {
      setSubjectId(sid);
      loadHistory(sid);
    }
  }, [router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadHistory = async (sid: string) => {
    try {
      const history = await api.getChatHistory(sid);
      setMessages(history);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !subjectId) return;

    const userMsg = inputValue.trim();
    setInputValue('');
    
    // Optimistic UI
    const tempId = Date.now().toString();
    setMessages(prev => [...prev, { id: tempId, subject_id: subjectId, role: 'user', content: userMsg, timestamp: new Date().toISOString() }]);
    
    setIsSending(true);
    try {
      // For Notebook, we just send all documents by default or empty to let backend use all
      const response = await api.chat(subjectId, userMsg, []);
      setMessages(prev => [...prev, { id: tempId + 'ai', subject_id: subjectId, role: 'ai', content: response.reply, timestamp: new Date().toISOString() }]);
    } catch (err) {
      console.error(err);
    } finally {
      setIsSending(false);
    }
  };

  const startStudy = async (type: 'quiz' | 'flashcards') => {
    if (!subjectId) return;
    setIsGenerating(true);
    setStudyMode(type);
    setStudyIndex(0);
    setQuizScore(0);
    setSelectedOption(null);
    setShowExplanation(false);
    setIsFlipped(false);
    setStudyItems([]);

    try {
      const items = await api.studyGenerate(subjectId, type);
      setStudyItems(items);
    } catch (err) {
      alert("Failed to generate study materials.");
      setStudyMode('none');
    } finally {
      setIsGenerating(false);
    }
  };

  const nextStudyItem = async () => {
    if (studyMode === 'quiz' && selectedOption !== null) {
        const item = studyItems[studyIndex];
        const isCorrect = item.options[selectedOption] === item.answer;
        if (isCorrect) setQuizScore(prev => prev + 1);
    }

    if (studyIndex < studyItems.length - 1) {
      setStudyIndex(prev => prev + 1);
      setIsFlipped(false);
      setSelectedOption(null);
      setShowExplanation(false);
    } else {
      // Finish Study Session
      let finalScore = 0;
      if (studyMode === 'quiz') {
         const isCorrect = studyItems[studyIndex].options[selectedOption!] === studyItems[studyIndex].answer;
         const totalCorrect = quizScore + (isCorrect ? 1 : 0);
         finalScore = totalCorrect / studyItems.length;
         alert(`Quiz Complete! Score: ${Math.round(finalScore * 100)}%`);
      } else {
         // Flashcards just assume 100% completion for now, could be enhanced with self-rating
         finalScore = 1.0;
         alert(`Flashcard Deck Complete!`);
      }
      
      try {
        await api.studyScore(subjectId!, studyMode === 'quiz' ? 'quiz' : 'flashcard', finalScore);
      } catch (err) {
         console.error(err);
      }
      setStudyMode('none');
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#111111] text-[#E0E0E0] font-sans overflow-hidden">
      
      {/* ── SIDEBAR (Slim Version for Notebook) ── */}
      <aside className="w-[80px] min-w-[80px] h-full flex flex-col items-center py-6 bg-[#141414] border-r border-[#222222] z-10">
        <nav className="flex flex-col gap-6 w-full items-center">
          <Link href="/dashboard" className="p-3 rounded-xl text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors" title="Dashboard">
            <Layout size={24} />
          </Link>
          <Link href="/notebook" className="p-3 rounded-xl text-[#FDE68A] bg-[#2A2A2A] transition-colors shadow-[0_0_15px_rgba(253,230,138,0.1)]" title="Notebook">
            <FileText size={24} />
          </Link>
          <Link href="/library" className="p-3 rounded-xl text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors" title="Library">
            <Book size={24} />
          </Link>
        </nav>
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main className="flex-1 flex flex-col h-full relative bg-[#0a0a0f]">
        
        {/* Header */}
        <header className="h-[72px] min-h-[72px] flex items-center justify-between px-8 border-b border-[#222] bg-[#141414]/80 backdrop-blur-md z-10">
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">Interactive Notebook</h1>
            <p className="text-xs text-[#888] mt-0.5">Chat with your documents & generate study materials</p>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={() => startStudy('flashcards')}
              className="flex items-center gap-2 px-4 py-2 bg-[#1A1A1A] border border-[#333] hover:border-[#FDE68A] text-[#ccc] hover:text-white rounded-xl text-sm font-medium transition-all"
            >
              <Zap size={16} className="text-[#FDE68A]" /> Flashcards
            </button>
            <button 
              onClick={() => startStudy('quiz')}
              className="flex items-center gap-2 px-4 py-2 bg-[#FDE68A] hover:bg-[#FCD34D] text-[#111] rounded-xl text-sm font-bold transition-all shadow-[0_0_15px_rgba(253,230,138,0.2)]"
            >
              <Target size={16} /> Take Quiz
            </button>
          </div>
        </header>

        {/* Chat History Area */}
        <div className="flex-1 overflow-y-auto p-8 flex flex-col gap-6 custom-scrollbar pb-32">
          {!subjectId && (
            <div className="text-center text-[#888] mt-20">
              Please select a subject in the Dashboard to use the Notebook.
            </div>
          )}
          
          {messages.length === 0 && subjectId && (
             <div className="text-center text-[#888] mt-20 max-w-md mx-auto">
                <FileText size={48} className="mx-auto mb-4 opacity-20" />
                <h3 className="text-lg font-medium text-white mb-2">Welcome to your Notebook</h3>
                <p>Ask me to summarize your notes, explain difficult concepts, or generate study materials using the buttons above.</p>
             </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[75%] p-4 rounded-2xl ${
                msg.role === 'user' 
                  ? 'bg-[#FDE68A] text-[#111] rounded-br-none' 
                  : 'bg-[#1A1A1A] text-[#E0E0E0] border border-[#333] rounded-bl-none'
              }`}>
                {msg.role === 'ai' ? (
                  <div className="prose prose-invert max-w-none text-sm" dangerouslySetInnerHTML={{ __html: msg.content.replace(/\n/g, '<br/>') }} />
                ) : (
                  <div className="text-sm font-medium">{msg.content}</div>
                )}
              </div>
            </div>
          ))}
          
          {isSending && (
             <div className="flex justify-start">
               <div className="bg-[#1A1A1A] border border-[#333] rounded-2xl rounded-bl-none p-4 text-[#888] text-sm animate-pulse">
                 StudyOS is thinking...
               </div>
             </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="absolute bottom-0 left-0 w-full p-6 bg-gradient-to-t from-[#0a0a0f] via-[#0a0a0f] to-transparent">
          <form onSubmit={handleSendMessage} className="max-w-4xl mx-auto relative">
            <input 
              type="text"
              value={inputValue}
              onChange={e => setInputValue(e.target.value)}
              placeholder="Ask anything about your notes..."
              className="w-full bg-[#1A1A1A] border border-[#333] focus:border-[#FDE68A] text-white rounded-2xl pl-6 pr-14 py-4 outline-none transition-all shadow-xl"
              disabled={!subjectId || isSending}
            />
            <button 
              type="submit" 
              disabled={!subjectId || isSending || !inputValue.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 bg-[#FDE68A] text-[#111] rounded-xl hover:bg-[#FCD34D] disabled:opacity-50 transition-colors"
            >
              <Send size={18} />
            </button>
          </form>
        </div>

        {/* ── STUDY MODE OVERLAY ── */}
        {studyMode !== 'none' && (
          <div className="absolute inset-0 bg-[#0a0a0f]/95 backdrop-blur-xl z-50 flex flex-col">
            <header className="flex justify-between items-center p-6 border-b border-[#222]">
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                {studyMode === 'quiz' ? <Target className="text-[#60A5FA]" /> : <Zap className="text-[#FDE68A]" />}
                {studyMode === 'quiz' ? 'Pop Quiz' : 'Flashcards'}
              </h2>
              <button onClick={() => setStudyMode('none')} className="p-2 hover:bg-[#222] rounded-full text-[#888] hover:text-white transition-colors">
                <X size={24} />
              </button>
            </header>
            
            <div className="flex-1 flex flex-col items-center justify-center p-8">
              {isGenerating ? (
                <div className="flex flex-col items-center gap-4 text-[#FDE68A] animate-pulse">
                  <Zap size={48} />
                  <p className="text-lg font-medium text-white">Generating intelligent {studyMode}...</p>
                </div>
              ) : studyItems.length > 0 ? (
                <div className="w-full max-w-3xl">
                  <div className="text-sm font-bold text-[#888] mb-6 text-center uppercase tracking-widest">
                    Question {studyIndex + 1} of {studyItems.length}
                  </div>
                  
                  {/* FLASHCARD UI */}
                  {studyMode === 'flashcards' && (
                    <div 
                      className="w-full h-[400px] perspective-1000 cursor-pointer mb-8"
                      onClick={() => setIsFlipped(!isFlipped)}
                    >
                      <div className={`relative w-full h-full transition-transform duration-500 transform-style-preserve-3d ${isFlipped ? 'rotate-y-180' : ''}`}>
                        <div className="absolute w-full h-full backface-hidden bg-[#1A1A1A] border-2 border-[#333] hover:border-[#FDE68A] rounded-3xl p-10 flex items-center justify-center text-center shadow-2xl">
                           <h3 className="text-3xl font-bold text-white">{studyItems[studyIndex].front}</h3>
                           <p className="absolute bottom-6 text-[#666] text-sm">Click to reveal answer</p>
                        </div>
                        <div className="absolute w-full h-full backface-hidden rotate-y-180 bg-[#FDE68A] border-2 border-[#FCD34D] rounded-3xl p-10 flex flex-col items-center justify-center text-center shadow-2xl overflow-y-auto">
                           <h3 className="text-xl font-medium text-[#111] leading-relaxed">{studyItems[studyIndex].back}</h3>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* QUIZ UI */}
                  {studyMode === 'quiz' && (
                    <div className="w-full bg-[#1A1A1A] border border-[#333] rounded-3xl p-8 mb-8 shadow-2xl">
                      <h3 className="text-2xl font-bold text-white mb-8">{studyItems[studyIndex].question}</h3>
                      <div className="flex flex-col gap-3">
                        {studyItems[studyIndex].options.map((opt: string, i: number) => {
                          const isSelected = selectedOption === i;
                          const isCorrect = opt === studyItems[studyIndex].answer;
                          const showResult = showExplanation;
                          
                          let bgClass = "bg-[#222] border-[#444] hover:border-[#666]";
                          if (showResult) {
                             if (isCorrect) bgClass = "bg-[#064E3B]/40 border-[#10B981] text-[#10B981]";
                             else if (isSelected && !isCorrect) bgClass = "bg-[#7F1D1D]/40 border-[#EF4444] text-[#EF4444]";
                             else bgClass = "bg-[#222] border-[#333] opacity-50";
                          } else if (isSelected) {
                             bgClass = "bg-[#FDE68A]/10 border-[#FDE68A] text-[#FDE68A]";
                          }

                          return (
                            <button
                              key={i}
                              disabled={showExplanation}
                              onClick={() => setSelectedOption(i)}
                              className={`w-full text-left p-4 rounded-xl border-2 transition-all ${bgClass}`}
                            >
                              <span className="font-bold mr-3 opacity-50">{['A','B','C','D'][i]}</span> {opt}
                            </button>
                          );
                        })}
                      </div>

                      {showExplanation && (
                        <div className="mt-6 p-4 bg-[#3B82F6]/10 border border-[#3B82F6]/30 rounded-xl">
                           <p className="text-[#93C5FD] text-sm leading-relaxed"><span className="font-bold">Explanation:</span> {studyItems[studyIndex].explanation}</p>
                        </div>
                      )}
                    </div>
                  )}

                  {/* CONTROLS */}
                  <div className="flex justify-between items-center px-4">
                     {studyMode === 'quiz' && !showExplanation ? (
                        <button 
                          onClick={() => setShowExplanation(true)}
                          disabled={selectedOption === null}
                          className="mx-auto px-8 py-3 bg-[#60A5FA] hover:bg-[#3B82F6] text-white font-bold rounded-xl disabled:opacity-50 transition-colors"
                        >
                          Check Answer
                        </button>
                     ) : (
                        <button 
                          onClick={nextStudyItem}
                          className="ml-auto px-8 py-3 bg-[#FDE68A] hover:bg-[#FCD34D] text-[#111] font-bold rounded-xl transition-colors flex items-center gap-2"
                        >
                          {studyIndex < studyItems.length - 1 ? 'Next' : 'Finish'} <ArrowRight size={18} />
                        </button>
                     )}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
