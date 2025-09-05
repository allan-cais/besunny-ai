import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, ChevronRight, MessageSquare } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { useAuth } from '@/providers/AuthProvider';
import { ChatMessage } from '@/types';
import { v4 as uuidv4 } from 'uuid';
import { config } from '@/config';

interface ProjectChatProps {
  projectId: string;
  userId: string;
  projectName?: string;
}

const ProjectChat: React.FC<ProjectChatProps> = ({ projectId, userId, projectName }) => {
  const { session } = useAuth();
  const [chatMessage, setChatMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(true);
  const [activeChatId, setActiveChatId] = useState<string | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const assistantContainerRef = useRef<HTMLDivElement>(null);

  // Simple chat state management - no complex database operations for now

  // RAG Agent API endpoint
  const RAG_AGENT_API_URL = `${config.pythonBackend.url}/api/v1/rag-agent/query`;

  // Initialize chat automatically when component mounts
  useEffect(() => {
    if (userId && projectId) {
      // Set a default chat ID and show welcome message
      const defaultChatId = `chat_${projectId}_${userId}`;
      setActiveChatId(defaultChatId);
      
      // Add welcome message
      const welcomeMessage: ChatMessage = {
        id: crypto.randomUUID(),
        content: `Hi! I'm Sunny AI, your intelligent assistant for Project "${projectName || 'this project'}". I can answer questions about your project data, emails, documents, and meetings. What would you like to know?`,
        role: "assistant",
        timestamp: new Date().toISOString()
      };
      setMessages([welcomeMessage]);
    }
  }, [userId, projectId, projectName]);

  // Real-time subscription for messages
  useEffect(() => {
    if (!activeChatId) return;

    const supabase = (window as any).supabase;
    if (!supabase) return;

    const subscription = supabase
      .channel(`chat-${activeChatId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'chat_messages',
          filter: `session_id=eq.${activeChatId}`
        },
        (payload: Record<string, unknown>) => {
          if (payload.new) {
            const newMessage = payload.new as ChatMessage;
            setMessages(prev => {
              // Check if message already exists
              const exists = prev.some(msg => msg.id === newMessage.id);
              if (!exists) {
                return [...prev, newMessage];
              }
              return prev;
            });
          }
        }
      )
      .subscribe();

    return () => {
      subscription.unsubscribe();
    };
  }, [activeChatId]);

  const loadMessagesForChat = async (chatId: string) => {
    // Simple local message loading - no database calls for now
    const welcomeMessage: ChatMessage = {
      id: crypto.randomUUID(),
      content: `Hi! I'm Sunny AI, your intelligent assistant for Project "${projectName || 'this project'}". I can answer questions about your project data, emails, documents, and meetings. What would you like to know?`,
      role: "assistant",
      timestamp: new Date().toISOString()
    };
    setMessages([welcomeMessage]);
  };

  const createNewChat = async () => {
    if (!userId) return;
    
    const newId = `chat_${projectId}_${userId}_${Date.now()}`;
    setActiveChatId(newId);
    await loadMessagesForChat(newId);
  };

  const saveMessagesForChat = async (chatId: string, messages: ChatMessage[]) => {
    // Simple local message saving - no database calls for now
    console.log('Messages saved locally:', messages);
  };

  const handleSendMessage = async () => {
    if (chatMessage.trim() && !isLoading) {
      const userMessageText = chatMessage.trim();
      setChatMessage("");
      
      // Create new chat if this is the first message
      if (!activeChatId) {
        await createNewChat();
        // Wait a moment for the chat to be created
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      if (!activeChatId) return;

      // Open chat interface immediately so user can see the message being sent
      setIsCollapsed(false);

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        content: userMessageText,
        role: "user",
        timestamp: new Date().toISOString()
      };
      
      // Add user message immediately
      setMessages(prev => [...prev, userMessage]);
      
      // Add typing indicator after a small delay to feel more natural
      setTimeout(() => {
        const typingMessage: ChatMessage = {
          id: crypto.randomUUID(),
          content: "",
          role: "assistant",
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, typingMessage]);
      }, 500); // 500ms delay
      
      setIsLoading(true);
      
      try {
        // Save user message to database
        await saveMessagesForChat(activeChatId, [userMessage]);
        
        // Send message to RAG Agent API for AI processing
        const ragPayload = {
          question: userMessageText,
          project_id: projectId
        };
        
        console.log("=== FRONTEND RAG REQUEST DEBUG ===");
        console.log("Project ID:", projectId);
        console.log("User ID:", userId);
        console.log("Question:", userMessageText);
        console.log("Payload:", ragPayload);
        console.log("=".repeat(50));
        
        const ragResponse = await fetch(RAG_AGENT_API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session?.access_token}` // Get token from session
          },
          body: JSON.stringify(ragPayload),
        });
        
        if (!ragResponse.ok) {
          throw new Error(`RAG Agent API error: ${ragResponse.status}`);
        }
        
        // Create assistant message with empty content initially
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          content: "",
          role: "assistant",
          timestamp: new Date().toISOString()
        };
        
        // Remove typing indicator and add empty assistant message
        setMessages(prev => {
          const withoutTyping = prev.filter(msg => !(msg.role === 'assistant' && (!msg.content || msg.content === "")));
          return [...withoutTyping, assistantMessage];
        });
        
        // Handle streaming response from RAG agent
        const reader = ragResponse.body?.getReader();
        if (!reader) {
          throw new Error('No response body reader available');
        }
        
        let responseText = '';
        
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = new TextDecoder().decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                // Response complete
                break;
              } else {
                // Add to current response
                responseText += data;
                // Update the assistant message with streaming text
                setMessages(prev => prev.map(msg => 
                  msg.id === assistantMessage.id 
                    ? { ...msg, content: responseText }
                    : msg
                ));
              }
            }
          }
        }
        
        // Save the complete assistant message to Supabase
        const completeMessage: ChatMessage = {
          ...assistantMessage,
          content: responseText
        };
        await saveMessagesForChat(activeChatId, [completeMessage]);
        
        // Update the message with the complete text
        setMessages(prev => prev.map(msg => 
          msg.id === assistantMessage.id 
            ? { ...msg, content: responseText }
            : msg
        ));
      } catch (error) {
        // Error sending message
        // Remove typing indicator and add error message
        setMessages(prev => {
          const withoutTyping = prev.filter(msg => !(msg.role === 'assistant' && (!msg.content || msg.content === "")));
                  return [...withoutTyping, {
          id: crypto.randomUUID(),
          content: "Sorry, I encountered an error. Please try again.",
          role: "assistant",
          timestamp: new Date().toISOString()
        }];
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };



  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const toggleChat = () => {
    setIsCollapsed(!isCollapsed);
  };

  // Show placeholder when no chat is selected
  if (!activeChatId) {
    return (
      <>
        <div
          ref={assistantContainerRef}
          className={`relative transition-all duration-300 ease-in-out ${
          isCollapsed ? 'w-0' : 'w-[25rem]'
        }`}>
          {!isCollapsed && (
            <div className="h-full border-l border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 flex flex-col">
              {/* Chat Header */}
              <div className="p-3 border-b border-[#4a5565] dark:border-zinc-700 flex-shrink-0">
                <div className="text-sm font-bold font-mono uppercase tracking-wide">
                  PROJECT ASSISTANT
                </div>
                <div className="text-xs text-gray-500 font-mono">
                  {projectName || 'Project'} Chat
                </div>
              </div>
              
              {/* Chat Messages */}
              <ScrollArea className="flex-1 p-2" ref={scrollAreaRef}>
                <div className="space-y-4">
                  {/* Welcome message */}
                  <div className="space-y-2">
                    <div className="text-xs font-bold font-mono uppercase tracking-wide text-left">
                      ASSISTANT
                    </div>
                    <div className="p-2 text-xs font-mono whitespace-pre-wrap break-words text-[#4a5565] dark:text-zinc-50 mr-8">
                      Hi! I'm Sunny AI, your intelligent assistant for Project "{projectName || 'this project'}". I can answer questions about your project data, emails, documents, and meetings. What would you like to know?
                    </div>
                  </div>
                </div>
              </ScrollArea>

              {/* Chat Input */}
              <div className="p-2 border-t border-[#4a5565] dark:border-zinc-700 flex-shrink-0">
                <div className="flex items-end space-x-2">
                  <div className="flex-1">
                    <textarea
                      ref={textareaRef}
                      value={chatMessage}
                      onChange={handleTextareaChange}
                      onKeyPress={handleKeyPress}
                      className="w-full resize-none border border-[#4a5565] dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-[#4a5565] dark:focus:ring-zinc-700"
                      rows={1}
                      placeholder="Type your message..."
                    />
                  </div>
                  <Button
                    type="button"
                    onClick={handleSendMessage}
                    disabled={isLoading || !chatMessage.trim()}
                    className="p-2 h-8 w-8 flex items-center justify-center border border-[#4a5565] dark:border-zinc-700 bg-[#4a5565] dark:bg-zinc-700 text-stone-100 dark:text-zinc-50 rounded-md hover:bg-[#3a4555] dark:hover:bg-zinc-600 transition-colors font-mono text-xs"
                  >
                    <Send className="w-6 h-6" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Floating sunnyAI Button (when chat sidebar is collapsed) */}
        {isCollapsed && (
          <button
            onClick={toggleChat}
            className="fixed right-4 bottom-4 w-12 h-12 bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-20 shadow-lg"
            title="Open Sunny AI - Project Assistant"
          >
            <MessageSquare className="w-6 h-6" />
          </button>
        )}
      </>
    );
  }

  return (
    <>
      {/* Right Sidebar - Project Chat */}
      <div
        ref={assistantContainerRef}
        className={`relative transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-0' : 'w-[25rem]'
      }`}>
        {!isCollapsed && (
          <div className="h-full border-l border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 flex flex-col">


            {/* Chat Messages */}
            <ScrollArea className="flex-1 p-2" ref={scrollAreaRef}>
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`space-y-2`}>
                    <div className={`text-xs font-bold font-mono uppercase tracking-wide ${
                      message.role === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      {message.role === 'user' ? 'USER' : 'Sunny AI Assistant'}
                    </div>
                    <div className={`p-2 text-xs font-mono whitespace-pre-wrap break-words ${
                      message.role === 'user' 
                        ? 'border border-[#4a5565] bg-[#4a5565] text-stone-100 ml-8' 
                        : 'text-[#4a5565] dark:text-zinc-50 mr-8'
                    }`}>
                      {message.content}
                      {message.role === 'assistant' && isLoading && (!message.content || message.content === "") && (
                        <span className="inline-flex items-center">
                          <span className="animate-pulse">.</span>
                          <span className="animate-pulse" style={{ animationDelay: '0.2s' }}>.</span>
                          <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>.</span>
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Chat Input */}
            <div className="p-2 border-t border-[#4a5565] dark:border-zinc-700 flex-shrink-0">
              <div className="flex items-end space-x-2">
                <div className="flex-1">
                  <textarea
                    ref={textareaRef}
                    value={chatMessage}
                    onChange={handleTextareaChange}
                    onKeyPress={handleKeyPress}
                    className="w-full resize-none border border-[#4a5565] dark:border-zinc-700 rounded-md bg-white dark:bg-zinc-900 px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-[#4a5565] dark:focus:ring-zinc-700"
                    rows={1}
                    placeholder="Type your message..."
                  />
                </div>
                <Button
                  type="button"
                  onClick={handleSendMessage}
                  disabled={isLoading || !chatMessage.trim()}
                  className="p-2 h-8 w-8 flex items-center justify-center border border-[#4a5565] dark:border-zinc-700 bg-[#4a5565] dark:bg-zinc-700 text-stone-100 dark:text-zinc-50 rounded-md hover:bg-[#3a4555] dark:hover:bg-zinc-600 transition-colors font-mono text-xs"
                >
                  <Send className="w-4 h-4 flex-shrink-0" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Chat Sidebar Toggle Button */}
        {!isCollapsed && (
          <button
            onClick={toggleChat}
            className="absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-6 bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-10"
            title="Collapse chat"
          >
            <ChevronRight className="w-3 h-3" />
          </button>
        )}
      </div>

      {/* Floating sunnyAI Button (when chat sidebar is collapsed) */}
      {isCollapsed && (
        <button
          onClick={toggleChat}
          className="fixed right-4 bottom-4 w-12 h-12 bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-20 shadow-lg"
          title="Open Project Assistant"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}
    </>
  );
};

export default ProjectChat; 