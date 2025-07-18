import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Send, CheckCircle, Edit3, ArrowRight } from 'lucide-react';
import { useSupabase } from '@/hooks/use-supabase';
import { Project } from '@/lib/supabase';

interface ProjectOnboardingData {
  project_name: string;
  overview: string;
  keywords: string[];
  deliverables: string;
  contacts: {
    internal_lead: string;
    agency_lead: string;
    client_lead: string;
  };
  shoot_date: string;
  location: string;
  references: string;
}

type ProjectOnboardingDataKey = keyof ProjectOnboardingData;
type ContactKey = keyof ProjectOnboardingData['contacts'];

interface ChatMessage {
  id: string;
  type: 'bot' | 'user';
  content: string;
  timestamp: Date;
  isTyping?: boolean;
}

interface CreateProjectDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onProjectCreated: (project: Project) => void;
  currentUserId: string;
}

const QUESTIONS = [
  {
    id: 'project_name',
    question: "What's the project name?",
    type: 'text' as const,
    required: true
  },
  {
    id: 'overview',
    question: "How would you describe this project in one sentence?",
    type: 'textarea' as const,
    required: true
  },
  {
    id: 'keywords',
    question: "What keywords or phrases are likely to appear in emails or files about this project? (comma-separated)",
    type: 'text' as const,
    required: true
  },
  {
    id: 'deliverables',
    question: "What are the expected deliverables?",
    type: 'textarea' as const,
    required: true
  },
  {
    id: 'internal_lead',
    question: "Who is the internal lead for this project?",
    type: 'text' as const,
    required: true
  },
  {
    id: 'agency_lead',
    question: "Who is the agency lead for this project?",
    type: 'text' as const,
    required: true
  },
  {
    id: 'client_lead',
    question: "Who is the client lead for this project?",
    type: 'text' as const,
    required: true
  },
  {
    id: 'shoot_date',
    question: "What is the primary shoot date or date range?",
    type: 'text' as const,
    required: true
  },
  {
    id: 'location',
    question: "Where is the shoot location?",
    type: 'text' as const,
    required: true
  },
  {
    id: 'references',
    question: "Any reference links or attachments? (optional)",
    type: 'textarea' as const,
    required: false
  }
];

