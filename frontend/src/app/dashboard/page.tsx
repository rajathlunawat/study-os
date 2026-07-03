'use client';

import { useState, useEffect } from 'react';
import { api, PredictionResponse, UserStats, StudyTask } from '@/lib/api';
import { Brain, Calendar, CheckCircle2, Circle, Flame, Target, Trophy, Clock, ArrowRight, BookOpen, Layers } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [tasks, setTasks] = useState<StudyTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // New plan state
  const [newTopic, setNewTopic] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [pred, userStats, allTasks] = await Promise.all([
        api.getPrediction(),
        api.getStats(),
        api.getTasks()
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

  const handleGeneratePlan = async () => {
    if (!newTopic || !targetDate) return;
    setIsGenerating(true);
    try {
      await api.generatePlanner(newTopic, new Date(targetDate).toISOString(), 2);
      await fetchData(); // Refresh everything
      setNewTopic('');
      setTargetDate('');
    } catch (err) {
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  const toggleTask = async (taskId: string, currentStatus: boolean) => {
    // Optimistic UI update
    setTasks(prev => prev.map(t => t.id === taskId ? { ...t, completed: !currentStatus } : t));
    
    try {
      await api.updateTask(taskId, !currentStatus);
      // Refresh stats quietly to update streak/completion metrics
      const newStats = await api.getStats();
      setStats(newStats);
      const newPred = await api.getPrediction();
      setPrediction(newPred);
    } catch {
      // Revert on error
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, completed: currentStatus } : t));
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#0d0d0d]">
        <div className="animate-pulse text-xl text-[#FACC15] font-medium tracking-wide">Syncing Workspace...</div>
      </div>
    );
  }

  // Calculate circumference for circular progress
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const score = prediction?.readiness_score || 0;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="min-h-screen bg-[#0d0d0d] text-[#e5e5e5] font-sans p-6 md:p-10 flex flex-col items-center">
      
      {/* HEADER NAVIGATION */}
      <header className="w-full max-w-7xl flex justify-between items-center mb-12 border-b border-[#222] pb-6">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-[#FACC15] rounded-lg flex items-center justify-center text-[#0d0d0d]">
            <Layers size={22} className="fill-current" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">StudyOS</h1>
            <p className="text-sm text-[#888] font-medium">Workspace Overview</p>
          </div>
        </div>
        <Link href="/" className="group flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#1a1a1a] hover:bg-[#FACC15] text-[#FACC15] hover:text-[#0d0d0d] font-semibold transition-all border border-[#333] hover:border-[#FACC15]">
          <span>Notebook</span>
          <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
        </Link>
      </header>

      {/* BENTO GRID LAYOUT */}
      <div className="w-full max-w-7xl grid grid-cols-1 md:grid-cols-12 gap-6 auto-rows-min">
        
        {/* ROW 1: STATS & READINESS */}
        
        {/* Left: Overall Readiness */}
        <div className="col-span-1 md:col-span-5 bg-[#141414] rounded-3xl p-8 border border-[#222] flex flex-col relative overflow-hidden group hover:border-[#333] transition-colors">
          <div className="absolute top-0 right-0 w-32 h-32 bg-[#FACC15] opacity-[0.03] rounded-bl-[100px] pointer-events-none" />
          
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#888] mb-8 flex items-center gap-2">
            <Target size={16} className="text-[#FACC15]" /> Exam Readiness
          </h2>
          
          <div className="flex items-center justify-between mt-auto">
            <div className="relative flex items-center justify-center w-40 h-40">
              <svg className="w-full h-full transform -rotate-90 drop-shadow-xl">
                <circle cx="80" cy="80" r={radius} stroke="#222" strokeWidth="10" fill="transparent" />
                <circle
                  cx="80" cy="80" r={radius}
                  stroke="#FACC15" strokeWidth="10" fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-all duration-1000 ease-out"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-5xl font-black text-white tracking-tighter">{score}</span>
                <span className="text-[10px] font-bold uppercase tracking-widest text-[#FACC15] mt-1">Score</span>
              </div>
            </div>
            
            <div className="text-right flex flex-col justify-center">
              <div className="text-2xl font-bold text-white mb-2 leading-tight">
                {prediction?.readiness_band || 'Unknown'}
              </div>
              <p className="text-sm font-medium text-[#888]">
                <span className="text-[#FACC15]">{((prediction?.pass_probability || 0) * 100).toFixed(1)}%</span> Pass Probability
              </p>
            </div>
          </div>
        </div>

        {/* Right: Quick Stats Bento Box */}
        <div className="col-span-1 md:col-span-7 grid grid-cols-2 md:grid-cols-3 gap-6">
          <div className="bg-[#141414] rounded-3xl p-6 border border-[#222] flex flex-col justify-between hover:bg-[#1a1a1a] transition-colors">
            <div className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center mb-6">
              <Brain size={20} className="text-[#FACC15]" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white tracking-tight">{Math.round((stats?.quiz_accuracy || 0) * 100)}%</p>
              <p className="text-xs font-bold uppercase tracking-wider text-[#666] mt-2">Quiz Accuracy</p>
            </div>
          </div>

          <div className="bg-[#141414] rounded-3xl p-6 border border-[#222] flex flex-col justify-between hover:bg-[#1a1a1a] transition-colors">
            <div className="w-10 h-10 rounded-full bg-[#1a1a1a] flex items-center justify-center mb-6">
              <Trophy size={20} className="text-[#FACC15]" />
            </div>
            <div>
              <p className="text-3xl font-bold text-white tracking-tight">{Math.round((stats?.task_completion || 0) * 100)}%</p>
              <p className="text-xs font-bold uppercase tracking-wider text-[#666] mt-2">Task Completion</p>
            </div>
          </div>

          <div className="col-span-2 md:col-span-1 bg-[#FACC15] rounded-3xl p-6 flex flex-col justify-between text-[#0d0d0d] relative overflow-hidden group">
            <div className="absolute -right-4 -top-4 opacity-20 transform rotate-12 group-hover:scale-110 transition-transform">
              <Flame size={120} />
            </div>
            <div className="w-10 h-10 rounded-full bg-black/10 flex items-center justify-center mb-6 relative z-10">
              <Flame size={20} className="text-[#0d0d0d]" />
            </div>
            <div className="relative z-10">
              <p className="text-4xl font-black tracking-tighter">{stats?.study_streak || 0}</p>
              <p className="text-xs font-bold uppercase tracking-wider text-black/60 mt-1">Day Streak</p>
            </div>
          </div>
        </div>

        {/* ROW 2: PLANNER & INSIGHTS */}

        {/* Left: AI Insights */}
        <div className="col-span-1 md:col-span-5 flex flex-col gap-6">
          <div className="bg-[#141414] rounded-3xl p-8 border border-[#222] flex-1">
            <h2 className="text-sm font-bold uppercase tracking-widest text-[#888] mb-6 flex items-center gap-2">
              <BookOpen size={16} className="text-[#FACC15]" /> Actionable Insights
            </h2>
            {(!prediction?.insights || prediction.insights.length === 0) ? (
              <p className="text-[#666] text-sm">No insights available yet. Keep studying!</p>
            ) : (
              <ul className="space-y-4">
                {prediction.insights.map((insight, idx) => (
                  <li key={idx} className="flex gap-4 text-sm font-medium text-[#ccc] items-start p-4 bg-[#1a1a1a] rounded-2xl border border-[#222]">
                    <span className="w-6 h-6 rounded-full bg-[#FACC15]/10 text-[#FACC15] flex items-center justify-center flex-shrink-0 text-xs font-bold">{idx + 1}</span>
                    <span className="leading-relaxed">{insight}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right: Task Manager */}
        <div className="col-span-1 md:col-span-7 bg-[#141414] rounded-3xl p-8 border border-[#222] flex flex-col">
          
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8 border-b border-[#222] pb-8">
            <h2 className="text-lg font-bold text-white flex items-center gap-3">
              <Calendar size={22} className="text-[#FACC15]" /> Study Roadmap
            </h2>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="text"
                placeholder="Topics (e.g. ML, Physics)"
                value={newTopic}
                onChange={e => setNewTopic(e.target.value)}
                className="bg-[#0d0d0d] border border-[#333] text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-[#FACC15] focus:ring-1 focus:ring-[#FACC15] transition-all text-white placeholder-[#555] w-full sm:w-48"
              />
              <input
                type="date"
                value={targetDate}
                onChange={e => setTargetDate(e.target.value)}
                className="bg-[#0d0d0d] border border-[#333] text-sm rounded-xl px-4 py-2.5 focus:outline-none focus:border-[#FACC15] transition-all text-[#ccc] [color-scheme:dark] w-full sm:w-auto"
              />
              <button
                onClick={handleGeneratePlan}
                disabled={isGenerating || !newTopic || !targetDate}
                className="bg-[#FACC15] text-[#0d0d0d] px-6 py-2.5 rounded-xl font-bold text-sm hover:bg-white transition-colors disabled:opacity-50 disabled:hover:bg-[#FACC15] whitespace-nowrap"
              >
                {isGenerating ? 'Building...' : 'Add Plan'}
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar" style={{ maxHeight: '500px' }}>
            {tasks.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-[#555] py-20">
                <Clock size={48} className="mb-4 opacity-20" />
                <p className="font-medium text-lg text-[#888]">No active tasks</p>
                <p className="text-sm mt-1">Generate a study roadmap above.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {tasks.map(task => {
                  const dateObj = new Date(task.scheduled_date);
                  const isPast = dateObj < new Date() && !task.completed;
                  return (
                    <div 
                      key={task.id} 
                      className={`group flex items-start gap-5 p-5 rounded-2xl border transition-all cursor-pointer ${
                        task.completed ? 'border-[#222] bg-[#0d0d0d] opacity-50' : 
                        isPast ? 'border-red-900/30 bg-red-950/10 hover:border-red-900/50' : 'border-[#333] bg-[#1a1a1a] hover:border-[#FACC15]'
                      }`}
                      onClick={() => toggleTask(task.id, task.completed)}
                    >
                      <div className="mt-0.5 flex-shrink-0 transition-transform group-hover:scale-110">
                        {task.completed ? (
                          <CheckCircle2 size={22} className="text-[#FACC15]" />
                        ) : (
                          <Circle size={22} className={isPast ? 'text-red-500' : 'text-[#555] group-hover:text-[#FACC15]'} />
                        )}
                      </div>
                      <div className="flex-1 pt-0.5">
                        <h4 className={`font-semibold text-[15px] leading-tight ${task.completed ? 'line-through text-[#666]' : 'text-[#eee]'}`}>
                          {task.title}
                        </h4>
                        {task.description && (
                          <p className={`text-sm mt-2 line-clamp-2 ${task.completed ? 'text-[#555]' : 'text-[#888]'}`}>{task.description}</p>
                        )}
                      </div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-[#666] whitespace-nowrap bg-[#0d0d0d] px-3 py-1.5 rounded-lg border border-[#222]">
                        {dateObj.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #333;
          border-radius: 20px;
        }
      `}} />
    </div>
  );
}
