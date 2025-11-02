export type MeetingStatus = 'scheduled' | 'cancelled' | 'completed';

export interface MeetingItem {
  id: number;
  title: string;
  description?: string | null;
  meeting_date: string; // ISO date
  start_time: string; // HH:MM
  end_time: string; // HH:MM
  location?: string | null;
  status: MeetingStatus;
  student_name?: string;
  subject_name?: string | null;
}
