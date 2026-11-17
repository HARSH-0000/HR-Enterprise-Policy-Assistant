import { ChatRequest, ChatResponse, Message } from '../types/chat'

const API_BASE_URL = '/api'

export const chatService = {
  async sendMessage(query: string, chatHistory?: Message[]): Promise<ChatResponse> {
    try {
      const payload: ChatRequest = {
        query,
        chat_history: chatHistory
      }

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: ChatResponse = await response.json()
      return data
    } catch (error) {
      console.error('Error sending message:', error)
      throw error
    }
  },

  async getHealthStatus(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`, {
        method: 'GET'
      })
      return response.ok
    } catch (error) {
      console.error('Error checking health status:', error)
      return false
    }
  }
}
