import React, { useState, useRef, useEffect } from 'react';
import { sendQuery } from './ChatBotAPI';
import styles from './styles.module.css';

/**
 * ChatBot — a floating chatbot widget for Docusaurus book pages.
 *
 * A bot icon sits at the bottom-right of the screen. Clicking it toggles
 * a chat popup where users can ask questions about the book content.
 */
export default function ChatBot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedContext, setSelectedContext] = useState(null);
  const [selectionPosition, setSelectionPosition] = useState(null);
  const [showTooltip, setShowTooltip] = useState(true);
  const messagesEndRef = useRef(null);
  const tooltipTimer = useRef(null);

  // Show tooltip on first load, hide after 5s
  useEffect(() => {
    tooltipTimer.current = setTimeout(() => setShowTooltip(false), 5000);
    return () => clearTimeout(tooltipTimer.current);
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Listen for custom 'chatbot:ask' event (text selection)
  useEffect(() => {
    const handler = (e) => {
      if (e.detail?.selectedText) {
        setSelectedContext(e.detail.selectedText);
        setSelectionPosition(null);
      }
    };
    window.addEventListener('chatbot:ask', handler);
    return () => window.removeEventListener('chatbot:ask', handler);
  }, []);

  // Detect text selection for floating "Ask" button
  useEffect(() => {
    const handleMouseUp = () => {
      setTimeout(() => {
        const sel = window.getSelection();
        const text = sel ? sel.toString().trim() : '';
        if (text.length > 0) {
          const range = sel.getRangeAt(0);
          const rect = range.getBoundingClientRect();
          setSelectionPosition({
            top: rect.bottom + 4,
            left: rect.left + rect.width / 2,
            text: text.slice(0, 12000),
          });
        } else {
          setSelectionPosition(null);
        }
      }, 0);
    };

    const handleScroll = () => {
      if (selectionPosition) setSelectionPosition(null);
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('scroll', handleScroll);
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('scroll', handleScroll);
    };
  }, [selectionPosition]);

  const handleSelectionAsk = () => {
    if (selectionPosition) {
      setSelectedContext(selectionPosition.text);
      setSelectionPosition(null);
      setIsOpen(true);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      selectedContext: selectedContext || undefined,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const data = await sendQuery(trimmed, selectedContext);
    setSelectedContext(null);

    const isError = data.status === 'error';
    const assistantMsg = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: data.answer || 'Sorry, I could not generate a response.',
      sources: data.sources || [],
      executionTimeMs: data.execution_time_ms,
      error: isError,
      noResults: !isError && (!data.sources || data.sources.length === 0),
    };
    setMessages((prev) => [...prev, assistantMsg]);
    setLoading(false);
  };

  return (
    <>
      {/* Floating "Ask about this selection" button */}
      {selectionPosition && (
        <button
          className={styles['chatbot-selection-btn']}
          style={{
            position: 'fixed',
            top: selectionPosition.top,
            left: selectionPosition.left,
            transform: 'translateX(-50%)',
            zIndex: 1000,
          }}
          onClick={handleSelectionAsk}
          type="button"
        >
          Ask about this selection
        </button>
      )}

      {/* Chat popup */}
      {isOpen && (
        <div className={styles['chatbot-popup']}>
          <div className={styles['chatbot-header']}>
            <div className={styles['chatbot-header-left']}>
              <div className={styles['chatbot-header-icon']}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="3" y="11" width="18" height="10" rx="2" />
                  <circle cx="12" cy="5" r="2" />
                  <path d="M12 7v4" />
                  <line x1="8" y1="16" x2="8" y2="16" />
                  <line x1="16" y1="16" x2="16" y2="16" />
                </svg>
              </div>
              <div>
                <div className={styles['chatbot-header-title']}>Ask the Book</div>
                <div className={styles['chatbot-header-subtitle']}>Powered by RAG</div>
              </div>
            </div>
            <button
              className={styles['chatbot-close-btn']}
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
              type="button"
            >
              &times;
            </button>
          </div>

          <div className={styles['chatbot-messages']}>
            {messages.length === 0 && (
              <div className={styles['chatbot-empty']}>
                <p>Ask a question about the book content.</p>
              </div>
            )}

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`${styles['chatbot-message']} ${
                  msg.role === 'user'
                    ? styles['chatbot-message--user']
                    : styles['chatbot-message--assistant']
                }`}
              >
                <div className={styles['chatbot-message-label']}>
                  {msg.role === 'user' ? 'You' : 'Book Assistant'}
                </div>
                <div className={styles['chatbot-message-content']}>
                  {msg.content}
                </div>
                {msg.error && (
                  <div className={styles['chatbot-error-hint']}>
                    <small>
                      Please check that the backend server is running and try
                      again.
                    </small>
                  </div>
                )}
                {msg.noResults && (
                  <div className={styles['chatbot-no-results']}>
                    <small>
                      No relevant content found in the book. Try rephrasing your
                      question or asking about a different topic.
                    </small>
                  </div>
                )}
                {msg.sources && msg.sources.length > 0 && (
                  <details className={styles['chatbot-sources']}>
                    <summary>Sources ({msg.sources.length})</summary>
                    <ol>
                      {msg.sources.map((src, i) => (
                        <li key={i}>
                          <strong>{src.section}</strong>
                          {src.source_url && (
                            <>
                              {' '}
                              <a
                                href={src.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                view
                              </a>
                            </>
                          )}
                          <br />
                          <small>
                            Relevance: {(src.similarity_score * 100).toFixed(0)}%
                          </small>
                        </li>
                      ))}
                    </ol>
                  </details>
                )}
                {msg.executionTimeMs && (
                  <div className={styles['chatbot-message-meta']}>
                    <small>{(msg.executionTimeMs / 1000).toFixed(1)}s</small>
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div
                className={`${styles['chatbot-message']} ${styles['chatbot-message--assistant']}`}
              >
                <div className={styles['chatbot-message-label']}>
                  Book Assistant
                </div>
                <div className={styles['chatbot-loading']}>
                  <span className={styles['chatbot-loading-dot']} />
                  <span className={styles['chatbot-loading-dot']} />
                  <span className={styles['chatbot-loading-dot']} />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form className={styles['chatbot-input-form']} onSubmit={handleSubmit}>
            {selectedContext && (
              <div className={styles['chatbot-context-bar']}>
                <span>Context from selected text</span>
                <button
                  type="button"
                  className={styles['chatbot-context-clear']}
                  onClick={() => setSelectedContext(null)}
                  aria-label="Clear selected text context"
                >
                  &times;
                </button>
              </div>
            )}
            <div className={styles['chatbot-input-row']}>
              <input
                type="text"
                className={styles['chatbot-input']}
                placeholder={
                  selectedContext
                    ? 'Ask about the selected text...'
                    : 'Ask a question...'
                }
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                aria-label="Chat message input"
              />
              <button
                type="submit"
                className={styles['chatbot-submit']}
                disabled={loading || !input.trim()}
                aria-label="Send message"
              >
                Send
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Floating bot icon + tooltip */}
      <div className={styles['chatbot-fab-container']}>
        {showTooltip && !isOpen && (
          <div className={styles['chatbot-tooltip']}>
            <span>Ask anything about the book</span>
            <div className={styles['chatbot-tooltip-arrow']} />
          </div>
        )}
        <button
          className={styles['chatbot-fab']}
          onClick={() => {
            setIsOpen(!isOpen);
            setShowTooltip(false);
          }}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => {
            if (!isOpen) {
              tooltipTimer.current = setTimeout(() => setShowTooltip(false), 3000);
            }
          }}
          aria-label={isOpen ? 'Close chat' : 'Open chat'}
          type="button"
        >
          {/* Bot icon (simple robot face SVG) */}
          <svg
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <line x1="8" y1="16" x2="8" y2="16" />
            <line x1="16" y1="16" x2="16" y2="16" />
          </svg>
        </button>
      </div>
    </>
  );
}
