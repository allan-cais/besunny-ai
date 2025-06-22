import { useState, useRef, useLayoutEffect } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, ChevronRight, MessageSquare } from "lucide-react";

interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

interface AIAssistantProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

const AIAssistant = ({ isCollapsed, onToggle }: AIAssistantProps) => {
  const [chatMessage, setChatMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "1",
      sessionId: "default",
      role: "assistant",
      content: "Hello! How can I help you today?",
      createdAt: new Date().toISOString()
    }
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

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

  const handleSendMessage = async () => {
    if (chatMessage.trim() && !isLoading) {
      const userMessage: ChatMessage = {
        id: Date.now().toString(),
        sessionId: "default",
        role: "user",
        content: chatMessage,
        createdAt: new Date().toISOString()
      };

      setMessages(prev => [...prev, userMessage]);
      setChatMessage("");
      setIsLoading(true);

      try {
        // Create a placeholder assistant message that will be updated
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          sessionId: "default",
          role: "assistant",
          content: "",
          createdAt: new Date().toISOString()
        };

        setMessages(prev => [...prev, assistantMessage]);

        // Call the backend API
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: userMessage.content,
            sessionId: userMessage.sessionId,
            messageId: assistantMessage.id
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to send message');
        }

        // Handle streaming response
        const reader = response.body?.getReader();
        if (reader) {
          const decoder = new TextDecoder();
          let accumulatedContent = "";

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6);
                if (data === '[DONE]') {
                  // Save messages to Supabase here
                  await saveMessagesToSupabase([userMessage, { ...assistantMessage, content: accumulatedContent }]);
                  setIsLoading(false);
                  return;
                }
                
                try {
                  const parsed = JSON.parse(data);
                  let displayContent = parsed.content;
                  // If the content is a JSON string with an 'output' field, parse and use it
                  if (typeof displayContent === 'string') {
                    try {
                      const maybeJson = JSON.parse(displayContent);
                      if (maybeJson && typeof maybeJson === 'object' && maybeJson.output) {
                        displayContent = maybeJson.output;
                      }
                    } catch {}
                  }
                  accumulatedContent += displayContent;
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === assistantMessage.id 
                        ? { ...msg, content: accumulatedContent }
                        : msg
                    )
                  );
                } catch (e) {
                  // Handle non-JSON data
                  accumulatedContent += data;
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === assistantMessage.id 
                        ? { ...msg, content: accumulatedContent }
                        : msg
                    )
                  );
                }
              }
            }
          }
        }
      } catch (error) {
        console.error('Error sending message:', error);
        setMessages(prev => {
          // Find the last assistant message and update it
          const lastAssistantIndex = prev.map(m => m.role).lastIndexOf('assistant');
          if (lastAssistantIndex !== -1) {
            const updated = [...prev];
            updated[lastAssistantIndex] = {
              ...updated[lastAssistantIndex],
              content: "Sorry, I encountered an error. Please try again."
            };
            return updated;
          }
          return prev;
        });
      } finally {
        setIsLoading(false);
      }
    }
  };

  const saveMessagesToSupabase = async (messages: ChatMessage[]) => {
    try {
      // This will be implemented when Supabase is set up
      console.log('Saving messages to Supabase:', messages);
      // await supabase.from('chat_messages').insert(messages);
    } catch (error) {
      console.error('Error saving messages to Supabase:', error);
    }
  };

  return (
    <>
      {/* Right Sidebar - AI Assistant */}
      <div className={`relative transition-all duration-300 ease-in-out ${
        isCollapsed ? 'w-0' : 'w-[25rem]'
      }`}>
        {!isCollapsed && (
          <div className="h-full w-full border-l border-[#4a5565] dark:border-zinc-700 bg-stone-100 dark:bg-zinc-800 flex flex-col">
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
                      {message.content}
                      {message.role === 'assistant' && isLoading && message.content === "" && (
                        <span className="animate-pulse">...</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Chat Input */}
            <div className="p-2 border-t border-[#4a5565] dark:border-zinc-700">
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