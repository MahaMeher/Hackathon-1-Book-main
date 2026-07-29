/**
 * ChatBotAPI.js
 *
 * API client helper for the RAG Chatbot backend.
 * Provides a sendQuery() function that POSTs user questions
 * to the FastAPI backend and returns the parsed response.
 */

const API_BASE_URL = '/api';

/**
 * Send a user query to the RAG chatbot backend.
 *
 * @param {string} query - The user's question (1-5000 chars).
 * @param {string|null} selectedContext - Optional selected text from the book page.
 * @returns {Promise<Object>} A response object with shape:
 *   {status, answer, sources, model_used, execution_time_ms}
 *   On error: {status: 'error', answer: '...', sources: []}
 */
export async function sendQuery(query, selectedContext = null) {
  const body = { query };

  if (selectedContext && selectedContext.trim()) {
    body.selected_context = selectedContext.trim();
  }

  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      let detail = `Server responded with status ${response.status}`;
      try {
        const errorBody = await response.json();
        if (errorBody.detail) {
          detail = errorBody.detail;
        }
      } catch {
        // ignore parse failure — use default message
      }
      return {
        status: 'error',
        answer: detail,
        sources: [],
        model_used: '',
        execution_time_ms: 0,
      };
    }

    return await response.json();
  } catch (err) {
    // Network error (backend unreachable, DNS failure, etc.)
    return {
      status: 'error',
      answer: 'Service is currently unavailable. Please make sure the backend server is running on port 8000 and try again.',
      sources: [],
      model_used: '',
      execution_time_ms: 0,
    };
  }
}
