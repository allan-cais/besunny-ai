import React, { createContext, useContext, useState, useEffect } from 'react';
import { useProject } from './ProjectProvider';
import { api } from '../lib/apiClient';
import type { ChatSession, ChatMessage } from '../types/chat';

interface ChatContextType {
  currentSession: ChatSession | null;
  sessions: ChatSession[];
  loading: boolean;
  sendMessage: (message: string) => Promise<void>;
  createSession: (title?: string) => Promise<ChatSession>;
  setCurrentSession: (session: ChatSession | null) => void;
  refreshSessions: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: React.ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const { currentProject } = useProject();
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchSessions = async () => {
    if (!currentProject) return;
    
    setLoading(true);
    try {
      const response = await api.getChatHistory(currentProject.id);
      setSessions(response.data || []);
      
      // Set first session as current if none selected
      if (!currentSession && response.data && response.data.length > 0) {
        setCurrentSession(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching chat sessions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, [currentProject]);

  const createSession = async (title?: string): Promise<ChatSession> => {
    if (!currentProject) {
      throw new Error('No project selected');
    }

    const newSession: ChatSession = {
      id: `temp-${Date.now()}`,
      project_id: currentProject.id,
      title: title || `Chat ${sessions.length + 1}`,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [],
    };

    setSessions(prev => [newSession, ...prev]);
    setCurrentSession(newSession);
    
    return newSession;
  };

  const sendMessage = async (message: string) => {
    if (!currentProject || !currentSession) {
      throw new Error('No project or session selected');
    }

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      content: message,
      role: 'user',
      timestamp: new Date().toISOString(),
    };

    // Add user message to current session
    const updatedSession = {
      ...currentSession,
      messages: [...currentSession.messages, userMessage],
      updated_at: new Date().toISOString(),
    };

    setCurrentSession(updatedSession);
    setSessions(prev => 
      prev.map(s => s.id === currentSession.id ? updatedSession : s)
    );

    try {
      const response = await api.sendMessage(currentProject.id, message, {
        sessionId: currentSession.id,
      });

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        content: response.data?.response || 'Sorry, I could not process your request.',
        role: 'assistant',
        timestamp: new Date().toISOString(),
        metadata: response.data?.metadata,
      };

      const finalSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, assistantMessage],
        updated_at: new Date().toISOString(),
      };

      setCurrentSession(finalSession);
      setSessions(prev => 
        prev.map(s => s.id === currentSession.id ? finalSession : s)
      );
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        content: 'Sorry, there was an error processing your request.',
        role: 'assistant',
        timestamp: new Date().toISOString(),
      };

      const errorSession = {
        ...updatedSession,
        messages: [...updatedSession.messages, errorMessage],
        updated_at: new Date().toISOString(),
      };

      setCurrentSession(errorSession);
      setSessions(prev => 
        prev.map(s => s.id === currentSession.id ? errorSession : s)
      );
    }
  };

  const refreshSessions = async () => {
    await fetchSessions();
  };

  const value = {
    currentSession,
    sessions,
    loading,
    sendMessage,
    createSession,
    setCurrentSession,
    refreshSessions,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
}; 