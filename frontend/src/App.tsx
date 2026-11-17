import { AnimatedBackground } from './components/AnimatedBackground'
import { Navbar } from './components/Navbar'
import { HeroSection } from './components/HeroSection'
import { ChatInterface } from './components/ChatInterface'

function App() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground />
      <Navbar />
      <main>
        <HeroSection />
        <ChatInterface />
      </main>
    </div>
  )
}

export default App
