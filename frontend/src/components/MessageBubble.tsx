import { motion } from 'framer-motion'
import { User, Bot } from 'lucide-react'
import { Message } from '../types/chat'
import { SourceCard } from './SourceCard'

interface MessageBubbleProps {
  message: Message
  index: number
}

export const MessageBubble = ({ message, index }: MessageBubbleProps) => {
  const isUser = message.role === 'user'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{
        duration: 0.4,
        delay: index * 0.05,
        ease: [0.22, 1, 0.36, 1]
      }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* Avatar - Assistant only */}
      {!isUser && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: index * 0.05 + 0.2, type: 'spring', stiffness: 200 }}
          className="flex-shrink-0"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-500 shadow-glow">
            <Bot className="h-5 w-5 text-white" />
          </div>
        </motion.div>
      )}

      {/* Message Content */}
      <div className={`flex max-w-[80%] flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
        <motion.div
          initial={{ scale: 0.9 }}
          animate={{ scale: 1 }}
          transition={{ delay: index * 0.05 + 0.1, type: 'spring', stiffness: 200 }}
          className="relative group"
        >
          {isUser ? (
            // User message
            <div className="relative overflow-hidden rounded-2xl rounded-tr-sm bg-gradient-to-br from-blue-600 to-cyan-600 px-6 py-3 shadow-lg">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 opacity-0 transition-opacity group-hover:opacity-100" />
              <p className="relative whitespace-pre-wrap text-sm leading-relaxed text-white">
                {message.content}
              </p>
            </div>
          ) : (
            // Assistant message
            <div className="relative overflow-hidden rounded-2xl rounded-tl-sm border border-white/10 bg-white/5 px-6 py-4 backdrop-blur-xl">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 transition-opacity group-hover:opacity-100" />
              <p className="relative whitespace-pre-wrap text-sm leading-relaxed text-gray-200">
                {message.content}
              </p>
            </div>
          )}
        </motion.div>

        {/* Sources */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 + 0.3 }}
            className="flex flex-wrap gap-2"
          >
            {message.sources.map((source, idx) => (
              <SourceCard key={idx} source={source} index={idx} />
            ))}
          </motion.div>
        )}

        {/* Timestamp */}
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: index * 0.05 + 0.4 }}
          className="text-xs text-gray-500"
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
          })}
        </motion.span>
      </div>

      {/* Avatar - User only */}
      {isUser && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: index * 0.05 + 0.2, type: 'spring', stiffness: 200 }}
          className="flex-shrink-0"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-full border border-white/20 bg-white/10 backdrop-blur-xl">
            <User className="h-5 w-5 text-white" />
          </div>
        </motion.div>
      )}
    </motion.div>
  )
}
