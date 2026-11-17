import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Shield, Zap, Brain } from 'lucide-react'
import { fadeInUp, staggerContainer } from '../constants/animations'

export const HeroSection = () => {
  const features = [
    { icon: Brain, label: 'AI-Powered', color: 'from-blue-500 to-cyan-500' },
    { icon: Shield, label: 'Secure', color: 'from-purple-500 to-pink-500' },
    { icon: Zap, label: 'Instant', color: 'from-cyan-500 to-blue-500' }
  ]

  return (
    <div className="relative min-h-screen pt-32 pb-20">
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8"
      >
        {/* Hero Badge */}
        <motion.div 
          variants={fadeInUp}
          className="flex justify-center"
        >
          <div className="relative inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 backdrop-blur-xl">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            >
              <Sparkles className="h-4 w-4 text-cyan-400" />
            </motion.div>
            <span className="text-sm font-medium text-gray-300">
              Powered by Advanced AI
            </span>
          </div>
        </motion.div>

        {/* Main Heading */}
        <motion.div variants={fadeInUp} className="mt-8 text-center">
          <h1 className="text-5xl font-bold tracking-tight text-white sm:text-6xl lg:text-7xl">
            <span className="block">HR Policy Intelligence</span>
            <span className="mt-2 block bg-gradient-to-r from-blue-400 via-cyan-400 to-purple-400 bg-clip-text text-transparent">
              Simplified
            </span>
          </h1>
        </motion.div>

        {/* Subtitle */}
        <motion.p 
          variants={fadeInUp}
          className="mx-auto mt-6 max-w-2xl text-center text-lg text-gray-400 sm:text-xl"
        >
          Ask questions about company policies and get instant, accurate answers 
          powered by advanced AI. Your personal HR assistant, available 24/7.
        </motion.p>

        {/* Feature Pills */}
        <motion.div 
          variants={fadeInUp}
          className="mt-10 flex flex-wrap justify-center gap-4"
        >
          {features.map((feature, index) => (
            <motion.div
              key={feature.label}
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 + 0.5 }}
              whileHover={{ scale: 1.05, y: -2 }}
              className="group relative overflow-hidden rounded-full border border-white/10 bg-white/5 px-6 py-3 backdrop-blur-xl"
            >
              <div className="flex items-center gap-2">
                <div className={`rounded-full bg-gradient-to-br ${feature.color} p-2`}>
                  <feature.icon className="h-4 w-4 text-white" />
                </div>
                <span className="text-sm font-medium text-white">{feature.label}</span>
              </div>
              <motion.div
                className={`absolute inset-0 bg-gradient-to-r ${feature.color} opacity-0 transition-opacity group-hover:opacity-10`}
              />
            </motion.div>
          ))}
        </motion.div>

        {/* CTA Buttons */}
        <motion.div 
          variants={fadeInUp}
          className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <motion.button
            whileHover={{ scale: 1.05, boxShadow: '0 0 30px rgba(59, 130, 246, 0.5)' }}
            whileTap={{ scale: 0.95 }}
            onClick={() => {
              document.getElementById('chat-interface')?.scrollIntoView({ behavior: 'smooth' })
            }}
            className="group relative inline-flex items-center gap-2 overflow-hidden rounded-xl px-8 py-4 text-base font-semibold text-white"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600" />
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 opacity-0 blur-xl transition-opacity group-hover:opacity-100" />
            <span className="relative">Start Chatting</span>
            <ArrowRight className="relative h-5 w-5 transition-transform group-hover:translate-x-1" />
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-8 py-4 text-base font-semibold text-white backdrop-blur-xl hover:bg-white/10"
          >
            Learn More
          </motion.button>
        </motion.div>

        {/* Floating Glass Card */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.8 }}
          className="mx-auto mt-16 max-w-4xl"
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-2xl shadow-glass-lg"
          >
            {/* Glow effect */}
            <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-blue-500/20 blur-3xl" />
            <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-purple-500/20 blur-3xl" />
            
            <div className="relative">
              <div className="mb-6 flex items-center gap-3">
                <div className="h-3 w-3 rounded-full bg-red-500" />
                <div className="h-3 w-3 rounded-full bg-yellow-500" />
                <div className="h-3 w-3 rounded-full bg-green-500" />
              </div>
              
              <div className="space-y-4">
                {/* Example Query */}
                <div className="flex justify-end">
                  <div className="max-w-md rounded-2xl rounded-tr-sm bg-gradient-to-br from-blue-600 to-cyan-600 px-6 py-3">
                    <p className="text-sm text-white">
                      What is the remote work policy?
                    </p>
                  </div>
                </div>

                {/* Example Response */}
                <div className="flex justify-start">
                  <div className="max-w-lg rounded-2xl rounded-tl-sm border border-white/10 bg-white/5 px-6 py-4 backdrop-blur-xl">
                    <p className="text-sm text-gray-300 leading-relaxed">
                      According to our Remote and Hybrid Work Policy, employees can work 
                      remotely up to 3 days per week with manager approval. Full details 
                      are available in the Employee Handbook.
                    </p>
                    <div className="mt-3 flex gap-2">
                      <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/20 px-3 py-1 text-xs text-blue-300">
                        📄 Remote Work Policy
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>

        {/* Scroll Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-16 flex justify-center"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="text-gray-500"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </motion.div>
        </motion.div>
      </motion.div>
    </div>
  )
}
