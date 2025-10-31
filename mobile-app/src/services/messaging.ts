import { io, Socket } from 'socket.io-client';
import { API_URL } from './api';
import { Message } from '@types';
import { api } from './api';

let socket: Socket | null = null;

export function initSocket(schoolId: number) {
  if (socket) return socket;
  socket = io(API_URL.replace('http', 'ws'), {
    transports: ['websocket'],
    path: '/socket.io',
    query: { school_id: String(schoolId) }
  });
  return socket;
}

export function onNewMessage(handler: (m: Message) => void) {
  socket?.on('new_message', handler);
}

export function disconnectSocket() {
  socket?.disconnect();
  socket = null;
}

export async function getConversations() {
  const { data } = await api.get('/api/messaging/conversations');
  return data;
}

export async function getMessages(conversationId: number) {
  const { data } = await api.get(`/api/messaging/${conversationId}/messages`);
  return data;
}

export async function sendMessage(conversationId: number, content: string, receiverId: number, receiverType: string) {
  const { data } = await api.post('/api/messaging/send', {
    conversation_id: conversationId,
    content,
    receiver_id: receiverId,
    receiver_type: receiverType
  });
  return data;
}
