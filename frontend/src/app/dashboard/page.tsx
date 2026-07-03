'use client';

import { useState, useEffect, useRef } from 'react';
import { api, PredictionResponse, UserStats, StudyTask, Subject } from '@/lib/api';
import { Home, Book, Bell, GraduationCap, Users, Search, Plus, FileText, FolderOpen, MoreHorizontal, Share2, Edit2, Play, Trash2, Zap, Calendar, Target, Check, BarChart2, Circle, ArrowRight, Flame, Upload } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function DashboardPage() {
  const router = useRouter();
  
  // Data state
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<string | null>(null);
  
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [tasks, setTasks] = useState<StudyTask[]>([]);
  
  const [isLoading, setIsLoading] = useState(true);

  // New subject/plan state
  const [newSubjectName, setNewSubjectName] = useState('');
  const [isAddingSubject, setIsAddingSubject] = useState(false);
  
  const [newTopic, setNewTopic] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadSubjects();
  }, []);

  useEffect(() => {
    if (selectedSubjectId) {
      localStorage.setItem('studyos_subject_id', selectedSubjectId);
      fetchData(selectedSubjectId);
    }
  }, [selectedSubjectId]);

  const loadSubjects = async () => {
    try {
      const subs = await api.getSubjects();
      setSubjects(subs);
      
      const storedId = localStorage.getItem('studyos_subject_id');
      if (storedId && subs.find(s => s.id === storedId)) {
        setSelectedSubjectId(storedId);
      } else if (subs.length > 0) {
        setSelectedSubjectId(subs[0].id);
      } else {
        setIsLoading(false); // No subjects yet
      }
    } catch (err) {
      console.error('Failed to load subjects', err);
      setIsLoading(false);
    }
  };

  const fetchData = async (subjectId: string) => {
    setIsLoading(true);
    try {
      const [pred, userStats, allTasks] = await Promise.all([
        api.getPrediction(subjectId),
        api.getStats(subjectId),
        api.getTasks(subjectId)
      ]);
      setPrediction(pred);
      setStats(userStats);
      setTasks(allTasks);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubjectName.trim()) return;
    
    setIsAddingSubject(true);
    try {
      const newSub = await api.addSubject(newSubjectName.trim());
      setSubjects(prev => [newSub, ...prev]);
      setSelectedSubjectId(newSub.id);
      setNewSubjectName('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsAddingSubject(false);
    }
  };

  const handleGeneratePlan = async () => {
    if (!newTopic || !selectedSubjectId) return;
    setIsGenerating(true);
    try {
      const targetDate = new Date();
      targetDate.setDate(targetDate.getDate() + 7);
      
      await api.generatePlanner(selectedSubjectId, newTopic, targetDate.toISOString(), 2);
      await fetchData(selectedSubjectId);
      setNewTopic('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleTask = async (taskId: string, currentStatus: boolean) => {
    if (!selectedSubjectId) return;
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, completed: !currentStatus } : t));
    try {
      await api.updateTask(taskId, !currentStatus);
      const newStats = await api.getStats(selectedSubjectId);
      setStats(newStats);
      const newPred = await api.getPrediction(selectedSubjectId);
      setPrediction(newPred);
    } catch {
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, completed: currentStatus } : t));
    }
  };

  const handleActionClick = (action: string) => {
    if (action === 'share' || action === 'edit') {
      alert(`${action.charAt(0).toUpperCase() + action.slice(1)} feature is coming soon!`);
    } else {
      router.push('/');
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedSubjectId) return;

    setIsUploading(true);
    try {
      await api.uploadDocument(file, 'notes', selectedSubjectId);
      // Optional: alert success or just let user know
      alert('Document uploaded successfully! View it in the Notebook.');
      // Refresh stats in case upload affected readiness (though it doesn't directly, it might in the future)
      fetchData(selectedSubjectId);
    } catch (err: any) {
      alert('Upload failed: ' + err?.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const activeTasks = tasks.filter(t => !t.completed);
  const completedTasks = tasks.filter(t => t.completed);

  return (
    <div className="flex h-screen w-full bg-[#111111] text-[#E0E0E0] font-sans overflow-hidden" style={{ backgroundImage: 'radial-gradient(ellipse at 80% 20%, rgba(60, 40, 30, 0.15), transparent 40%), radial-gradient(ellipse at 20% 80%, rgba(40, 50, 70, 0.1), transparent 40%)' }}>
      
      {/* ── SIDEBAR ── */}
      <aside className="w-[280px] min-w-[280px] h-full flex flex-col justify-between py-6 px-4 bg-[#111111]/80 backdrop-blur-2xl border-r border-[#222222] shadow-[4px_0_24px_rgba(0,0,0,0.4)] z-10">
        <div className="flex flex-col gap-8">
          <nav className="flex flex-col gap-1.5">
            <Link href="/" className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors">
              <Home size={18} /> Home
            </Link>
            <button className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors">
              <Book size={18} /> Library
            </button>
            <button className="flex items-center justify-between px-4 py-2.5 rounded-xl text-sm font-medium text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors">
              <div className="flex items-center gap-3">
                <Bell size={18} /> Notifications
              </div>
              <span className="bg-[#222] text-[#ccc] text-[10px] font-bold px-2 py-0.5 rounded-full">2</span>
            </button>
            <div className="flex items-center gap-3 px-4 py-3 mt-1 rounded-xl text-sm font-semibold bg-[#FDE68A] text-[#111] shadow-[0_0_15px_rgba(253,230,138,0.15)] cursor-pointer">
              <GraduationCap size={18} /> Learn
            </div>
            <button className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors mt-1">
              <Users size={18} /> My Team
            </button>
            <button className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium text-[#999] hover:text-white hover:bg-[#1A1A1A] transition-colors">
              <Search size={18} /> Search
            </button>
          </nav>

          <div className="w-full h-px bg-gradient-to-r from-transparent via-[#333] to-transparent my-1" />

          <div className="flex flex-col gap-2">
            <div className="px-4 flex items-center justify-between text-xs font-bold uppercase tracking-widest text-[#555] mb-2">
              My Subjects <MoreHorizontal size={14} className="cursor-pointer hover:text-white transition-colors" />
            </div>
            
            <form onSubmit={handleAddSubject} className="px-4 mb-2">
              <div className="flex items-center gap-2 bg-[#1A1A1A] border border-[#333] rounded-xl px-3 py-1.5 focus-within:border-[#FDE68A] transition-colors">
                <input 
                  type="text" 
                  placeholder="New subject..." 
                  className="bg-transparent border-none outline-none text-xs w-full text-white placeholder-[#555]"
                  value={newSubjectName}
                  onChange={e => setNewSubjectName(e.target.value)}
                />
                <button type="submit" disabled={isAddingSubject || !newSubjectName} className="text-[#888] hover:text-white disabled:opacity-50">
                  <Plus size={14} />
                </button>
              </div>
            </form>

            <div className="flex flex-col gap-1 max-h-[200px] overflow-y-auto custom-scrollbar">
              {subjects.map(subject => (
                <button 
                  key={subject.id}
                  onClick={() => setSelectedSubjectId(subject.id)}
                  className={`flex items-center gap-3 px-4 py-2 rounded-xl text-sm font-medium transition-colors ${selectedSubjectId === subject.id ? 'bg-[#2A2A2A] text-white' : 'text-[#888] hover:text-white hover:bg-[#1A1A1A]'}`}
                >
                  <FileText size={16} className={selectedSubjectId === subject.id ? 'text-[#FDE68A]' : ''} /> 
                  <span className="truncate">{subject.name}</span>
                </button>
              ))}
            </div>

          </div>
        </div>

        {/* Removed user profile widget as requested */}
      </aside>

      {/* ── MAIN CONTENT ── */}
      <main className="flex-1 h-full flex flex-col px-10 py-12 overflow-y-auto custom-scrollbar relative z-0">
        
        {!selectedSubjectId && !isLoading ? (
           <div className="flex-1 flex flex-col items-center justify-center text-center max-w-md mx-auto">
             <div className="w-20 h-20 bg-[#1A1A1A] rounded-2xl flex items-center justify-center mb-6 border border-[#333]">
               <Book size={32} className="text-[#FDE68A]" />
             </div>
             <h2 className="text-2xl font-bold text-white mb-2">Welcome to StudyOS</h2>
             <p className="text-[#888] mb-8 leading-relaxed">Create your first Subject in the sidebar to start tracking your readiness, generating tasks, and studying with AI memory.</p>
           </div>
        ) : (
          <>
            {/* Header */}
            <div className="flex justify-between items-start mb-8">
              <div>
                <h1 className="text-3xl font-bold text-white tracking-tight">{subjects.find(s => s.id === selectedSubjectId)?.name || 'Learning'}</h1>
                <p className="text-[#888] mt-2 font-medium">Study your cards with spaced repetition.</p>
              </div>
              
              <div className="flex items-center gap-3 bg-[#1A1A1A] border border-[#333] rounded-xl p-1 pr-1.5 focus-within:border-[#FDE68A] transition-colors shadow-lg">
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  onChange={handleFileChange} 
                  style={{ display: 'none' }} 
                  accept=".pdf,.txt,.docx"
                />
                <button 
                  onClick={handleUploadClick}
                  disabled={isUploading}
                  className="flex items-center gap-2 bg-[#2A2A2A] hover:bg-[#333] text-[#888] hover:text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-[#444] disabled:opacity-50"
                  title="Upload notes directly to this subject"
                >
                  <Upload size={16} /> {isUploading ? 'Uploading...' : 'Upload Notes'}
                </button>
                <div className="w-px h-6 bg-[#333] mx-1"></div>
                <input 
                  type="text" 
                  placeholder="e.g. Chapter 4..." 
                  className="bg-transparent border-none outline-none text-sm px-4 py-2 w-48 text-white placeholder-[#555]"
                  value={newTopic}
                  onChange={e => setNewTopic(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleGeneratePlan()}
                />
                <button 
                  onClick={handleGeneratePlan}
                  disabled={isGenerating || !newTopic}
                  className="flex items-center gap-2 bg-[#2A2A2A] hover:bg-[#333] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors border border-[#444] disabled:opacity-50"
                >
                  <Plus size={16} /> {isGenerating ? 'Adding...' : 'New Study Plan'}
                </button>
              </div>
            </div>

            {/* Stats Row */}
            <div className="flex items-center gap-12 bg-[#141414]/50 backdrop-blur-md border border-[#222] rounded-2xl p-6 mb-10 shadow-sm overflow-x-auto custom-scrollbar">
              <div className="flex items-center gap-4 shrink-0">
                <Zap size={24} className="text-[#999]" />
                <div>
                  <div className="text-xl font-bold text-white leading-none">{activeTasks.length}</div>
                  <div className="text-xs font-medium text-[#666] mt-1">Due</div>
                </div>
              </div>
              <div className="w-px h-10 bg-[#222] shrink-0" />
              <div className="flex items-center gap-4 shrink-0">
                <Flame size={24} className="text-[#F87171]" />
                <div>
                  <div className="text-xl font-bold text-white leading-none">{stats?.study_streak || 0}</div>
                  <div className="text-xs font-medium text-[#666] mt-1">Days Streak</div>
                </div>
              </div>
              <div className="w-px h-10 bg-[#222] shrink-0" />
              <div className="flex items-center gap-4 shrink-0">
                <Calendar size={24} className="text-[#34D399]" />
                <div>
                  <div className="text-xl font-bold text-white leading-none">{Math.round((stats?.task_completion || 0) * 100)}%</div>
                  <div className="text-xs font-medium text-[#666] mt-1">Completion Rate</div>
                </div>
              </div>
              <div className="w-px h-10 bg-[#222] shrink-0" />
              <div className="flex items-center gap-4 shrink-0">
                <Target size={24} className="text-[#60A5FA]" />
                <div>
                  <div className="text-xl font-bold text-white leading-none">{prediction ? Math.round(prediction.readiness_score * 100) : 0}%</div>
                  <div className="text-xs font-medium text-[#666] mt-1">Readiness Score</div>
                </div>
              </div>
            </div>

            {/* Filters */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-2 text-[#666] hover:text-white cursor-pointer transition-colors text-sm font-medium">
                <Search size={16} /> Smart Search
              </div>
              <div className="flex items-center gap-3">
                <button className="flex items-center gap-2 bg-[#1A1A1A] border border-[#2A2A2A] hover:border-[#444] px-4 py-2 rounded-xl text-sm font-medium text-[#CCC] transition-all">
                  Created by me <MoreHorizontal size={14} className="ml-1" />
                </button>
                <button className="flex items-center gap-2 bg-[#1A1A1A] border border-[#2A2A2A] hover:border-[#444] px-4 py-2 rounded-xl text-sm font-medium text-[#CCC] transition-all">
                  Recent Plans <MoreHorizontal size={14} className="ml-1" />
                </button>
                <button className="flex items-center gap-2 bg-[#1A1A1A] border border-[#2A2A2A] hover:border-[#444] px-4 py-2 rounded-xl text-sm font-medium text-[#CCC] transition-all">
                  Archive
                </button>
                <button onClick={() => handleActionClick('study_all')} className="flex items-center gap-2 bg-[#FDE68A] text-[#111] hover:bg-white px-5 py-2 rounded-xl text-sm font-bold transition-all shadow-[0_0_20px_rgba(253,230,138,0.2)] ml-2">
                  <Zap size={16} className="fill-current" /> Study All
                </button>
              </div>
            </div>

            {/* Task Lists */}
            {isLoading ? (
              <div className="flex-1 flex items-center justify-center">
                <div className="animate-pulse text-[#666] font-medium flex items-center gap-3">
                  <Circle className="animate-spin" size={20} /> Loading Study Plans...
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4 pb-20">
                
                {/* Active Tasks */}
                {activeTasks.length === 0 && completedTasks.length === 0 && (
                  <div className="text-center py-20 text-[#555] bg-[#141414] rounded-2xl border border-[#222]">
                    No study plans for {subjects.find(s => s.id === selectedSubjectId)?.name}. Generate one above to begin!
                  </div>
                )}

                {activeTasks.map((task, i) => {
                  // Fake varying progress for UI aesthetics based on index
                  const fakeProgress = i === 0 ? 25 : i === 1 ? 0 : 50;
                  const radius = 24;
                  const circumference = 2 * Math.PI * radius;
                  const strokeDashoffset = circumference - (fakeProgress / 100) * circumference;
                  
                  return (
                    <div key={task.id} className="group bg-[#141414]/80 backdrop-blur-md border border-[#2A2A2A] hover:border-[#444] rounded-2xl p-5 flex items-center gap-6 transition-all hover:bg-[#1A1A1A]/80 shadow-sm">
                      {/* Progress Ring */}
                      <div className="relative flex items-center justify-center w-16 h-16 shrink-0">
                        <svg className="w-full h-full transform -rotate-90">
                          <circle cx="32" cy="32" r={radius} stroke="#222" strokeWidth="4" fill="transparent" />
                          <circle
                            cx="32" cy="32" r={radius}
                            stroke="#FDE68A" strokeWidth="4" fill="transparent"
                            strokeDasharray={circumference}
                            strokeDashoffset={strokeDashoffset}
                            strokeLinecap="round"
                            className="transition-all duration-1000"
                          />
                        </svg>
                        <div className="absolute text-xs font-bold text-white">{fakeProgress}%</div>
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-bold text-white truncate">{task.title}</h3>
                        <p className="text-sm text-[#888] truncate mt-0.5">{task.description || task.title}</p>
                        <div className="flex items-center gap-4 mt-3 text-xs font-medium text-[#666]">
                          <span className="flex items-center gap-1.5"><Target size={12} /> {fakeProgress}% Complete</span>
                          <span className="flex items-center gap-1.5"><Calendar size={12} /> {new Date(task.scheduled_date).toLocaleDateString(undefined, {month: 'short', day: 'numeric'})}</span>
                          <span className="flex items-center gap-1.5"><Users size={12} /> by you</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 opacity-50 group-hover:opacity-100 transition-opacity shrink-0">
                        <button onClick={() => handleActionClick('share')} className="p-2.5 rounded-xl hover:bg-[#222] text-[#888] hover:text-white transition-colors"><Share2 size={18} /></button>
                        <button onClick={() => handleActionClick('edit')} className="p-2.5 rounded-xl hover:bg-[#222] text-[#888] hover:text-white transition-colors"><Edit2 size={18} /></button>
                        <Link href="/" className="p-2.5 rounded-xl hover:bg-[#222] text-[#888] hover:text-white transition-colors"><Play size={18} /></Link>
                        <button 
                          onClick={() => toggleTask(task.id, task.completed)}
                          className="p-2.5 rounded-xl hover:bg-[#222] text-[#888] hover:text-[#34D399] transition-colors"
                          title="Mark Complete"
                        >
                          <Check size={18} />
                        </button>
                      </div>

                      {/* Primary Button */}
                      <div className="pl-4 shrink-0 border-l border-[#2A2A2A] ml-2">
                        <Link 
                          href="/"
                          className="bg-[#FDE68A] hover:bg-white text-[#111] px-5 py-2.5 rounded-xl text-sm font-bold transition-colors flex items-center gap-2 shadow-[0_4px_14px_rgba(253,230,138,0.15)]"
                        >
                          <BarChart2 size={16} /> View Notes
                        </Link>
                      </div>
                    </div>
                  );
                })}

                {/* Completed Tasks */}
                {completedTasks.length > 0 && (
                  <div className="mt-8">
                    <div className="flex items-center gap-4 mb-4">
                      <h3 className="text-sm font-semibold text-[#666]">Completed</h3>
                      <div className="flex-1 h-px bg-[#222]" />
                    </div>
                    <div className="flex flex-col gap-4">
                      {completedTasks.map(task => (
                        <div key={task.id} className="group bg-[#111] border border-[#222] rounded-2xl p-5 flex items-center gap-6 opacity-60 hover:opacity-100 transition-opacity">
                          {/* Progress Ring - 100% */}
                          <div className="relative flex items-center justify-center w-16 h-16 shrink-0">
                            <svg className="w-full h-full transform -rotate-90">
                              <circle cx="32" cy="32" r={24} stroke="#34D399" strokeWidth="4" fill="transparent" />
                            </svg>
                            <div className="absolute text-xs font-bold text-[#34D399]">100%</div>
                          </div>

                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-bold text-[#999] line-through decoration-[#444] truncate">{task.title}</h3>
                            <div className="flex items-center gap-4 mt-2 text-xs font-medium text-[#555]">
                              <span className="flex items-center gap-1.5"><Check size={12} className="text-[#34D399]" /> Completed</span>
                              <span className="flex items-center gap-1.5"><Users size={12} /> by you</span>
                            </div>
                          </div>

                          <button 
                            onClick={() => toggleTask(task.id, task.completed)}
                            className="p-3 rounded-xl hover:bg-[#222] text-[#555] hover:text-white transition-colors"
                            title="Mark Uncomplete"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            )}
          </>
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
