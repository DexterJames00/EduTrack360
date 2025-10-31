export type UserRole = 'instructor' | 'school_admin' | 'student' | 'admin' | 'parent';

export interface User {
  id: number;
  username: string;
  role: UserRole;
  school_id: number;
}

export interface Conversation {
  id: number;
  title: string;
  last_message?: string;
  updated_at?: string;
  unread_count?: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  sender_type: UserRole;
  content: string;
  created_at: string;
  is_read?: boolean;
}

export * from './attendance';
