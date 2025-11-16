import React from 'react'
import { User, Bot, Loader } from 'lucide-react'
import './Message.css'

const Message = ({ message, isStreaming }) => {
  const { text, sender, timestamp } = message

  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  return (
    <div className={`message ${sender === 'user' ? 'user-message' : 'assistant-message'}`}>
      <div className="message-content">
        <div className="message-avatar">
          {sender === 'user' ? (
            <User size={20} />
          ) : (
            <Bot size={20} />
          )}
        </div>
        <div className="message-body">
          <div className="message-text">
            {isStreaming && !text ? (
              <div className="streaming-indicator">
                <Loader size={16} className="spinner" />
                <span>Thinking...</span>
              </div>
            ) : (
              text
            )}
            {text && text.endsWith(' ') === false && sender === 'assistant' && (
              <span className="cursor">|</span>
            )}
          </div>
          <div className="message-time">
            {formatTime(timestamp)}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Message