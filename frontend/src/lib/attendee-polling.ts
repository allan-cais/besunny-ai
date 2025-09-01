import { attendeeService } from './attendee-service';

export interface PollingResult {
  meetingId: string;
  status?: string;
  error?: string;
}

export interface AttendeePollingService {
  pollAllMeetings(): Promise<PollingResult[]>;
}

class AttendeePollingServiceImpl implements AttendeePollingService {
  async pollAllMeetings(): Promise<PollingResult[]> {
    try {
      return await attendeeService.pollAllMeetings();
    } catch (error) {
      // Error polling meetings
      return [];
    }
  }
}

export const attendeePollingService = new AttendeePollingServiceImpl(); 