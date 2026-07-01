'use client';

import { useState, useEffect } from 'react';
import { api, PredictionResponse, UserStats, StudyTask } from '@/lib/api';
import { Brain, Calendar, CheckCircle2, Circle, Flame, Target, Trophy, Clock } from 'lucide-react';
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
      <div className="flex h-screen w-full items-center justify-center bg-[#0a0a0f]">
        <div className="animate-pulse text-xl text-[#00cec9]">Loading StudyOS Dashboard...</div>
      </div>
    );
  }

  // Calculate circumference for circular progress
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const score = prediction?.readiness_score || 0;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white font-sans p-8 flex flex-col items-center">
      
      {/* HEADER */}
      <header className="w-full max-w-6xl flex justify-between items-center mb-10">
        <div>
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-[#6c5ce7] to-[#00cec9]">
            Progress Dashboard
          </h1>
          <p className="text-gray-400 mt-2">Track your exam readiness and manage your study plans.</p>
        </div>
        <Link href="/" className="px-6 py-2 rounded-full bg-[#12121a] border border-[#2a2a35] hover:border-[#6c5ce7] transition-all text-sm font-medium">
          ← Back to Notebook
        </Link>
      </header>

      <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* LEFT COLUMN: Readiness & Stats */}
        <div className="col-span-1 space-y-8">
          
          {/* Readiness Score Card */}
          <div className="bg-[#12121a] rounded-3xl p-8 border border-[#2a2a35] flex flex-col items-center relative overflow-hidden group">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#6c5ce7] to-[#00cec9] opacity-50 group-hover:opacity-100 transition-opacity" />
            <h2 className="text-lg font-medium text-gray-300 mb-6 w-full flex items-center gap-2">
              <Target size={20} className="text-[#00cec9]" /> Exam Readiness
            </h2>
            
            <div className="relative flex items-center justify-center w-40 h-40">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="80" cy="80" r={radius} stroke="#2a2a35" strokeWidth="12" fill="transparent" />
                <circle
                  cx="80" cy="80" r={radius}
                  stroke="url(#gradient)" strokeWidth="12" fill="transparent"
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  className="transition-all duration-1000 ease-out"
                  strokeLinecap="round"
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#6c5ce7" />
                    <stop offset="100%" stopColor="#00cec9" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute flex flex-col items-center">
                <span className="text-4xl font-bold">{score}</span>
                <span className="text-xs text-gray-400">/ 100</span>
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <div className="text-xl font-semibold mb-1" style={{ color: score >= 70 ? '#00cec9' : score >= 50 ? '#f39c12' : '#e74c3c'}}>
                {prediction?.readiness_band || 'Unknown'}
              </div>
              <p className="text-sm text-gray-400">Pass Probability: {((prediction?.pass_probability || 0) * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#12121a] rounded-2xl p-5 border border-[#2a2a35]">
              <div className="flex justify-between items-start mb-2">
                <Brain size={20} className="text-[#6c5ce7]" />
                <span className="text-2xl font-bold">{Math.round((stats?.quiz_accuracy || 0) * 100)}%</span>
              </div>
              <p className="text-sm text-gray-400">Quiz Accuracy</p>
            </div>
            <div className="bg-[#12121a] rounded-2xl p-5 border border-[#2a2a35]">
              <div className="flex justify-between items-start mb-2">
                <Trophy size={20} className="text-[#00cec9]" />
                <span className="text-2xl font-bold">{Math.round((stats?.task_completion || 0) * 100)}%</span>
              </div>
              <p className="text-sm text-gray-400">Task Completion</p>
            </div>
            <div className="bg-[#12121a] rounded-2xl p-5 border border-[#2a2a35] col-span-2 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-[#6c5ce7]/10 text-[#6c5ce7]">
                  <Flame size={24} />
                </div>
                <div>
                  <p className="text-sm text-gray-400">Study Streak</p>
                  <p className="text-xl font-bold">{stats?.study_streak || 0} Days</p>
                </div>
              </div>
            </div>
          </div>

          {/* Insights */}
          {prediction?.insights && prediction.insights.length > 0 && (
            <div className="bg-[#12121a] rounded-3xl p-6 border border-[#2a2a35]">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-400 mb-4">AI Insights</h3>
              <ul className="space-y-3">
                {prediction.insights.map((insight, idx) => (
                  <li key={idx} className="flex gap-3 text-sm text-gray-300 bg-[#1a1a24] p-3 rounded-xl border border-[#2a2a35]">
                    <span className="text-[#6c5ce7]">✦</span>
                    {insight}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: Study Planner */}
        <div className="col-span-1 md:col-span-2 space-y-8">
          
          {/* Plan Generator Form */}
          <div className="bg-[#12121a] rounded-3xl p-8 border border-[#2a2a35]">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Calendar size={22} className="text-[#6c5ce7]" /> Generate Study Plan
            </h2>
            <div className="flex flex-col md:flex-row gap-4">
              <input
                type="text"
                placeholder="Topics (e.g. Thermodynamics, ML Basics)"
                value={newTopic}
                onChange={e => setNewTopic(e.target.value)}
                className="flex-1 bg-[#0a0a0f] border border-[#2a2a35] rounded-xl px-4 py-3 focus:outline-none focus:border-[#6c5ce7] transition-colors"
              />
              <input
                type="date"
                value={targetDate}
                onChange={e => setTargetDate(e.target.value)}
                className="bg-[#0a0a0f] border border-[#2a2a35] rounded-xl px-4 py-3 focus:outline-none focus:border-[#6c5ce7] transition-colors [color-scheme:dark]"
              />
              <button
                onClick={handleGeneratePlan}
                disabled={isGenerating || !newTopic || !targetDate}
                className="bg-gradient-to-r from-[#6c5ce7] to-[#00cec9] text-white px-8 py-3 rounded-xl font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
              >
                {isGenerating ? 'Generating...' : 'Build Plan'}
              </button>
            </div>
          </div>

          {/* Tasks List */}
          <div className="bg-[#12121a] rounded-3xl p-8 border border-[#2a2a35] min-h-[400px]">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <CheckCircle2 size={22} className="text-[#00cec9]" /> Your Study Tasks
            </h2>
            
            {tasks.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-gray-500">
                <Clock size={32} className="mb-3 opacity-50" />
                <p>No active study tasks.</p>
                <p className="text-sm">Generate a plan above to get started.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {tasks.map(task => {
                  const dateObj = new Date(task.scheduled_date);
                  const isPast = dateObj < new Date() && !task.completed;
                  return (
                    <div 
                      key={task.id} 
                      className={`flex items-start gap-4 p-4 rounded-2xl border transition-all cursor-pointer hover:bg-[#1a1a24] ${
                        task.completed ? 'border-[#2a2a35] bg-[#0a0a0f]/50 opacity-60' : 
                        isPast ? 'border-red-900/50 bg-red-900/10' : 'border-[#2a2a35] bg-[#1a1a24]'
                      }`}
                      onClick={() => toggleTask(task.id, task.completed)}
                    >
                      <div className="mt-1 flex-shrink-0">
                        {task.completed ? (
                          <CheckCircle2 size={24} className="text-[#00cec9]" />
                        ) : (
                          <Circle size={24} className={isPast ? 'text-red-500' : 'text-gray-500'} />
                        )}
                      </div>
                      <div className="flex-1">
                        <h4 className={`font-medium text-lg ${task.completed ? 'line-through text-gray-500' : ''}`}>
                          {task.title}
                        </h4>
                        {task.description && (
                          <p className="text-sm text-gray-400 mt-1 line-clamp-2">{task.description}</p>
                        )}
                      </div>
                      <div className="text-xs font-medium text-gray-500 whitespace-nowrap bg-[#0a0a0f] px-3 py-1 rounded-full border border-[#2a2a35]">
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
    </div>
  );
}
