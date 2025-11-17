import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { User, Bot, Loader, ZoomIn } from 'lucide-react'
import Lightbox from 'yet-another-react-lightbox'
import 'yet-another-react-lightbox/styles.css'
import './Message.css'

const Message = ({ message, isStreaming }) => {
  const [isLightboxOpen, setIsLightboxOpen] = useState(false) 

  const { text, sender, timestamp, imageData, mimeType } = message

  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  let imageUrl = null

  if (imageData) {
    imageUrl = `data:${mimeType};base64,${imageData}`
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
                <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            code({ node, inline, className, children, ...props }) {
                              const match = /language-(\w+)/.exec(className || '')
                              return !inline && match ? (
                                <SyntaxHighlighter
                                  language={match[1]}
                                  PreTag="div"
                                  {...props}
                                >
                                  {String(children).replace(/\n$/, '')}
                                </SyntaxHighlighter>
                              ) : (
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              )
                            }
                          }}
                        >
                      {text}
                </ReactMarkdown>
            )}
          </div>
          {imageUrl && (
            <div className="message-image-container">
              <div 
                className="message-image-thumbnail"
                onClick={() => setIsLightboxOpen(true)}
                role="button"
                tabIndex={0}
                onKeyPress={(e) => e.key === 'Enter' && setIsLightboxOpen(true)}
              >
                <img 
                  src={imageUrl} 
                  alt="Attached image" 
                  className="thumbnail-image"
                />
                <div className="thumbnail-overlay">
                  <ZoomIn size={24} />
                </div>
              </div>
            </div>
          )}

          <div className="message-time">
            {formatTime(timestamp)}
          </div>
        </div>
      </div>

      {imageUrl && (
        <Lightbox
          open={isLightboxOpen}
          close={() => setIsLightboxOpen(false)}
          slides={[{ src: imageUrl }]}
          render={{
            buttonPrev: () => null,
            buttonNext: () => null,
          }}
        />
      )}
    </div>
  )
}

export default Message