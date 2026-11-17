import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { Message } from '../types/chat'
import { chatService } from '../services/chatService'
import { MessageBubble } from './MessageBubble'
import { fadeInUp } from '../constants/animations'

export const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiReady, setApiReady] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    checkApiHealth()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const checkApiHealth = async () => {
    const isHealthy = await chatService.getHealthStatus()
    setApiReady(isHealthy)
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!input.trim() || loading || !apiReady) {
      return
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await chatService.sendMessage(input, messages)

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        sources: response.sources
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      }

      setMessages((prev) => [...prev, errorMessage])
      console.error('Error:', error)
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div id="chat-interface" className="relative min-h-screen py-20">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8 text-center"
        >
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            Ask Your Questions
          </h2>
          <p className="mt-3 text-gray-400">
            Get instant answers about company policies and procedures
          </p>
          
          {/* API Status Badge */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-4 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-xl"
          >
            {apiReady ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-green-400" />
                <span className="text-sm text-green-400">Connected</span>
              </>
            ) : (
              <>
                <XCircle className="h-4 w-4 text-red-400" />
                <span className="text-sm text-red-400">Disconnected</span>
              </>
            )}
          </motion.div>
        </motion.div>

        {/* Chat Container */}
        <motion.div
          variants={fadeInUp}
          initial="hidden"
          animate="visible"
          className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 backdrop-blur-2xl shadow-glass-lg"
        >
          {/* Glow effect */}
          <div className="absolute -top-40 right-0 h-80 w-80 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="absolute -bottom-40 left-0 h-80 w-80 rounded-full bg-purple-500/10 blur-3xl" />

          <div className="relative">
            {/* Messages Area */}
            <div className="h-[600px] overflow-y-auto p-6 space-y-6">
              {messages.length === 0 && (
                <WelcomeScreen />
              )}

              <AnimatePresence mode="popLayout">
                {messages.map((message, index) => (
                  <MessageBubble 
                    key={message.id} 
                    message={message}
                    index={index}
                  />
                ))}
              </AnimatePresence>

              {loading && <TypingIndicator />}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="border-t border-white/10 bg-white/5 p-6 backdrop-blur-xl">
              <form onSubmit={handleSendMessage} className="flex gap-3">
                <div className="relative flex-1">
                  <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={apiReady ? 'Ask about HR policies...' : 'Connecting to backend...'}
                    disabled={loading || !apiReady}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-6 py-4 text-white placeholder-gray-500 backdrop-blur-xl focus:border-blue-500/50 focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50"
                  />
                </div>

                <motion.button
                  type="submit"
                  disabled={loading || !apiReady || !input.trim()}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="relative overflow-hidden rounded-xl bg-gradient-to-r from-blue-600 to-cyan-600 px-6 py-4 font-semibold text-white shadow-glow transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Send className="h-5 w-5" />
                  )}
                </motion.button>
              </form>

              <p className="mt-3 text-center text-xs text-gray-500">
                AI can make mistakes. Please verify important information.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}

const WelcomeScreen = () => {
  const suggestions = [
    'What is the remote work policy?',
    'How do I submit an expense report?',
    'What are the vacation days policy?',
    'Tell me about the performance review process'
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center py-12 text-center"
    >
      <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500">
        <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>

      <h3 className="mb-2 text-xl font-semibold text-white">
        Start a Conversation
      </h3>
      <p className="mb-6 text-gray-400">
        Try asking one of these questions
      </p>

      <div className="grid gap-3 sm:grid-cols-2">
        {suggestions.map((suggestion, index) => (
          <motion.button
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-left text-sm text-gray-300 backdrop-blur-xl hover:bg-white/10 hover:text-white"
          >
            {suggestion}
          </motion.button>
        ))}
      </div>
    </motion.div>
  )
}

const TypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex justify-start"
    >
      <div className="rounded-2xl rounded-tl-sm border border-white/10 bg-white/5 px-6 py-4 backdrop-blur-xl">
        <div className="flex gap-1">
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0 }}
            className="h-2 w-2 rounded-full bg-blue-400"
          />
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
            className="h-2 w-2 rounded-full bg-cyan-400"
          />
          <motion.div
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
            className="h-2 w-2 rounded-full bg-purple-400"
          />
        </div>
      </div>
    </motion.div>
  )
}
