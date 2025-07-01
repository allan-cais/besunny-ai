import { useState, useRef, useLayoutEffect, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, ChevronRight, MessageSquare } from "lucide-react";
import { useSupabase, useSupabaseSubscription } from "@/hooks/use-supabase";
import { ChatMessage as SupabaseChatMessage } from "@/lib/supabase";

interface ChatMessage {
  id: string;
  session_id: string;
  role?: string;
  message?: string;
  used_chunks?: string[];
  created_at: string;
}

interface ChatSession {
  id: string;
  user_id?: string;
  project_id?: string;
  started_at: string;
  ended_at?: string;
}

interface AIAssistantProps {
  isCollapsed: boolean;
  onToggle: () => void;
  activeChatId: string | null;
  chats: ChatSession[];
  onChatUpdate: (updatedChats: ChatSession[]) => void;
  currentUserId?: string;
  currentProjectId?: string;
}

const AIAssistant = ({ 
  isCollapsed, 
  onToggle, 
  activeChatId, 
  chats, 
  onChatUpdate,
  currentUserId,
  currentProjectId 
}: AIAssistantProps) => {
  const [chatMessage, setChatMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const assistantContainerRef = useRef<HTMLDivElement>(null);

  // Supabase hooks
  const { 
    isLoading: supabaseLoading, 
    error: supabaseError, 
    saveMessages, 
    getMessagesBySession, 
    createChatSession,
    isConfigured: supabaseConfigured 
  } = useSupabase();

  // Get n8n webhook URL from environment or use default
  const N8N_WEBHOOK_URL = import.meta.env.VITE_N8N_WEBHOOK_URL || 'https://n8n.customaistudio.io/webhook/kirit-rag-webhook';

  // Real-time subscription for messages
  useSupabaseSubscription(activeChatId || '', (payload) => {
    if (payload.eventType === 'INSERT' && payload.new) {
      const newMessage = payload.new as SupabaseChatMessage;
      if (newMessage.session_id === activeChatId) {
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
  });

  const loadMessagesForChat = useCallback(async (chatId: string) => {
    try {
      const supabaseMessages = await getMessagesBySession(chatId, 100);
      let loadedMessages: ChatMessage[] = supabaseMessages;
      // If no messages found, initialize with welcome message
      if (loadedMessages.length === 0) {
        loadedMessages = [{
          id: crypto.randomUUID(),
          session_id: chatId,
          role: "assistant",
          message: "Hello! How can I help you today?",
          created_at: new Date().toISOString()
        }];
      }
      setMessages(loadedMessages);
    } catch (error) {
      setMessages([{
        id: crypto.randomUUID(),
        session_id: chatId,
        role: "assistant",
        message: "Hello! How can I help you today?",
        created_at: new Date().toISOString()
      }]);
    }
  }, [getMessagesBySession]);

  // Load messages for the active chat
  useEffect(() => {
    if (activeChatId) {
      loadMessagesForChat(activeChatId);
    } else {
      setMessages([]);
    }
  }, [activeChatId, loadMessagesForChat]);

  useLayoutEffect(() => {
    if (textareaRef.current) {
      const event = new Event('input', { bubbles: true });
      textareaRef.current.dispatchEvent(event);
    }
  }, [isCollapsed]);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatMessage(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${e.target.scrollHeight}px`;
  };

  const saveMessagesForChat = async (chatId: string, messages: ChatMessage[]) => {
    try {
      // Convert to the format expected by Supabase (omit created_at for new messages)
      const messagesToSave = messages.map(msg => ({
        id: msg.id,
        session_id: msg.session_id,
        role: msg.role,
        message: msg.message,
        used_chunks: msg.used_chunks || []
      }));
      await saveMessages(messagesToSave);
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  };

  const updateChatMetadata = (chatId: string, lastMessage: string) => {
    const updatedChats = chats.map(chat => {
      if (chat.id === chatId) {
        return {
          ...chat,
          started_at: new Date().toISOString()
        };
      }
      return chat;
    });
    onChatUpdate(updatedChats);
  };

  const handleSendMessage = async () => {
    if (chatMessage.trim() && !isLoading && activeChatId) {
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        session_id: activeChatId,
        role: "user",
        message: chatMessage,
        created_at: new Date().toISOString()
      };
      const newMessages = [...messages, userMessage];
      setMessages(newMessages);
      setChatMessage("");
      setIsLoading(true);
      try {
        await saveMessagesForChat(activeChatId, [userMessage]);
      } catch (error) {
        console.error('Error saving messages for chat:', error);
      }
      setIsLoading(false);
    }
  };

  // Effect to handle focusing the textarea
  useEffect(() => {
    if (!isCollapsed && !isLoading && activeChatId) {
      textareaRef.current?.focus();
    }
  }, [isCollapsed, isLoading, activeChatId]);

  // Effect to handle clicks outside of interactive elements
  useEffect(() => {
    const handleDocumentClick = (event: MouseEvent) => {
      if (isCollapsed || !textareaRef.current || !activeChatId) return;

      const target = event.target as HTMLElement;

      // Ignore clicks within the AI assistant panel itself
      if (assistantContainerRef.current?.contains(target)) {
        return;
      }

      // Ignore clicks on other common interactive elements on the page
      if (
        target.closest(
          'a, button, input, textarea, select, [contenteditable="true"]'
        )
      ) {
        return;
      }

      // If the click is on a non-interactive part of the page, focus the textarea
      textareaRef.current.focus();
    };

    document.addEventListener('click', handleDocumentClick, true);

    return () => {
      document.removeEventListener('click', handleDocumentClick, true);
    };
  }, [isCollapsed, activeChatId]);

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
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center text-gray-500 dark:text-gray-400">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">Select a chat or create a new one to start</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Floating sunnyAI Button (when chat sidebar is collapsed) */}
        {isCollapsed && (
          <button
            onClick={onToggle}
            className="fixed right-4 bottom-4 w-12 h-12 bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-20 shadow-lg"
            title="Open sunnyAI"
          >
            <MessageSquare className="w-6 h-6" />
          </button>
        )}
      </>
    );
  }

  return (
    <>
      {/* Right Sidebar - AI Assistant */}
      <div
        ref={assistantContainerRef}
        className={`relative transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-0' : 'w-[25rem]'
      }`}>
        {!isCollapsed && (
          <div className="h-full border-l border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 flex flex-col">
            {/* Chat Header */}
            <div className="p-3 border-b border-[#4a5565] dark:border-zinc-700 flex-shrink-0">
              <div className="text-sm font-bold">
                Chat Session
              </div>
              <div className="text-xs text-gray-500">
                {activeChatId}
              </div>
            </div>

            {/* Chat Messages */}
            <ScrollArea className="flex-1 p-2" ref={scrollAreaRef}>
              <div className="space-y-4">
                {messages.map((message) => (
                  <div key={message.id} className={`space-y-2`}>
                    <div className={`text-xs font-bold ${
                      message.role === 'user' ? 'text-right' : 'text-left'
                    }`}>
                      {message.role === 'user' ? 'USER' : 'ASSISTANT'}
                    </div>
                    <div className={`p-2 text-xs whitespace-pre-wrap break-words ${
                      message.role === 'user' 
                        ? 'border border-[#4a5565] bg-[#4a5565] text-stone-100 ml-8' 
                        : 'text-[#4a5565] dark:text-zinc-50 mr-8'
                    }`}>
                      {message.message}
                      {message.role === 'assistant' && isLoading && message.message === "" && (
                        <span className="animate-pulse">...</span>
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
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder="Type message..."
                    className="w-full bg-transparent border border-[#4a5565] dark:border-zinc-700 font-mono text-xs resize-none p-2 overflow-hidden"
                    rows={1}
                    disabled={isLoading}
                  />
                </div>
                <Button
                  onClick={handleSendMessage}
                  size="icon"
                  disabled={isLoading || !chatMessage.trim()}
                  className="border border-[#4a5565] bg-stone-100 text-[#4a5565] hover:bg-[#4a5565] hover:text-stone-100 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-50 dark:hover:bg-zinc-50 dark:hover:text-zinc-900 w-8 h-8 flex-shrink-0 disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Chat Sidebar Toggle Button */}
        {!isCollapsed && (
          <button
            onClick={onToggle}
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
          onClick={onToggle}
          className="fixed right-4 bottom-4 w-12 h-12 bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 border border-[#4a5565] dark:border-zinc-700 rounded-full flex items-center justify-center hover:bg-stone-300 dark:hover:bg-zinc-700 transition-colors z-20 shadow-lg"
          title="Open sunnyAI"
        >
          <MessageSquare className="w-6 h-6" />
        </button>
      )}
    </>
  );
};

export default AIAssistant; 