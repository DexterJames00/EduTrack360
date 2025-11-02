import React, { useEffect, useState, useCallback, useRef } from 'react';
import { View, FlatList, RefreshControl, StyleSheet } from 'react-native';
import { List, Chip, Text, Card, useTheme, Divider } from 'react-native-paper';
import SchoolAppbar from '@components/SchoolAppbar';
import { format } from 'date-fns';
import api from '@services/api.service';
import type { MeetingItem } from '@types';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import io, { Socket } from 'socket.io-client';
import { useAuth } from '@context/AuthContext';

export default function MeetingsScreen() {
  const [items, setItems] = useState<MeetingItem[]>([]);
  const [loading, setLoading] = useState(false);
  const insets = useSafeAreaInsets();
  const theme = useTheme();
  const { user } = useAuth();
  const socketRef = useRef<Socket | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getMeetings<any>();
      let list: MeetingItem[] = [];
      if (Array.isArray(data?.meetings)) {
        list = data.meetings as MeetingItem[];
      } else if (Array.isArray(data?.items)) {
        // Map API fields to MeetingItem
        list = (data.items as any[]).map((it) => ({
          id: it.id,
          title: it.title,
          description: it.description ?? null,
          meeting_date: it.date,
          start_time: it.start,
          end_time: it.end,
          location: it.location ?? null,
          status: it.status,
          student_name: it.student ?? undefined,
          subject_name: it.subject ?? undefined,
        }));
      }
      setItems(list);
    } catch (e) {
      console.warn('Failed to load meetings', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Realtime: listen for meeting messages and refresh list
  useEffect(() => {
    if (!user) return;
    const url = api.getWebSocketUrl();
    const s = io(url, { path: '/socket.io', transports: ['websocket', 'polling'], forceNew: true });
    s.on('connect', () => {
      const schoolId = (user as any).schoolId ?? (user as any).school_id;
      if (schoolId) s.emit('join_school', { schoolId });
    });
    s.on('new_message', (payload: any) => {
      const t = payload.type || payload.message_type;
      if (t === 'meeting') {
        // meeting created/updated — reload list
        load();
      }
    });
    socketRef.current = s;
    return () => {
      s.disconnect();
      socketRef.current = null;
    };
  }, [user, load]);

  const whenStr = (d: string, s: string, e: string) => {
    try {
      const dd = new Date(d);
      return `${format(dd, 'EEE, MMM d, yyyy')} • ${s} - ${e}`;
    } catch {
      return `${d} • ${s}-${e}`;
    }
  };

  const statusColor = (st: MeetingItem['status']) => st === 'scheduled' ? '#059669' : st === 'cancelled' ? '#b91c1c' : '#2563eb';

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
  contentContainerStyle={{ paddingTop: 0, paddingBottom: 12 }}
        data={items}
        keyExtractor={(it) => String(it.id)}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
  ListHeaderComponent={
    <>
      <SchoolAppbar />
      <View style={{ height: 8 }} />
    </>
  }
        ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        renderItem={({ item }) => (
          <Card mode="elevated" style={{ marginHorizontal: 12, backgroundColor: theme.colors.surface }}>
            <Card.Content style={{ paddingVertical: 12 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                <View style={{ flex: 1 }}>
                  <Text variant="titleMedium" style={{ fontWeight: '700', color: theme.colors.onSurface }}>
                    {item.title}
                  </Text>
                  <Text variant="bodySmall" style={{ color: theme.colors.onSurface }}>
                    {whenStr(item.meeting_date, item.start_time, item.end_time)}
                  </Text>
                </View>
                <Chip mode="flat" style={{ backgroundColor: theme.dark ? '#1f2937' : '#f3f4f6' }} textStyle={{ color: statusColor(item.status) }}>
                  {item.status}
                </Chip>
              </View>
              <Divider style={{ marginVertical: 10, backgroundColor: theme.colors.outline }} />
              <View style={{ rowGap: 4 }}>
                {item.location ? (
                  <Text style={{ color: theme.colors.onSurface }}>� {item.location}</Text>
                ) : null}
                {item.student_name ? (
                  <Text style={{ color: theme.colors.onSurface }}>� {item.student_name}</Text>
                ) : null}
                {item.subject_name ? (
                  <Text style={{ color: theme.colors.onSurface }}>📖 {item.subject_name}</Text>
                ) : null}
              </View>
            </Card.Content>
          </Card>
        )}
          
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={{ color: theme.colors.onBackground, opacity: 0.7 }}>No meetings yet.</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
});
