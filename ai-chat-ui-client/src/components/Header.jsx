import React from 'react'
import { Plus } from 'lucide-react'
import './Header.css'

const Header = ({ onNewChat }) => {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-brand">
          <img
            src="/fil_intl.svg"
            alt="FIL Logo"
            className="header-logo"
          />
          <h1 className="header-title">IDEAL</h1>
        </div>
        <button 
          className="new-chat-button"
          onClick={onNewChat}
          type="button"
        >
          <Plus size={20} />
          New Chat
        </button>
      </div>
    </header>
  )
}

export default Header