import React, { useEffect, useMemo, useState } from 'react';
import { View, StyleSheet, FlatList } from 'react-native';
import { Appbar, ActivityIndicator, Card, Text, List, Divider, Chip, MD3Colors, useTheme } from 'react-native-paper';
import ScreenHeader from '@components/ScreenHeader';
import { useNavigation } from '@react-navigation/native';
import api from '@services/api.service';
import type { AttendanceHistoryResult, AttendanceItem, AttendanceSummary } from '@types';

function formatDate(d: string | null): string {
  if (!d) return '-';
  try {
    const date = new Date(d);
    return date.toLocaleDateString();
  } catch {
    return d;
  }
}

function StatusChip({ status }: { status: string }) {
  const { fg, bg } = useMemo(() => {
    const s = (status || '').toLowerCase();
    if (s.includes('present')) return { fg: '#16a34a', bg: 'rgba(22,163,74,0.15)' }; // green
    if (s.includes('late')) return { fg: '#f59e0b', bg: 'rgba(245,158,11,0.15)' }; // orange/amber
    if (s.includes('absent')) return { fg: '#ef4444', bg: 'rgba(239,68,68,0.15)' }; // red
    return { fg: '#6b7280', bg: 'rgba(107,114,128,0.15)' }; // gray
  }, [status]);
  return <Chip style={{ backgroundColor: bg }} textStyle={{ color: fg }}>{status}</Chip>;
}

export default function AttendanceScreen() {
  const navigation = useNavigation<any>();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<AttendanceSummary | null>(null);
  const [history, setHistory] = useState<AttendanceHistoryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, h] = await Promise.all([
        api.getAttendanceSummary<AttendanceSummary>(),
        api.getAttendanceHistory<AttendanceHistoryResult>(50),
      ]);
      setSummary(s);
      setHistory(h);
    } catch (e: any) {
      setError(e?.response?.data?.message || e?.message || 'Failed to load attendance');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
  <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Appbar.Header mode="small" elevated style={{ backgroundColor: theme.colors.primary }}>
        <Appbar.BackAction onPress={() => navigation.goBack()} color={theme.colors.onPrimary} />
        <Appbar.Content
          title="Attendance"
          subtitle="Summary & History"
          titleStyle={{ color: theme.colors.onPrimary }}
          subtitleStyle={{ color: theme.colors.onPrimary, opacity: 0.8 }}
        />
        <Appbar.Action icon="refresh" onPress={load} color={theme.colors.onPrimary} />
      </Appbar.Header>

      <ScreenHeader title="Attendance" subtitle="Summary & history" icon="calendar-check" />
      {loading ? (
        <View style={styles.center}><ActivityIndicator /></View>
      ) : error ? (
        <View style={styles.center}><Text style={{ color: MD3Colors.error50 }}>{error}</Text></View>
      ) : (
        <FlatList
          ListHeaderComponent={
            <View style={styles.content}>
              <Card style={styles.card}>
                <Card.Title title="Today" subtitle="Entries for today" left={(p) => <List.Icon {...p} icon="calendar-today" />} />
                <Card.Content>
                  {summary?.today?.length ? (
                    summary.today.map((t, idx) => (
                      <View key={idx} style={{ marginBottom: 8 }}>
                        <Text>{formatDate(t.date)} • {t.subject || '—'} • {t.instructor || '—'}</Text>
                        <StatusChip status={t.status} />
                        {idx < (summary.today.length - 1) && <Divider style={{ marginTop: 8 }} />}
                      </View>
                    ))
                  ) : (
                    <Text>No entries today.</Text>
                  )}
                </Card.Content>
              </Card>

              <Card style={styles.card}>
                <Card.Title title="Totals" subtitle="All-time" left={(p) => <List.Icon {...p} icon="chart-areaspline" />} />
                <Card.Content>
                  {summary?.totals ? (
                    Object.entries(summary.totals).map(([k, v]) => (
                      <List.Item key={k} title={`${k}: ${v}`} left={(p) => <List.Icon {...p} icon={k.toLowerCase().includes('present') ? 'check-circle' : k.toLowerCase().includes('absent') ? 'close-circle' : 'clock-outline'} />} />
                    ))
                  ) : (
                    <Text>No totals available.</Text>
                  )}
                </Card.Content>
              </Card>

              <Text style={{ marginVertical: 8, marginLeft: 8, opacity: 0.6 }}>Recent History</Text>
            </View>
          }
          data={history?.items || []}
          keyExtractor={(_, idx) => String(idx)}
          renderItem={({ item }: { item: AttendanceItem }) => (
            <List.Item
              title={`${formatDate(item.date)} • ${item.subject || '—'}`}
              description={item.instructor || undefined}
              left={(p) => <List.Icon {...p} icon="book-open-variant" />}
              right={() => <StatusChip status={item.status} />}
            />
          )}
          ItemSeparatorComponent={Divider}
          contentContainerStyle={{ paddingBottom: 24 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16 },
  card: { marginBottom: 12 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
