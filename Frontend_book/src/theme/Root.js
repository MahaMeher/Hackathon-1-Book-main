import React from 'react';
import ChatBot from '../components/ChatBot';

/**
 * Root — Docusaurus theme wrapper that renders around every page.
 *
 * Adds the ChatBot as a fixed-position panel on book content pages.
 */
export default function Root({ children }) {
  return (
    <>
      {children}
      <ChatBot />
    </>
  );
}
