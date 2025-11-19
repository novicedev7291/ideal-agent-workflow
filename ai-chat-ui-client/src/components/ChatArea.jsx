import React, { useEffect, useRef } from 'react'
import Message from './Message'
import './ChatArea.css'

const ChatArea = ({ messages, isLoading }) => {
  const chatContainerRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="chat-area">
      <div className="chat-container" ref={chatContainerRef}>
        {messages.length === 0 ? (
          <div className="empty-state">
            <h2>Welcome to IDEAL</h2>
            <p>Start a conversation by typing below.</p>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message) => (
              <Message 
                key={message.id} 
                message={message} 
                isStreaming={isLoading && message.sender === 'assistant' && message.text === ''}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatArea