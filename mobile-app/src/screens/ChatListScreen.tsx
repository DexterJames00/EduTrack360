import React, { useEffect } from 'react';
import { View, FlatList, RefreshControl, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useMessaging } from '@context/MessagingContext';
import { List, Divider, Badge, Text, Avatar } from 'react-native-paper';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { format, isToday, isThisYear } from 'date-fns';
import SchoolAppbar from '@components/SchoolAppbar';
import { useAuth } from '@context/AuthContext';

export default function ChatListScreen() {
  const navigation = useNavigation<any>();
  const { conversations, refreshConversations } = useMessaging();
  const insets = useSafeAreaInsets();
  const { user } = useAuth();
  const theme = require('react-native-paper').useTheme();

  useEffect(() => {
    refreshConversations();
  }, []);

  // Header will show school name via SchoolAppbar (same as Home)

  const formatWhen = (iso?: string) => {
    if (!iso) return '';
    const d = new Date(iso);
    if (isToday(d)) return format(d, 'p');
    if (isThisYear(d)) return format(d, 'MMM d');
    return format(d, 'MMM d, yyyy');
  };

  const getInitials = (name?: string) => {
    if (!name) return '?';
    const parts = name.trim().split(/\s+/);
    const a = parts[0]?.[0] || '';
    const b = parts[1]?.[0] || '';
    return (a + b).toUpperCase();
  };

  const colorPalette = ['#93c5fd', '#a5b4fc', '#fda4af', '#86efac', '#fde68a', '#c4b5fd'];
  const colorFromString = (s?: string) => {
    if (!s) return '#e5e7eb';
    let hash = 0;
    for (let i = 0; i < s.length; i++) hash = s.charCodeAt(i) + ((hash << 5) - hash);
    const idx = Math.abs(hash) % colorPalette.length;
    return colorPalette[idx];
  };

  const getDescMeta = (text?: string) => {
    const t = text || '';
    const lower = t.toLowerCase();
    if (lower.includes('academic')) return { icon: 'book-open-variant' as const, text: t };
    if (lower.includes('attendance')) return { icon: 'calendar-check' as const, text: t };
    if (lower.includes('meeting')) return { text: t } as { text: string; icon?: any }; // no icon for meetings
    if (lower.includes('notification')) return { icon: 'bell-outline' as const, text: t };
    return { icon: 'message-text-outline' as const, text: t };
  };

  return (
  <View style={{ flex: 1, backgroundColor: theme.colors.background }}>
  <FlatList
    contentContainerStyle={[styles.container, { paddingTop: 0, paddingBottom: 8 }]}
        data={conversations}
        keyExtractor={(item) => String(item.id)}
        refreshControl={<RefreshControl refreshing={false} onRefresh={refreshConversations} />}
  ListHeaderComponent={<SchoolAppbar />}
        renderItem={({ item }) => (
          <>
            <List.Item
              title={item.title}
              titleStyle={{ fontWeight: '600' }}
              description={() => {
                const meta = getDescMeta(item.last_message);
                return (
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    {'icon' in meta && meta.icon ? (
                      <MaterialCommunityIcons name={meta.icon as any} size={16} color="#6b7280" />
                    ) : null}
                    <Text numberOfLines={1} style={{ marginLeft: 6, color: '#4b5563' }}>{meta.text || ' '}</Text>
                  </View>
                );
              }}
              descriptionNumberOfLines={1}
              onPress={() => navigation.navigate('ChatDetail' as never, { conversationId: item.id, title: item.title } as never)}
              left={() => (
                <Avatar.Text
                  size={40}
                  label={getInitials(item.title)}
                  style={{ backgroundColor: colorFromString(item.title) }}
                  color="#111827"
                />
              )}
              right={() => (
                <View style={{ alignItems: 'flex-end', justifyContent: 'center', minWidth: 56 }}>
                  <Text variant="labelSmall" style={{ opacity: 0.6 }}>{formatWhen(item.updated_at)}</Text>
                  {item.unread_count ? (
                    <Badge style={{ marginTop: 6, backgroundColor: '#d32f2f' }} size={18}>{item.unread_count}</Badge>
                  ) : null}
                </View>
              )}
            />
            <Divider leftInset />
          </>
        )}
        ListEmptyComponent={<View style={styles.empty}><Text>No conversations.</Text></View>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { paddingVertical: 4 },
  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingTop: 80 },
  // no FAB per request
});
