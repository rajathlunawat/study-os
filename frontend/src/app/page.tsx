'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { api, Source, ChatResponse, ChatMessage, Subject } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

/* ─── Main Notebook Page ─── */
export default function NotebookPage() {
  const router = useRouter();

  const [subjectId, setSubjectId] = useState<string | null>(null);
  const [subjectName, setSubjectName] = useState<string>('StudyOS Notebook');

  const [sources, setSources] = useState<Source[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load subject on mount
  useEffect(() => {
    const storedId = localStorage.getItem('studyos_subject_id');
    if (storedId) {
      setSubjectId(storedId);
      
      // Fetch subject name for UI
      api.getSubjects().then(subs => {
        const sub = subs.find(s => s.id === storedId);
        if (sub) setSubjectName(sub.name);
      }).catch(console.error);

      // Fetch documents and chat history for this subject
      Promise.all([
        api.getDocuments(storedId),
        api.getChatHistory(storedId)
      ])
      .then(([docs, history]) => {
        setSources(docs);
        setMessages(history);
      })
      .catch(console.error);
    }
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  /* ─── Upload Handler ─── */
  const handleUploadClick = () => {
    if (!subjectId) {
      setUploadError("Please select a subject from the Dashboard first.");
      return;
    }
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !subjectId) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const uploaded = await api.uploadDocument(file, 'notes', subjectId);
      setSources(prev => [...prev, uploaded]);

      // If it's the very first document and chat is empty, simulate a welcome
      if (sources.length === 0 && messages.length === 0) {
        setMessages(prev => [...prev, {
          id: 'sys-welcome',
          subject_id: subjectId,
          role: 'ai',
          content: `I've processed "${file.name}". Ask me anything about this document, or type /quiz to generate a quiz from it.`,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (err: unknown) {
      const msg = (err as { message?: string })?.message || 'Upload failed. Is the backend running?';
      setUploadError(msg);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  /* ─── Chat Handler ─── */
  const handleSendMessage = useCallback(async () => {
    if (!inputValue.trim() || isTyping || !subjectId) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      subject_id: subjectId,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response: ChatResponse = await api.chat(
        subjectId,
        userMsg.content,
        sources.map(s => s.id)
      );

      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        subject_id: subjectId,
        role: 'ai',
        content: response.reply,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        subject_id: subjectId,
        role: 'ai',
        content: 'Sorry, I could not reach the backend. Please ensure the API server is running and NEXT_PUBLIC_API_URL is set.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  }, [inputValue, isTyping, sources, subjectId]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  /* ─── Delete Source ─── */
  const handleDeleteSource = async (id: string) => {
    try {
      await api.deleteDocument(id);
      setSources(prev => prev.filter(s => s.id !== id));
    } catch {
      // Silently fail — source might already be removed
    }
  };

  return (
    <div className="app-container">

      {/* ─── LEFT SIDEBAR (SOURCES) ─── */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div style={{ fontSize: '24px' }}>🎓</div>
          <div className="sidebar-title truncate">{subjectName}</div>
        </div>

        <div className="sidebar-content">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            style={{ display: 'none' }}
            accept=".pdf,.txt,.docx"
          />
          <button
            className="upload-button"
            onClick={handleUploadClick}
            disabled={isUploading || !subjectId}
            style={{ marginBottom: '12px', opacity: !subjectId ? 0.5 : 1 }}
          >
            {isUploading ? '⏳ Uploading...' : '⊕ Add Notes / Chapters'}
          </button>
          
          <Link href="/dashboard" style={{ display: 'block', textDecoration: 'none' }}>
            <button
              className="upload-button"
              style={{
                background: '#FACC15',
                border: 'none',
                color: '#0d0d0d',
                fontWeight: 'bold',
                boxShadow: '0 4px 14px rgba(250, 204, 21, 0.2)'
              }}
            >
              📊 View Dashboard
            </button>
          </Link>

          {uploadError && (
            <p style={{ fontSize: '12px', color: '#e74c3c', marginBottom: '12px', marginTop: '12px' }}>
              {uploadError}
            </p>
          )}

          <div style={{ marginTop: '24px' }}>
            <h3 style={{
              fontSize: '12px',
              textTransform: 'uppercase',
              color: 'var(--text-tertiary)',
              letterSpacing: '1px',
              marginBottom: '12px',
              fontWeight: 600,
            }}>
              Subject Materials ({sources.length})
            </h3>

            {sources.length === 0 ? (
              <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                No materials uploaded yet.
              </p>
            ) : (
              sources.map(source => (
                <div key={source.id} className="source-item">
                  <div className="source-icon">📄</div>
                  <div className="source-details">
                    <span className="source-name" title={source.title}>{source.title}</span>
                    <span className="source-meta">{source.file_type} · {source.status || 'ready'}</span>
                  </div>
                  <button
                    onClick={() => handleDeleteSource(source.id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      fontSize: '14px',
                      color: 'var(--text-tertiary)',
                      padding: '4px',
                    }}
                    title="Remove source"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>

      {/* ─── MAIN AREA (CHAT) ─── */}
      <main className="main-area">
        {!subjectId ? (
          /* Empty State No Subject */
          <div className="empty-state">
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📂</div>
            <h2>No Subject Selected</h2>
            <p>
              Please go to the Dashboard and select or create a custom subject (e.g. DSA, EGD, IS) to start tracking your performance.
            </p>
            <Link href="/dashboard" style={{ textDecoration: 'none' }}>
              <button
                className="upload-button"
                style={{
                  marginTop: '24px',
                  background: '#FACC15',
                  color: '#111',
                  border: 'none',
                  fontWeight: 600,
                }}
              >
                Go to Dashboard
              </button>
            </Link>
          </div>
        ) : sources.length === 0 && messages.length === 0 ? (
          /* Empty State No Docs */
          <div className="empty-state">
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📚</div>
            <h2>Welcome to {subjectName}</h2>
            <p>
              Upload chapters, lecture notes, or previous year question papers to create a personalized AI-powered study notebook for this subject.
            </p>
            <button
              className="upload-button"
              style={{
                marginTop: '24px',
                background: 'var(--accent-blue)',
                color: '#fff',
                border: 'none',
                fontWeight: 600,
              }}
              onClick={handleUploadClick}
            >
              Upload Your First Document
            </button>
          </div>
        ) : (
          /* Active Chat Interface */
          <>
            <div className="chat-container">
              {messages.map(msg => (
                <div key={msg.id} className={`message-row ${msg.role}`}>
                  <div className="message-bubble">
                    {msg.role === 'ai' ? (
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="message-row ai">
                  <div className="message-bubble" style={{ color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                    Thinking…
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div className="input-area">
              <div className="input-container">
                <input
                  type="text"
                  className="chat-input"
                  placeholder="Ask about your sources, or type /quiz or /flashcards to test yourself…"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                />
                <button
                  className="send-button"
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isTyping}
                  aria-label="Send message"
                >
                  ↑
                </button>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
