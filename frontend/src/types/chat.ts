export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Source[]
}

export interface Source {
  title: string
  policy_id: string
  page: number
  department: string
  status: string
}

export interface ChatRequest {
  query: string
  chat_history?: Message[]
}

export interface ChatResponse {
  response: string
  sources: Source[]
  usage?: {
    input_tokens: number
    output_tokens: number
  }
}

export interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}
