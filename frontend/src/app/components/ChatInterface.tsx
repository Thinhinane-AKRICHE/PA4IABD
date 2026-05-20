'use client';

import { useState, useRef, useEffect } from 'react';
import { TravelBuddyAPI } from '../lib/api';
import type { ChatResponse, ToolUsed } from '../lib/types';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai' | 'typing';
  timestamp: Date;
  toolsUsed?: ToolUsed[]; // ✅ Utilise le type ToolUsed au lieu de string[]
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Bonjour ! Je suis votre assistant voyage intelligent. Comment puis-je vous aider aujourd'hui ?",
      sender: 'ai',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    checkApiStatus();
  }, []);

  const checkApiStatus = async () => {
    const status = await TravelBuddyAPI.healthCheck();
    setApiStatus(status.status === 'healthy' ? 'online' : 'offline');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    const message = inputValue.trim();
    if (!message || isLoading) return;

    const userMessage: Message = {
      id: Date.now(),
      text: message,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const typingId = Date.now() + 1;
    setMessages(prev => [...prev, {
      id: typingId,
      text: '',
      sender: 'typing',
      timestamp: new Date()
    }]);

    try {
      const response: ChatResponse = await TravelBuddyAPI.chat(message, 1, threadId);
      
      if (response.thread_id) {
        setThreadId(response.thread_id);
      }

      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== typingId);
        return [...filtered, {
          id: Date.now() + 2,
          text: response.response,
          sender: 'ai',
          timestamp: new Date(),
          toolsUsed: response.tools_used // ✅ Maintenant TypeScript accepte cette propriété
        }];
      });

    } catch (error) {
      console.error('Erreur:', error);
      
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== typingId);
        return [...filtered, {
          id: Date.now() + 2,
          text: 'Désolé, je ne peux pas me connecter au serveur pour le moment. Veuillez réessayer.',
          sender: 'ai',
          timestamp: new Date()
        }];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isLoading) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewConversation = async () => {
    try {
      const result = await TravelBuddyAPI.newConversation(1);
      setThreadId(result.thread_id);
      setMessages([
        {
          id: Date.now(),
          text: "Nouvelle conversation démarrée ! Comment puis-je vous aider ?",
          sender: 'ai',
          timestamp: new Date()
        }
      ]);
    } catch (error) {
      console.error('Erreur lors de la création de conversation:', error);
    }
  };

  const menuItems = [
    { 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ), 
      label: 'Conversations', 
      active: true 
    },
    { 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ), 
      label: 'Destinations' 
    },
    { 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ), 
      label: 'Mes voyages' 
    },
    { 
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      ), 
      label: 'Favoris' 
    },
  ];

  return (
    <div className="flex h-screen bg-[#F5F5F0]">
      {/* Sidebar */}
      <aside className={`${isSidebarOpen ? 'w-64' : 'w-16'} bg-white border-r border-[#E5E5DC] transition-all duration-300 flex flex-col`}>
        {/* Logo */}
        <div className="p-4 border-b border-[#E5E5DC] flex items-center justify-between">
          {isSidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-[#D4C5B0] to-[#C4B5A0] rounded-lg flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
              <div>
                <h2 className="font-semibold text-[#2D2D2D] text-sm">TravelBuddy</h2>
                <p className="text-xs text-[#999]">AI Assistant</p>
              </div>
            </div>
          ) : (
            <div className="w-8 h-8 bg-gradient-to-br from-[#D4C5B0] to-[#C4B5A0] rounded-lg flex items-center justify-center mx-auto">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
            </div>
          )}
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            onClick={handleNewConversation}
            className="w-full bg-white hover:bg-[#F5F5F0] border border-[#E5E5DC] rounded-lg p-2.5 flex items-center justify-center gap-2 transition-all duration-200 group"
            title="Nouveau chat"
          >
            <svg className="w-4 h-4 text-[#666]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {isSidebarOpen && <span className="text-[#2D2D2D] text-sm font-medium">Nouveau chat</span>}
          </button>
        </div>

        {/* Menu Items */}
        <nav className="flex-1 px-2 py-2 space-y-1 overflow-y-auto">
          {menuItems.map((item, index) => (
            <button
              key={index}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 ${
                item.active 
                  ? 'bg-[#F5F5F0] text-[#2D2D2D]' 
                  : 'text-[#666] hover:bg-[#F5F5F0] hover:text-[#2D2D2D]'
              }`}
              title={!isSidebarOpen ? item.label : undefined}
            >
              <span className={isSidebarOpen ? '' : 'mx-auto'}>{item.icon}</span>
              {isSidebarOpen && <span className="text-sm font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* User Profile */}
        <div className="border-t border-[#E5E5DC]">
          <button className="w-full p-3 flex items-center gap-3 hover:bg-[#F5F5F0] transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#C4B5A0] to-[#B4A590] flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            {isSidebarOpen && (
              <div className="flex-1 text-left">
                <p className="text-sm font-medium text-[#2D2D2D]">Utilisateur</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${apiStatus === 'online' ? 'bg-green-500' : 'bg-red-400'}`}></div>
                  <span className="text-xs text-[#999]">
                    {apiStatus === 'online' ? 'En ligne' : 'Hors ligne'}
                  </span>
                </div>
              </div>
            )}
            {isSidebarOpen && (
              <svg className="w-4 h-4 text-[#999]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            )}
          </button>
        </div>

        {/* Toggle Sidebar */}
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="p-3 border-t border-[#E5E5DC] hover:bg-[#F5F5F0] transition-colors flex items-center justify-center"
          title={isSidebarOpen ? 'Réduire' : 'Agrandir'}
        >
          <svg className={`w-4 h-4 text-[#666] transition-transform ${isSidebarOpen ? '' : 'rotate-180'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </svg>
        </button>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.sender === 'typing' ? (
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#D4C5B0] to-[#C4B5A0] flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                      </svg>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-3 bg-white rounded-2xl border border-[#E5E5DC]">
                      <div className="flex gap-1">
                        <span className="w-2 h-2 bg-[#999] rounded-full animate-bounce"></span>
                        <span className="w-2 h-2 bg-[#999] rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                        <span className="w-2 h-2 bg-[#999] rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={`max-w-[85%] ${message.sender === 'user' ? '' : 'flex gap-3'}`}>
                    {/* AI Avatar */}
                    {message.sender === 'ai' && (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#D4C5B0] to-[#C4B5A0] flex items-center justify-center flex-shrink-0 mt-1">
                        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                        </svg>
                      </div>
                    )}

                    <div className="flex-1 min-w-0">
                      <div className={`px-4 py-3 rounded-2xl ${
                        message.sender === 'user'
                          ? 'bg-[#2D2D2D] text-white'
                          : 'bg-white border border-[#E5E5DC] text-[#2D2D2D]'
                      }`}>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                          {message.text}
                        </p>

                        {message.toolsUsed && message.toolsUsed.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-[#E5E5DC] flex flex-wrap gap-2">
                            {message.toolsUsed.map((tool, i) => (
                              <span key={i} className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#F5F5F0] rounded-full text-xs text-[#666]">
                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                </svg>
                                {tool.name} {/* ✅ Affichage du nom de l'outil */}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      
                      {message.sender === 'user' && (
                        <div className="mt-1.5 px-1 flex items-center justify-end gap-2">
                          <span className="text-xs text-[#999]">
                            {new Date(message.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[#B4A590] to-[#A49580] flex items-center justify-center">
                            <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-[#E5E5DC] bg-white">
          <div className="max-w-3xl mx-auto px-4 py-4">
            <div className="relative flex items-end gap-2 bg-white border border-[#E5E5DC] rounded-2xl p-2 focus-within:border-[#C4B5A0] transition-colors shadow-sm">
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Posez votre question sur vos prochains voyages..."
                disabled={isLoading}
                rows={1}
                className="flex-1 px-3 py-2.5 bg-transparent resize-none focus:outline-none text-[#2D2D2D] text-sm placeholder-[#999] disabled:opacity-50 max-h-32"
                style={{
                  minHeight: '40px',
                  maxHeight: '128px'
                }}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement;
                  target.style.height = 'auto';
                  target.style.height = Math.min(target.scrollHeight, 128) + 'px';
                }}
              />
              
              <button
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim()}
                className="p-2.5 bg-[#2D2D2D] text-white rounded-xl hover:bg-[#1a1a1a] disabled:opacity-50 disabled:cursor-not-allowed transition-all flex-shrink-0 shadow-sm hover:shadow-md"
                title="Envoyer"
              >
                {isLoading ? (
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
            
            <p className="mt-3 text-xs text-center text-[#999]">
              TravelBuddy peut faire des erreurs. Vérifiez les informations importantes.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}