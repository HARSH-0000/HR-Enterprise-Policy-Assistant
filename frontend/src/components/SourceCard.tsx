import { motion } from 'framer-motion'
import { FileText, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Source } from '../types/chat'

interface SourceCardProps {
  source: Source
  index: number
}

export const SourceCard = ({ source, index }: SourceCardProps) => {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.1, type: 'spring', stiffness: 200 }}
      className="group relative"
    >
      <motion.button
        onClick={() => setIsExpanded(!isExpanded)}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="relative overflow-hidden rounded-lg border border-white/10 bg-white/5 backdrop-blur-xl transition-all hover:border-blue-500/30"
      >
        {/* Glow effect on hover */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-cyan-500/10 opacity-0 transition-opacity group-hover:opacity-100" />
        
        <div className="relative flex items-center gap-2 px-3 py-2">
          <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-blue-500/20 to-cyan-500/20">
            <FileText className="h-3 w-3 text-blue-400" />
          </div>
          <span className="text-xs font-medium text-gray-300">
            {source.title}
          </span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.3 }}
          >
            <ChevronDown className="h-3 w-3 text-gray-500" />
          </motion.div>
        </div>
      </motion.button>

      {/* Expanded Details */}
      <motion.div
        initial={false}
        animate={{
          height: isExpanded ? 'auto' : 0,
          opacity: isExpanded ? 1 : 0
        }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="overflow-hidden"
      >
        <motion.div
          initial={{ y: -10 }}
          animate={{ y: 0 }}
          className="mt-2 rounded-lg border border-white/10 bg-white/5 p-4 backdrop-blur-xl"
        >
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Policy ID:</span>
              <span className="font-mono text-gray-300">{source.policy_id}</span>
            </div>
            {source.page > 0 && (
              <div className="flex items-center justify-between">
                <span className="text-gray-500">Page:</span>
                <span className="text-gray-300">{source.page}</span>
              </div>
            )}
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Department:</span>
              <span className="text-gray-300">{source.department}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-500">Status:</span>
              <span
                className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                  source.status === 'approved'
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-yellow-500/20 text-yellow-400'
                }`}
              >
                {source.status}
              </span>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  )
}
