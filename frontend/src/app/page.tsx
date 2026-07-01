'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { api, Source, ChatResponse } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import Link from 'next/link';

/* ─── Types ─── */
interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
}

/* ─── Main Notebook Page ─── */
export default function NotebookPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Load existing documents from the API on mount
  useEffect(() => {
    api.getDocuments()
      .then((docs) => setSources(docs))
      .catch(() => {
        // Backend not connected yet — start empty
      });
  }, []);

  // Auto-scroll chat to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  /* ─── Upload Handler ─── */
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      const uploaded = await api.uploadDocument(file, 'notes');
      setSources(prev => [...prev, uploaded]);

      // First document — send a welcome message
      if (sources.length === 0) {
        setMessages([{
          id: 'sys-welcome',
          role: 'ai',
          content: `I've processed "${file.name}". Ask me anything about this document, or type /quiz to generate a quiz from it.`,
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
    if (!inputValue.trim() || isTyping) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response: ChatResponse = await api.chat(
        userMsg.content,
        sources.map(s => s.id)
      );

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: response.reply,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: 'Sorry, I could not reach the backend. Please ensure the API server is running and NEXT_PUBLIC_API_URL is set.',
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsTyping(false);
    }
  }, [inputValue, isTyping, sources]);

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
          <div className="sidebar-title">StudyOS Notebook</div>
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
            disabled={isUploading}
            style={{ marginBottom: '12px' }}
          >
            {isUploading ? '⏳ Uploading...' : '⊕ Add Source'}
          </button>
          
          <Link href="/dashboard" style={{ display: 'block', textDecoration: 'none' }}>
            <button
              className="upload-button"
              style={{
                background: 'transparent',
                border: '1px solid #2a2a35',
                color: 'var(--text-secondary)'
              }}
            >
              📊 View Dashboard
            </button>
          </Link>

          {uploadError && (
            <p style={{ fontSize: '12px', color: '#e74c3c', marginBottom: '12px' }}>
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
              Sources ({sources.length})
            </h3>

            {sources.length === 0 ? (
              <p style={{ fontSize: '13px', color: 'var(--text-tertiary)', fontStyle: 'italic' }}>
                No sources uploaded yet.
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
        {sources.length === 0 && messages.length === 0 ? (
          /* Empty State */
          <div className="empty-state">
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📚</div>
            <h2>Welcome to StudyOS</h2>
            <p>
              Upload your syllabus, lecture notes, or previous year question papers to create a personalized AI-powered study notebook.
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
                  placeholder="Ask about your sources, or type /quiz to test yourself…"
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
