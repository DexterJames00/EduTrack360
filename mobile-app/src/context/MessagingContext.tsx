import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import io, { Socket } from 'socket.io-client';
import api from '@services/api.service';
import { Conversation, Message } from '../types';
import { useAuth } from './AuthContext';

interface MessagingContextShape {
  conversations: Conversation[];
  messages: Record<number, Message[]>;
  refreshConversations: () => Promise<void>;
  loadMessages: (conversationId: number) => Promise<void>;
  send: (conversationId: number, content: string, receiverId?: number, receiverType?: string) => Promise<void>;
  markRead: (conversationId: number) => Promise<void>;
  emitTyping: (conversationId: number, isTyping: boolean) => void;
}

const MessagingContext = createContext<MessagingContextShape | undefined>(undefined);

export const MessagingProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Record<number, Message[]>>({});
  const socketRef = useRef<Socket | null>(null);

  const { user } = useAuth();
  // helper to fetch conversations and map to local type
  const fetchConversations = async () => {
    const res = await api.get<any>('/api/messaging/conversations');
    const list = (res.conversations || []).map((c: any) => ({
      id: c.id,
      title: c.participantName || 'Chat',
      last_message: c.lastMessage,
      updated_at: c.lastMessageTime,
      unread_count: c.unreadCount,
    } as Conversation));
    setConversations(list);
  };
  useEffect(() => {
    if (!user) return;
  const url = api.getWebSocketUrl();
  const s = io(url, { path: '/socket.io', transports: ['websocket', 'polling'], forceNew: true });
    s.on('connect', () => {
      const schoolId = (user as any).schoolId ?? (user as any).school_id;
      if (schoolId) s.emit('join_school', { schoolId });
    });
    s.on('new_message', (payload: any) => {
      const convId = payload.conversationId || payload.conversation_id;
      const mapped: Message = {
        id: payload.id,
        conversation_id: convId,
        sender_id: payload.senderId || payload.sender_id,
        sender_type: (payload.senderType || payload.sender_type || 'instructor') as any,
        content: payload.content,
        created_at: payload.timestamp,
        is_read: false,
      };
      setMessages(prev => ({
        ...prev,
        [convId]: [...(prev[convId] || []), mapped]
      }));
      // Refresh chat list to bump last message/time
      fetchConversations().catch(() => {});
    });
    s.on('messages_read', (payload: any) => {
      // Any read update should refresh the conversations list for unread counts
      fetchConversations().catch(() => {});
    });
    socketRef.current = s;
    return () => {
      s.disconnect();
      socketRef.current = null;
    };
  }, [user]);

  const value = useMemo(() => ({
    conversations,
    messages,
    refreshConversations: fetchConversations,
    loadMessages: async (conversationId: number) => {
      const res = await api.get<any>(`/api/messaging/conversations/${conversationId}/messages`);
      const msgs: Message[] = (res.messages || []).map((m: any) => ({
        id: m.id,
        conversation_id: m.conversationId,
        sender_id: m.senderId,
        sender_type: m.senderRole as any,
        content: m.content,
        created_at: m.timestamp,
        is_read: m.isRead,
      }));
      setMessages(prev => ({ ...prev, [conversationId]: msgs }));
    },
    markRead: async (conversationId: number) => {
      try {
        await api.post(`/api/messaging/conversations/${conversationId}/mark-read`);
        // Update local state: mark mine as already read is not necessary here; refresh list instead
        fetchConversations().catch(() => {});
      } catch {}
    },
    emitTyping: (conversationId: number, isTyping: boolean) => {
      const u: any = user;
      if (!u || !socketRef.current) return;
      socketRef.current.emit('typing', {
        schoolId: u.schoolId ?? u.school_id,
        conversationId,
        userId: u.id,
        isTyping
      });
    },
    send: async (conversationId: number, content: string, receiverId?: number, receiverType?: string) => {
      const res = await api.post<any>(`/api/messaging/conversations/${conversationId}/messages`, { content });
      const m = res.message;
      const mapped: Message = {
        id: m.id,
        conversation_id: m.conversationId,
        sender_id: m.senderId,
        sender_type: m.senderRole as any,
        content: m.content,
        created_at: m.timestamp,
        is_read: m.isRead,
      };
      setMessages(prev => ({
        ...prev,
        [conversationId]: [...(prev[conversationId] || []), mapped]
      }));
    }
  }), [conversations, messages]);

  return <MessagingContext.Provider value={value}>{children}</MessagingContext.Provider>;
};

export function useMessaging() {
  const ctx = useContext(MessagingContext);
  if (!ctx) throw new Error('useMessaging must be used within MessagingProvider');
  return ctx;
}
