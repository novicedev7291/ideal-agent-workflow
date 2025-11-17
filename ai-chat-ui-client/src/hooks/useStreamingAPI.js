import { useState, useCallback } from 'react'

const useStreamingAPI = () => {
  const [isLoading, setIsLoading] = useState(false)

  const isRenderableMarkdown = (text) => {
    const codeBlockMatches = text.match(/```/g)
    if (codeBlockMatches && codeBlockMatches.length % 2 !== 0) {
      return false
    }

    const inlineCodeMatches = text.match(/`/g)
    if (inlineCodeMatches && inlineCodeMatches.length % 2 !== 0) {
      return false
    }

    const boldMatches = text.match(/\*\*/g)
    if (boldMatches && boldMatches.length % 2 !== 0) {
      return false
    }

    return true
  }

  const bufferAndRender = (accumulatedText, buffer, onStreamUpdate) => {
    const combinedText = buffer + accumulatedText
    
    const lastSentenceEnd = Math.max(
      combinedText.lastIndexOf('. '),
      combinedText.lastIndexOf('.\n'),
      combinedText.lastIndexOf('!\n'),
      combinedText.lastIndexOf('?\n')
    )

    if (lastSentenceEnd > 0) {
      const textToRender = combinedText.substring(0, lastSentenceEnd + 1)
      const remainingBuffer = combinedText.substring(lastSentenceEnd + 1)

      if (isRenderableMarkdown(textToRender)) {
        onStreamUpdate(textToRender)
        return remainingBuffer
      }
    }

    if (combinedText.includes('```')) {
      const codeBlockEnd = combinedText.lastIndexOf('```\n')
      if (codeBlockEnd > 0 && combinedText.indexOf('```') < codeBlockEnd) {
        const textToRender = combinedText.substring(0, codeBlockEnd + 4)
        if (isRenderableMarkdown(textToRender)) {
          onStreamUpdate(textToRender)
          return combinedText.substring(codeBlockEnd + 4)
        }
      }
    }

    if (combinedText.length > 100) {
      onStreamUpdate(combinedText)
      return ''
    }

    return combinedText
  }

  const sendMessage = useCallback(async ({ message, sessionId } , onStreamUpdate) => {
    setIsLoading(true)

    console.log(`Request with session_id : ${sessionId}`)
    
    try {
      const API_BASE_URL = 'http://localhost:8000'
      const API_ENDPOINT = '/chat/stream'
      
      const reqBody = { "message": message, "session_id": sessionId }

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

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      let accumulatedText = ''
      let buffer = ''
      let lineBuffer = ''

      let lastUpdateTime = Date.now()
      const UPDATE_INTVL = 100 //ms
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          if (lineBuffer.trim()) {
            try {
              const data = JSON.parse(lineBuffer)
              if (data.role && data.role === 'assistant' && data.content) {
                if (data.mimeType === 'image/png') {
                  onStreamUpdate('', data.content, data.mimeType)
                } else if (data.content !== 'START' && data.content !== 'END') {
                  buffer += data.content
                }
              }
            } catch (e) {
              console.warn('Failed to parse remaining line', lineBuffer, e)
            }
          }
          if(buffer) {
            onStreamUpdate(accumulatedText + buffer, null, null)
          }
          break
        }
        
        const chunk = decoder.decode(value, { stream: true })
        lineBuffer += chunk

        const lines = lineBuffer.split('\n')
        lineBuffer = lines.pop() || ''
        
        for (const line of lines) {
          if (line.trim() === '') continue
          
          try {
            const data = JSON.parse(line)
            if (data.role && data.role === 'assistant' 
                && data.content 
                && (data.content !== 'START' && data.content !== 'END')) {

              //TODO: Remove hardcoding png
              if (data.mimeType == 'image/png') {
                onStreamUpdate('', data.content, data.mimeType)
                continue
              }

              buffer += data.content

              const currentTime = Date.now()
              const shouldUpdate = currentTime - lastUpdateTime >= UPDATE_INTVL

              if (shouldUpdate && buffer.length > 0) {
                const testText  = accumulatedText + buffer

                if (isRenderableMarkdown(testText) || buffer.length > 150) {
                  accumulatedText = testText
                  onStreamUpdate(accumulatedText, null, data.mimeType)
                  buffer = ''
                  lastUpdateTime = currentTime
                }
              }
            }
          } catch (e) {
            console.warn('Failed to parse line', line, e)
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