const CreateProjectDialog: React.FC<CreateProjectDialogProps> = ({
  open,
  onOpenChange,
  onProjectCreated,
  currentUserId
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [onboardingData, setOnboardingData] = useState<Partial<ProjectOnboardingData>>({});
  const [currentInput, setCurrentInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSummary, setShowSummary] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [isThinking, setIsThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const editInputRef = useRef<HTMLInputElement>(null);
  const editTextareaRef = useRef<HTMLTextAreaElement>(null);

  const { createProject } = useSupabase();

  // Initialize chat when dialog opens
  useEffect(() => {
    if (open) {
      initializeChat();
    }
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when question changes
  useEffect(() => {
    if (currentQuestionIndex < QUESTIONS.length) {
      setTimeout(() => {
        const currentQuestion = QUESTIONS[currentQuestionIndex];
        if (currentQuestion.type === 'textarea') {
          textareaRef.current?.focus();
        } else {
          inputRef.current?.focus();
        }
      }, 100);
    }
  }, [currentQuestionIndex]);

  const initializeChat = () => {
    const welcomeMessage: ChatMessage = {
      id: 'welcome',
      type: 'bot',
      content: "Hi! I'm here to help you set up your new project. Let me ask you a few questions to gather all the details we need.",
      timestamp: new Date()
    };
    
    setMessages([welcomeMessage]);
    setCurrentQuestionIndex(0);
    setOnboardingData({});
    setCurrentInput('');
    setError(null);
    setShowSummary(false);
    
    // Add thinking message, then first question
    setTimeout(() => {
      addThinkingMessage();
      setTimeout(() => {
        removeThinkingMessage();
        addBotMessage(QUESTIONS[0].question);
      }, 1200); // 1.2 second thinking pause
    }, 800);
  };

  const addBotMessage = (content: string, isTyping = false) => {
    const message: ChatMessage = {
      id: `bot-${Date.now()}`,
      type: 'bot',
      content,
      timestamp: new Date(),
      isTyping
    };
    setMessages(prev => [...prev, message]);
  };

  const addThinkingMessage = () => {
    const message: ChatMessage = {
      id: `thinking-${Date.now()}`,
      type: 'bot',
      content: '...',
      timestamp: new Date(),
      isTyping: true
    };
    setMessages(prev => [...prev, message]);
    setIsThinking(true);
  };

  const removeThinkingMessage = () => {
    setMessages(prev => prev.filter(msg => !msg.isTyping));
    setIsThinking(false);
  };

  const addUserMessage = (content: string) => {
    const message: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, message]);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setCurrentInput(e.target.value);
  };

  const handleSubmit = async () => {
    if (!currentInput.trim()) return;

    const currentQuestion = QUESTIONS[currentQuestionIndex];
    const answer = currentInput.trim();
    
    // Add user message
    addUserMessage(answer);
    
    // Save the answer
    const newData = { ...onboardingData };
    
    if (currentQuestion.id === 'keywords') {
      newData.keywords = answer.split(',').map(k => k.trim()).filter(k => k);
    } else if (currentQuestion.id === 'internal_lead') {
      newData.contacts = { ...newData.contacts, internal_lead: answer };
    } else if (currentQuestion.id === 'agency_lead') {
      newData.contacts = { ...newData.contacts, agency_lead: answer };
    } else if (currentQuestion.id === 'client_lead') {
      newData.contacts = { ...newData.contacts, client_lead: answer };
    } else {
      (newData as Record<string, string>)[currentQuestion.id] = answer;
    }
    
    setOnboardingData(newData);
    setCurrentInput('');

    // Move to next question or show summary
    const nextIndex = currentQuestionIndex + 1;
    if (nextIndex < QUESTIONS.length) {
      // Add thinking message
      addThinkingMessage();
      
      // Wait a moment, then show next question
      setTimeout(() => {
        removeThinkingMessage();
        setCurrentQuestionIndex(nextIndex);
        addBotMessage(QUESTIONS[nextIndex].question);
      }, 1500); // 1.5 second thinking pause
    } else {
      // All questions answered, show summary
      addThinkingMessage();
      
      setTimeout(() => {
        removeThinkingMessage();
        addBotMessage("Perfect! Let me show you a summary of what we've collected:");
        setShowSummary(true);
      }, 1500); // 1.5 second thinking pause
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

    const handleEditAnswer = (questionId: string) => {
    // Get the current value for editing
    let currentValue = '';
    if (questionId === 'keywords') {
      currentValue = onboardingData.keywords?.join(', ') || '';
    } else if (questionId === 'internal_lead') {
      currentValue = onboardingData.contacts?.internal_lead || '';
    } else if (questionId === 'agency_lead') {
      currentValue = onboardingData.contacts?.agency_lead || '';
    } else if (questionId === 'client_lead') {
      currentValue = onboardingData.contacts?.client_lead || '';
    } else {
      currentValue = (onboardingData as Record<string, string>)[questionId] || '';
    }
    
    setEditingField(questionId);
    setEditValue(currentValue);
    
    // Focus the edit input after a short delay
    setTimeout(() => {
      const currentQuestion = QUESTIONS.find(q => q.id === questionId);
      if (currentQuestion?.type === 'textarea') {
        editTextareaRef.current?.focus();
      } else {
        editInputRef.current?.focus();
      }
    }, 100);
  };

  const handleSaveEdit = () => {
    if (!editingField || !editValue.trim()) return;

    const newData = { ...onboardingData };
    
    if (editingField === 'keywords') {
      newData.keywords = editValue.split(',').map(k => k.trim()).filter(k => k);
    } else if (editingField === 'internal_lead') {
      newData.contacts = { ...newData.contacts, internal_lead: editValue.trim() };
    } else if (editingField === 'agency_lead') {
      newData.contacts = { ...newData.contacts, agency_lead: editValue.trim() };
    } else if (editingField === 'client_lead') {
      newData.contacts = { ...newData.contacts, client_lead: editValue.trim() };
    } else {
      (newData as Record<string, string>)[editingField] = editValue.trim();
    }
    
    setOnboardingData(newData);
    setEditingField(null);
    setEditValue('');
  };

  const handleCancelEdit = () => {
    setEditingField(null);
    setEditValue('');
  };

  const handleConfirm = async () => {
    setSubmitting(true);
    setError(null);

    try {
      // First create the project in Supabase
      const newProject = await createProject({
        id: crypto.randomUUID(),
        name: onboardingData.project_name || '',
        description: onboardingData.overview || '',
        status: 'active',
        created_by: currentUserId
      });

      if (!newProject) {
        throw new Error('Failed to create project');
      }

      // Prepare the payload for n8n webhook
      const webhookPayload = {
        project_id: newProject.id,
        user_id: currentUserId,
        summary: {
          project_name: onboardingData.project_name || '',
          overview: onboardingData.overview || '',
          keywords: onboardingData.keywords || [],
          deliverables: onboardingData.deliverables || '',
          contacts: {
            internal_lead: onboardingData.contacts?.internal_lead || '',
            agency_lead: onboardingData.contacts?.agency_lead || '',
            client_lead: onboardingData.contacts?.client_lead || ''
          },
          shoot_date: onboardingData.shoot_date || '',
          location: onboardingData.location || '',
          references: onboardingData.references || ''
        }
      };

      // Send to n8n webhook for project onboarding (optional)
      const webhookUrl = import.meta.env.VITE_N8N_PROJECT_ONBOARDING_WEBHOOK_URL;
      
      if (webhookUrl) {
        try {
          const webhookResponse = await fetch(webhookUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(webhookPayload)
          });

          if (!webhookResponse.ok) {
            // Webhook failed but project was created - handle silently
          }
        } catch (webhookError) {
          // Don't throw error - webhook is optional
        }
      }

      // Call the callback
      onProjectCreated(newProject);
      
      // Close dialog
      onOpenChange(false);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setSubmitting(false);
    }
  };

  const currentQuestion = QUESTIONS[currentQuestionIndex];
  const isLastQuestion = currentQuestionIndex === QUESTIONS.length - 1;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] h-[80vh] bg-stone-100 dark:bg-zinc-800 border border-[#4a5565] dark:border-zinc-700 font-mono text-xs flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle className="text-[#4a5565] dark:text-zinc-50 font-mono text-sm font-bold">
            PROJECT ONBOARDING WIZARD
          </DialogTitle>
          <DialogDescription className="text-gray-600 dark:text-gray-400 font-mono text-xs">
            Complete the questionnaire to create your new project
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 flex flex-col min-h-0">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.type === 'user'
                      ? 'bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900'
                      : 'bg-stone-200 dark:bg-zinc-700 text-[#4a5565] dark:text-zinc-50'
                  }`}
                >
                  {message.isTyping ? (
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                  ) : (
                    <div className="text-sm">{message.content}</div>
                  )}
                </div>
              </div>
            ))}
            
            {/* Summary Section */}
            {showSummary && (
              <div className="bg-stone-200 dark:bg-zinc-700 rounded-lg p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-[#4a5565] dark:text-zinc-50">Project Summary</h3>
                  {editingField && (
                    <span className="text-xs text-blue-600 dark:text-blue-400 font-mono">
                      Editing {editingField.replace('_', ' ')}...
                    </span>
                  )}
                </div>
                
                {Object.entries(onboardingData).map(([key, value]) => {
                  if (!value) return null;
                  
                  if (key === 'contacts') {
                    return Object.entries(value as Record<string, string>).map(([contactKey, contactValue]) => {
                      const isEditing = editingField === contactKey;
                      
                      return (
                        <div key={contactKey} className="flex justify-between items-start">
                          <span className="text-[#4a5565] dark:text-zinc-300 capitalize">
                            {contactKey.replace('_', ' ')}:
                          </span>
                          <div className="flex items-center space-x-2">
                            {isEditing ? (
                              <div className="flex items-center space-x-2">
                                <Input
                                  ref={editInputRef}
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  onKeyPress={(e) => {
                                    if (e.key === 'Enter') {
                                      handleSaveEdit();
                                    } else if (e.key === 'Escape') {
                                      handleCancelEdit();
                                    }
                                  }}
                                  className="w-48 font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50"
                                  autoFocus
                                />
                                <Button
                                  size="sm"
                                  onClick={handleSaveEdit}
                                  className="h-6 px-2 font-mono text-xs bg-green-600 hover:bg-green-700 text-white"
                                >
                                  ✓
                                </Button>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={handleCancelEdit}
                                  className="h-6 px-2 font-mono text-xs"
                                >
                                  ✕
                                </Button>
                              </div>
                            ) : (
                              <>
                                <span className="text-[#4a5565] dark:text-zinc-50">{contactValue}</span>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => handleEditAnswer(contactKey)}
                                  className="h-6 w-6 p-0"
                                >
                                  <Edit3 className="h-3 w-3" />
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    });
                  }
                  
                  if (key === 'keywords') {
                    const displayValue = (value as string[]).join(', ');
                    const isEditing = editingField === 'keywords';
                    
                    return (
                      <div key={key} className="flex justify-between items-start">
                        <span className="text-[#4a5565] dark:text-zinc-300 capitalize">
                          {key.replace('_', ' ')}:
                        </span>
                        <div className="flex items-center space-x-2">
                          {isEditing ? (
                            <div className="flex items-center space-x-2">
                              <Input
                                ref={editInputRef}
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter') {
                                    handleSaveEdit();
                                  } else if (e.key === 'Escape') {
                                    handleCancelEdit();
                                  }
                                }}
                                className="w-48 font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50"
                                autoFocus
                              />
                              <Button
                                size="sm"
                                onClick={handleSaveEdit}
                                className="h-6 px-2 font-mono text-xs bg-green-600 hover:bg-green-700 text-white"
                              >
                                ✓
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={handleCancelEdit}
                                className="h-6 px-2 font-mono text-xs"
                              >
                                ✕
                              </Button>
                            </div>
                          ) : (
                            <>
                              <span className="text-[#4a5565] dark:text-zinc-50">{displayValue}</span>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleEditAnswer('keywords')}
                                className="h-6 w-6 p-0"
                              >
                                <Edit3 className="h-3 w-3" />
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    );
                  }
                  
                  const displayValue = value as string;
                  const isEditing = editingField === key;
                  const currentQuestion = QUESTIONS.find(q => q.id === key);
                  
                  return (
                    <div key={key} className="flex justify-between items-start">
                      <span className="text-[#4a5565] dark:text-zinc-300 capitalize">
                        {key.replace('_', ' ')}:
                      </span>
                      <div className="flex items-center space-x-2">
                        {isEditing ? (
                          <div className="flex items-center space-x-2">
                            {currentQuestion?.type === 'textarea' ? (
                              <Textarea
                                ref={editTextareaRef}
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSaveEdit();
                                  } else if (e.key === 'Escape') {
                                    handleCancelEdit();
                                  }
                                }}
                                className="w-48 font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 resize-none"
                                rows={2}
                                autoFocus
                              />
                            ) : (
                              <Input
                                ref={editInputRef}
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter') {
                                    handleSaveEdit();
                                  } else if (e.key === 'Escape') {
                                    handleCancelEdit();
                                  }
                                }}
                                className="w-48 font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50"
                                autoFocus
                              />
                            )}
                            <Button
                              size="sm"
                              onClick={handleSaveEdit}
                              className="h-6 px-2 font-mono text-xs bg-green-600 hover:bg-green-700 text-white"
                            >
                              ✓
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={handleCancelEdit}
                              className="h-6 px-2 font-mono text-xs"
                            >
                              ✕
                            </Button>
                          </div>
                        ) : (
                          <>
                            <span className="text-[#4a5565] dark:text-zinc-50">{displayValue}</span>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleEditAnswer(key)}
                              className="h-6 w-6 p-0"
                            >
                              <Edit3 className="h-3 w-3" />
                            </Button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive" className="mx-4 mb-4 border-red-500 bg-red-50 dark:bg-red-900/20">
              <AlertDescription className="font-mono text-xs text-red-700 dark:text-red-400">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Input Section */}
          {!showSummary && currentQuestion && (
            <div className="flex-shrink-0 p-4 border-t border-[#4a5565] dark:border-zinc-700">
              <div className="flex space-x-2">
                {currentQuestion.type === 'textarea' ? (
                  <Textarea
                    ref={textareaRef}
                    value={currentInput}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    placeholder={isThinking ? "Please wait..." : "Type your answer..."}
                    disabled={isThinking}
                    className="flex-1 font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600 resize-none disabled:opacity-50"
                    rows={3}
                  />
                ) : (
                  <Input
                    ref={inputRef}
                    value={currentInput}
                    onChange={handleInputChange}
                    onKeyPress={handleKeyPress}
                    placeholder={isThinking ? "Please wait..." : "Type your answer..."}
                    disabled={isThinking}
                    className="flex-1 font-mono text-xs border border-[#4a5565] dark:border-zinc-700 bg-stone-50 dark:bg-zinc-900 text-[#4a5565] dark:text-zinc-50 placeholder:text-gray-500 dark:placeholder:text-gray-400 focus:border-[#4a5565] dark:focus:border-zinc-600 disabled:opacity-50"
                  />
                )}
                <Button
                  onClick={handleSubmit}
                  disabled={!currentInput.trim() || loading || isThinking}
                  className="font-mono text-xs bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 hover:bg-[#3a4555] dark:hover:bg-zinc-200 disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {currentQuestionIndex + 1} of {QUESTIONS.length} questions
              </div>
            </div>
          )}

          {/* Confirmation Section */}
          {showSummary && (
            <div className="flex-shrink-0 p-4 border-t border-[#4a5565] dark:border-zinc-700">
              <Button
                onClick={handleConfirm}
                disabled={submitting || editingField !== null}
                className="w-full font-mono text-xs bg-[#4a5565] dark:bg-zinc-50 text-stone-100 dark:text-zinc-900 hover:bg-[#3a4555] dark:hover:bg-zinc-200 disabled:opacity-50"
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating Project...
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Create Project
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default CreateProjectDialog; 