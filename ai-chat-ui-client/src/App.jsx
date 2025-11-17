import React, { useState } from 'react'
import Header from './components/Header'
import ChatArea from './components/ChatArea'
import ChatInput from './components/ChatInput'
import useStreamingAPI from './hooks/useStreamingAPI'
import useSessionAPI from './hooks/useSessionAPI'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [sessionId, createSession] = useSessionAPI()
  const { sendMessage, isLoading } = useStreamingAPI()

  const handleNewChat = () => {
    createSession()
    setMessages([])
  }

  const handleSendMessage = async (messageText) => {
    if (!messageText.trim()) return

    if (!sessionId) {
      createSession()
    }

    // Add user message
    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
      mimeType: 'text/plain'
    }
    
    setMessages(prev => [...prev, userMessage])

    const assistantMessage = {
      id: Date.now() + 1,
      text: '',
      sender: 'assistant',
      timestamp: new Date(), 
      imageData: '',
      mimeType: ''
    }
    
    setMessages(prev => [...prev, assistantMessage])

    try {
      await sendMessage({ 'message': messageText, 'sessionId': sessionId }, (streamedText, imageData, mimeType) => {
        setMessages(prev => 
          prev.map(msg => 
            msg.id === assistantMessage.id 
              ? { ...msg, text: streamedText || msg.text, imageData: imageData || msg.imageData, mimeType: mimeType || msg.mimeType }
              : msg
          )
        )
      })
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => 
        prev.map(msg => 
          msg.id === assistantMessage.id 
            ? { ...msg, text: 'Sorry, I encountered an error. Please try again.' }
            : msg
        )
      )
    }
  }

  return (
    <div className="app">
      <Header onNewChat={handleNewChat} />
      <ChatArea messages={messages} isLoading={isLoading} />
      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}

export default App