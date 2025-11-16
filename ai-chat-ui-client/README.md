# AI Chat UI Client

A modern, responsive AI conversational UI built with React and Vite. This application provides a clean chat interface with real-time streaming responses from AI assistants.

## Features

- **Real-time Chat Interface**: Clean and intuitive chat UI with user and assistant message bubbles
- **Streaming Responses**: Support for real-time streaming text tokens from backend API
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **New Chat Functionality**: Easy reset button to start fresh conversations
- **Modern UI**: Clean, professional design with smooth animations
- **Accessibility**: Built with accessibility best practices

## Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Fast build tool and dev server
- **Lucide React** - Beautiful icons
- **CSS3** - Custom styling with flexbox and grid
- **ESLint** - Code linting for quality assurance

## Project Structure

```
src/
  components/
    Header.jsx          # Header with New Chat button
    ChatArea.jsx        # Main chat display area
    ChatInput.jsx       # Input field with send button
    Message.jsx         # Individual message component
  hooks/
    useStreamingAPI.js  # Custom hook for API streaming
  App.jsx               # Main application component
  main.jsx              # Application entry point
  index.css             # Global styles
```

## Getting Started

### Prerequisites

- Node.js (version 16 or higher)
- npm or yarn package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai-chat-ui-client
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm run dev
   ```

4. **Open your browser**
   Navigate to `http://localhost:3000` to see the application

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint for code quality

## API Integration

The application is designed to work with streaming text APIs. To connect to your backend:

1. **Update the API endpoint** in `src/hooks/useStreamingAPI.js`:
   ```javascript
   const API_ENDPOINT = 'https://your-api-endpoint.com/chat/stream'
   ```

2. **Modify the request format** if needed:
   ```javascript
   body: JSON.stringify({ 
     message: message,
     // Add other parameters as needed
   }),
   ```

3. **Adjust the response parsing** based on your API's response format

### Expected API Format

The application expects a streaming response where each chunk contains text tokens. The API can send:

- **JSON Lines**: `{"token": "Hello"}`
- **Plain Text**: Direct text chunks
- **Server-Sent Events**: Standard SSE format

## Customization

### Styling

All component styles are in separate CSS files for easy customization:
- `src/components/Header.css` - Header styles
- `src/components/ChatArea.css` - Chat area and scrollbar styles
- `src/components/Message.css` - Message bubble styles
- `src/components/ChatInput.css` - Input field styles

### Colors and Theme

Update the color scheme in the CSS files:
- Primary color: `#007bff`
- Success color: `#28a745`
- Background: `#f8f9fa`
- Text: `#333`

### Icons

Icons are from Lucide React. You can replace them in the components:
- Send button: `Send` icon
- New chat: `Plus` icon
- User avatar: `User` icon
- Assistant avatar: `Bot` icon

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with React and Vite for optimal performance
- Icons by Lucide React
- Inspired by modern chat interfaces