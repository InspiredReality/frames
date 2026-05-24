import React, { useRef, useEffect } from 'react';
import ChatBubble from '../components/ChatBubble';
import ChatInput from '../components/ChatInput';
import { useChat } from '../hooks/useChat';
import './Page.css';

const INITIAL = [
  {
    role: 'assistant',
    text: "Welcome to Win. This is where we get strategic and results-focused. What goal are you working toward?"
  }
];

const REPLIES = [
  "Solid goal. Let's break it into steps and make it happen.",
  "That's a win worth chasing. What's blocking you right now?",
  "Good thinking. Winning starts with clarity — you've got that.",
  "Strong. Let's map out what success looks like for this.",
  "Perfect. What's the one thing that would make the biggest difference today?"
];

function getReply(text) {
  return REPLIES[Math.floor(Math.random() * REPLIES.length)];
}

export default function Win() {
  const { messages, typing, sendMessage } = useChat(INITIAL);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="page-title">Win</h1>
        <p className="page-subtitle">Set the goal. Make it real.</p>
      </div>

      <div className="chat-scroll">
        {messages.map((m, i) => (
          <ChatBubble key={i} role={m.role} text={m.text} />
        ))}
        {typing && <ChatBubble role="assistant" typing />}
        <div ref={bottomRef} />
      </div>

      <ChatInput onSend={text => sendMessage(text, getReply)} disabled={typing} />
    </div>
  );
}
