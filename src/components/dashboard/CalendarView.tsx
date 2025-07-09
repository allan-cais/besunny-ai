import React, { useState, useRef, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Calendar, 
  Video, 
  Clock, 
  Send, 
  Loader2,
  ExternalLink,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Meeting } from '@/lib/calendar';
import { apiKeyService } from '@/lib/api-keys';
import { calendarService } from '@/lib/calendar';

interface CalendarViewProps {
  meetings: Meeting[];
  onSyncCalendar: () => void;
  syncing: boolean;
  onMeetingUpdate: () => void;
}

type ViewMode = 'day' | 'week' | 'month';

function stripHtml(html: string): string {
  if (!html) return '';
  return html.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}

const CalendarView: React.FC<CalendarViewProps> = ({ 
  meetings, 
  onSyncCalendar, 
  syncing, 
  onMeetingUpdate 
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('week');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedMeeting, setSelectedMeeting] = useState<Meeting | null>(null);
  const [sendingBot, setSendingBot] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const initialLoad = useRef(true);

  // Auto-scroll to noon (12pm) for Day/Week views on initial load and when clicking Today
  useEffect(() => {
    if ((viewMode === 'day' || viewMode === 'week') && scrollRef.current) {
      // Only scroll on initial load or when currentDate is today
      if (initialLoad.current || isToday(currentDate)) {
        requestAnimationFrame(() => {
          if (scrollRef.current) {
            scrollRef.current.scrollTop = 12 * 60;
          }
        });
      }
      initialLoad.current = false;
    }
  }, [viewMode, currentDate]);

  function isToday(date: Date) {
    const now = new Date();
    return (
      date.getDate() === now.getDate() &&
      date.getMonth() === now.getMonth() &&
      date.getFullYear() === now.getFullYear()
    );
  }

  const getStatusBadge = (status: Meeting['status']) => {
    switch (status) {
      case 'accepted':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">Attending</Badge>;
      case 'declined':
        return <Badge variant="secondary" className="bg-red-100 text-red-800 text-xs">Declined</Badge>;
      case 'tentative':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">Tentative</Badge>;
      case 'needsAction':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800 text-xs">Invited</Badge>;
      case 'pending':
        return <Badge variant="secondary" className="bg-gray-100 text-gray-800 text-xs">Pending</Badge>;
      case 'bot_scheduled':
        return <Badge variant="secondary" className="bg-blue-100 text-blue-800 text-xs">Bot Scheduled</Badge>;
      case 'bot_joined':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">Bot Joined</Badge>;
      case 'transcribing':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800 text-xs">Transcribing</Badge>;
      case 'completed':
        return <Badge variant="secondary" className="bg-green-100 text-green-800 text-xs">Completed</Badge>;
      case 'failed':
        return <Badge variant="secondary" className="bg-red-100 text-red-800 text-xs">Failed</Badge>;
      default:
        return <Badge variant="secondary" className="text-xs">Unknown</Badge>;
    }
  };

  const sendBotToMeeting = async (meeting: Meeting) => {
    if (!meeting.meeting_url) return;
    try {
      setSendingBot(meeting.id);
      const result = await apiKeyService.sendBotToMeeting(meeting.meeting_url, {
        bot_name: meeting.bot_name || 'Kirit Notetaker',
        bot_chat_message: {
          to: 'everyone',
          message: meeting.bot_chat_message || 'Hi, I\'m here to transcribe this meeting!',
        },
      });
      await calendarService.updateMeetingStatus(
        meeting.id, 
        'bot_scheduled', 
        result.id || result.bot_id
      );
      onMeetingUpdate();
    } catch (err: any) {
      // Optionally handle error
    } finally {
      setSendingBot(null);
    }
  };

  const canSendBot = (meeting?: Meeting | null) => {
    if (!meeting) return false;
    return meeting.meeting_url && 
           (meeting.status === 'pending' || meeting.status === 'accepted') && 
           !sendingBot;
  };

  const formatTime = (dateTime: string) => {
    const date = new Date(dateTime);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const getWeekDays = () => {
    const days = [];
    const startOfWeek = new Date(currentDate);
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
    for (let i = 0; i < 7; i++) {
      const day = new Date(startOfWeek);
      day.setDate(startOfWeek.getDate() + i);
      days.push(day);
    }
    return days;
  };

  const getMonthDays = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const startDate = new Date(firstDay);
    startDate.setDate(firstDay.getDate() - firstDay.getDay());
    const days = [];
    for (let i = 0; i < 42; i++) {
      const day = new Date(startDate);
      day.setDate(startDate.getDate() + i);
      days.push(day);
    }
    return days;
  };

  const getMeetingsForDate = (date: Date) => {
    return meetings.filter(meeting => {
      const meetingDate = new Date(meeting.start_time);
      return meetingDate.toDateString() === date.toDateString();
    });
  };

  const getMeetingsForTimeSlot = (date: Date, hour: number) => {
    return meetings.filter(meeting => {
      const meetingDate = new Date(meeting.start_time);
      return meetingDate.toDateString() === date.toDateString() && 
             meetingDate.getHours() === hour;
    });
  };

  const navigateDate = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (viewMode === 'day') {
      newDate.setDate(currentDate.getDate() + (direction === 'next' ? 1 : -1));
    } else if (viewMode === 'week') {
      newDate.setDate(currentDate.getDate() + (direction === 'next' ? 7 : -7));
    } else if (viewMode === 'month') {
      newDate.setMonth(currentDate.getMonth() + (direction === 'next' ? 1 : -1));
    }
    setCurrentDate(newDate);
  };

  const DayView = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i); // 0 to 23 (all hours)
    return (
      <div ref={scrollRef} className="h-[600px] overflow-y-auto">
        {hours.map(hour => {
          const timeSlotMeetings = getMeetingsForTimeSlot(currentDate, hour);
          return (
            <div key={hour} className="flex border-b border-gray-200 dark:border-gray-700 min-h-[60px]">
              <div className="w-16 p-2 text-xs text-gray-500 border-r border-gray-200 dark:border-gray-700">
                {formatTime(new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), hour))}
              </div>
              <div className="flex-1 p-1">
                {timeSlotMeetings.map(meeting => (
                  <div
                    key={meeting.id}
                    className="bg-blue-100 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700 rounded p-2 mb-1 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/40"
                    onClick={() => setSelectedMeeting(meeting)}
                  >
                    <div className="font-medium truncate">{meeting.title}</div>
                    <div className="text-gray-600 dark:text-gray-400">
                      {formatTime(meeting.start_time)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  const WeekView = () => {
    const hours = Array.from({ length: 24 }, (_, i) => i); // 0 to 23 (all hours)
    const weekDays = getWeekDays();
    return (
      <div ref={scrollRef} className="h-[600px] overflow-y-auto">
        <div className="flex">
          <div className="w-16" />
          {weekDays.map((day, i) => (
            <div key={i} className="flex-1 text-center text-xs font-medium py-2">
              {formatDate(day)}
            </div>
          ))}
        </div>
        {hours.map(hour => (
          <div key={hour} className="flex border-b border-gray-200 dark:border-gray-700 min-h-[60px]">
            <div className="w-16 p-2 text-xs text-gray-500 border-r border-gray-200 dark:border-gray-700">
              {formatTime(new Date(currentDate.getFullYear(), currentDate.getMonth(), currentDate.getDate(), hour))}
            </div>
            {weekDays.map((day, i) => {
              const timeSlotMeetings = getMeetingsForTimeSlot(day, hour);
              return (
                <div key={i} className="flex-1 p-1">
                  {timeSlotMeetings.map(meeting => (
                    <div
                      key={meeting.id}
                      className="bg-blue-100 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700 rounded p-2 mb-1 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/40"
                      onClick={() => setSelectedMeeting(meeting)}
                    >
                      <div className="font-medium truncate">{meeting.title}</div>
                      <div className="text-gray-600 dark:text-gray-400">
                        {formatTime(meeting.start_time)}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    );
  };

  const MonthView = () => {
    const monthDays = getMonthDays();
    const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return (
      <div>
        <div className="grid grid-cols-7 gap-1 mb-2">
          {weekDays.map(day => (
            <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-1">
          {monthDays.map((day, index) => {
            const dayMeetings = getMeetingsForDate(day);
            const isCurrentMonth = day.getMonth() === currentDate.getMonth();
            const isToday = day.toDateString() === new Date().toDateString();
            return (
              <div
                key={index}
                className={`min-h-[100px] p-2 border border-gray-200 dark:border-gray-700 ${
                  isCurrentMonth ? 'bg-white dark:bg-gray-900' : 'bg-gray-50 dark:bg-gray-800'
                } ${isToday ? 'ring-2 ring-blue-500' : ''}`}
              >
                <div className={`text-sm font-medium mb-1 ${
                  isCurrentMonth ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400'
                }`}>
                  {day.getDate()}
                </div>
                <div className="space-y-1">
                  {dayMeetings.slice(0, 3).map(meeting => (
                    <div
                      key={meeting.id}
                      className="bg-blue-100 dark:bg-blue-900/20 border border-blue-300 dark:border-blue-700 rounded p-1 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/40 text-xs"
                      onClick={() => setSelectedMeeting(meeting)}
                    >
                      <div className="font-medium truncate">{meeting.title}</div>
                      <div className="text-gray-600 dark:text-gray-400">
                        {formatTime(meeting.start_time)}
                      </div>
                    </div>
                  ))}
                  {dayMeetings.length > 3 && (
                    <div className="text-xs text-gray-500">
                      +{dayMeetings.length - 3} more
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <Card className="bg-white dark:bg-zinc-900 border border-[#4a5565] dark:border-zinc-700 w-full mx-auto max-w-6xl px-4 md:px-8 mt-8">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center">
              <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <CardTitle className="text-base font-bold">CALENDAR</CardTitle>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateDate('prev')}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setCurrentDate(new Date());
                // Scroll to noon (12pm) after setting date
                requestAnimationFrame(() => {
                  if (scrollRef.current) {
                    scrollRef.current.scrollTop = 12 * 60;
                  }
                });
              }}
            >
              Today
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateDate('next')}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button
              onClick={onSyncCalendar}
              disabled={syncing}
              variant="outline"
              size="sm"
              className="font-mono text-xs"
            >
              {syncing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  SYNCING...
                </>
              ) : (
                <>
                  <Calendar className="mr-2 h-4 w-4" />
                  SYNC
                </>
              )}
            </Button>
          </div>
        </div>
        <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as ViewMode)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="day">Day</TabsTrigger>
            <TabsTrigger value="week">Week</TabsTrigger>
            <TabsTrigger value="month">Month</TabsTrigger>
          </TabsList>
          <TabsContent value="day">
            <CardContent>
              <div className="mb-4">
                <h2 className="text-lg font-semibold">{formatDate(currentDate)}</h2>
              </div>
              <DayView />
            </CardContent>
          </TabsContent>
          <TabsContent value="week">
            <CardContent>
              <div className="mb-4">
                <h2 className="text-lg font-semibold">{`${formatDate(getWeekDays()[0])} - ${formatDate(getWeekDays()[6])}`}</h2>
              </div>
              <WeekView />
            </CardContent>
          </TabsContent>
          <TabsContent value="month">
            <CardContent>
              <div className="mb-4">
                <h2 className="text-lg font-semibold">{currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</h2>
              </div>
              <MonthView />
            </CardContent>
          </TabsContent>
        </Tabs>
      </CardHeader>
      <Dialog open={!!selectedMeeting} onOpenChange={() => setSelectedMeeting(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{selectedMeeting?.title}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-500" />
              <span className="text-sm">
                {selectedMeeting && `${formatTime(selectedMeeting.start_time)} - ${formatTime(selectedMeeting.end_time)}`}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              {getStatusBadge(selectedMeeting?.status || 'pending')}
            </div>
            {selectedMeeting?.description && (
              <div>
                <h4 className="font-medium text-sm mb-2">Description</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {stripHtml(selectedMeeting.description)}
                </p>
              </div>
            )}
            {selectedMeeting?.meeting_url && (
              <div>
                <h4 className="font-medium text-sm mb-2">Meeting URL</h4>
                <div className="flex items-center space-x-2">
                  <Video className="w-4 h-4 text-gray-500" />
                  <span className="text-sm text-blue-600 dark:text-blue-400 truncate">
                    {selectedMeeting.meeting_url}
                  </span>
                </div>
              </div>
            )}
            <div className="flex space-x-2 pt-4">
              {selectedMeeting && canSendBot(selectedMeeting) && (
                <Button
                  onClick={() => selectedMeeting && sendBotToMeeting(selectedMeeting)}
                  disabled={sendingBot === selectedMeeting?.id}
                  size="sm"
                  className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
                >
                  {sendingBot === selectedMeeting?.id ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      SENDING...
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" />
                      SEND BOT
                    </>
                  )}
                </Button>
              )}
              {selectedMeeting?.meeting_url && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open(selectedMeeting.meeting_url, '_blank')}
                >
                  <ExternalLink className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  );
};

export default CalendarView; 