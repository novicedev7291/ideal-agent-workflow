import { useState, useCallback } from 'react'

const useStreamingAPI = () => {
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async ({ message, sessionId } , onStreamUpdate) => {
    setIsLoading(true)
    
    try {
      const API_BASE_URL = 'http://localhost:8000'
      const API_ENDPOINT = '/chat/stream'
      
      const reqBody = { "message": message, "session_id": sessionId }

      console.info('Sending req : ' + JSON.stringify(reqBody))

      const response = await fetch(API_BASE_URL + API_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reqBody),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      // Handle streaming response
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let accumulatedText = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.trim() === '') continue
          
          try {
            const data = JSON.parse(line)
            if (data.role && data.role === 'assistant' && data.content && (data.content !== 'START' && data.content !== 'END')) {
              accumulatedText += data.content
              onStreamUpdate(accumulatedText)
            }
          } catch (e) {
            // If not JSON, treat the entire line as text
            accumulatedText += line
            onStreamUpdate(accumulatedText)
          }
        }
      }
      
      return accumulatedText
      
    } catch (error) {
      console.error('Streaming API error:', error)
      
      return 'Error reaching agent'
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Mock streaming response for development/demo purposes
  const mockStreamingResponse = async (message, onStreamUpdate) => {
    const responses = [
      "Hello! I'm an AI assistant. I'm here to help you with any questions or tasks you might have.",
      "I understand you said: \"" + message + "\". That's an interesting topic to discuss.",
      "I can help you with various tasks like answering questions, providing information, writing, coding, and much more.",
      "Feel free to ask me anything you'd like to know or any task you'd like assistance with.",
      "I'm designed to be helpful, harmless, and honest in all my interactions."
    ]
    
    const selectedResponse = responses[Math.floor(Math.random() * responses.length)]
    const words = selectedResponse.split(' ')
    let accumulatedText = ''
    
    for (let i = 0; i < words.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 80 + Math.random() * 40)) // Variable delay
      accumulatedText += (i === 0 ? '' : ' ') + words[i]
      onStreamUpdate(accumulatedText)
    }
    
    return accumulatedText
  }

  return {
    sendMessage,
    isLoading
  }
}

export default useStreamingAPI