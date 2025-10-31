import React, { useEffect, useMemo, useRef, useState } from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { RouteProp, useRoute } from '@react-navigation/native';
import { RootStackParamList } from '../../App';
import { useMessaging } from '@context/MessagingContext';
import { useAuth } from '@context/AuthContext';
import { TextInput, IconButton, useTheme, Text, Divider } from 'react-native-paper';
import { format, isSameDay } from 'date-fns';

export default function ChatDetailScreen() {
  const route = useRoute<RouteProp<RootStackParamList, 'ChatDetail'>>();
  const { messages, send, loadMessages, markRead } = useMessaging();
  const { user } = useAuth();
  const theme = useTheme();
  const [text, setText] = useState('');
  const items = messages[route.params.conversationId] || [];
  const listRef = useRef<FlatList>(null);

  useEffect(() => {
    loadMessages(route.params.conversationId);
    // Immediately mark messages as read when opening
    markRead(route.params.conversationId);
  }, [route.params.conversationId]);

  useEffect(() => {
    // scroll to bottom on new messages
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 50);
  }, [items.length]);

  const isMine = (senderType: string) => senderType === user?.role;
  useEffect(() => {
    // Mark read again if new messages arrived while viewing this conversation
    if (items.length) markRead(route.params.conversationId);
  }, [items.length]);

  return (
    <View style={styles.container}>
      <FlatList
        ref={listRef}
        contentContainerStyle={{ padding: 12 }}
        data={items}
        keyExtractor={(m) => String(m.id)}
        renderItem={({ item, index }) => {
          const mine = isMine(item.sender_type as any);
          const prev = index > 0 ? items[index - 1] : undefined;
          const showDateHeader = !prev || !isSameDay(new Date(prev.created_at), new Date(item.created_at));
          return (
            <View>
              {showDateHeader && (
                <View style={styles.dayRow}>
                  <Divider style={{ flex: 1 }} />
                  <Text style={styles.dayText}>{format(new Date(item.created_at), 'PPP')}</Text>
                  <Divider style={{ flex: 1 }} />
                </View>
              )}
              <View style={[styles.bubble, mine ? styles.mine : styles.theirs, { backgroundColor: mine ? theme.colors.primary : '#e6f0ff' }]}>
                <Text style={{ color: mine ? 'white' : '#111' }}>{item.content}</Text>
                <Text style={[styles.time, { color: mine ? 'rgba(255,255,255,0.85)' : '#555' }]}>
                  {format(new Date(item.created_at), 'p')}
                  {mine ? `  ${item.is_read ? '✓✓' : '✓'}` : ''}
                </Text>
              </View>
            </View>
          );
        }}
      />
      {user?.role !== 'parent' && (
        <View style={styles.inputRow}>
          <TextInput
            mode="outlined"
            style={styles.input}
            value={text}
            onChangeText={setText}
            placeholder="Type a message"
            onSubmitEditing={async () => {
              if (!text.trim()) return;
              await send(route.params.conversationId, text);
              setText('');
            }}
          />
          <IconButton
            icon="send"
            mode="contained-tonal"
            onPress={async () => {
              if (!text.trim()) return;
              await send(route.params.conversationId, text);
              setText('');
            }}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  bubble: { paddingVertical: 10, paddingHorizontal: 12, marginVertical: 6, maxWidth: '80%', borderRadius: 16 },
  mine: { alignSelf: 'flex-end', borderBottomRightRadius: 4 },
  theirs: { alignSelf: 'flex-start', borderBottomLeftRadius: 4 },
  inputRow: { flexDirection: 'row', padding: 8, borderTopWidth: 1, borderColor: '#eee', alignItems: 'center' },
  input: { flex: 1, marginRight: 8 },
  dayRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginVertical: 6 },
  dayText: { marginHorizontal: 8, opacity: 0.6 },
  time: { fontSize: 10, alignSelf: 'flex-end', marginTop: 4 }
});
