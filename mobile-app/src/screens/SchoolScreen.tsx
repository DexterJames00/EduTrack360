import React, { useEffect, useMemo, useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, Card, ActivityIndicator, MD3Colors, Appbar, List, Divider, useTheme } from 'react-native-paper';
import SchoolAppbar from '@components/SchoolAppbar';
import { useNavigation } from '@react-navigation/native';
import api from '@services/api.service';
import { useAuth } from '@context/AuthContext';

export default function SchoolScreen() {
  const navigation = useNavigation<any>();
  const { user, logout } = useAuth();
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [school, setSchool] = useState<any>(null);
  const [subjectsCount, setSubjectsCount] = useState<number | null>(null);
  const [instructorsCount, setInstructorsCount] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const sid = (user as any)?.schoolId ?? (user as any)?.school_id;
        if (sid) {
          const data = await api.get(`/api/schools/${sid}`);
          setSchool(data);
        }
        // Derive student info from attendance history (unique subjects and instructors)
        try {
          const history: any = await api.getAttendanceHistory<any>(100);
          const items: any[] = Array.isArray(history?.items) ? history.items : [];
          const subj = new Set<string>();
          const inst = new Set<string>();
          for (const it of items) {
            if (it?.subject) subj.add(String(it.subject));
            if (it?.instructor) inst.add(String(it.instructor));
          }
          setSubjectsCount(subj.size || 0);
          setInstructorsCount(inst.size || 0);
        } catch {
          setSubjectsCount(null);
          setInstructorsCount(null);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  const displayName = useMemo(() => {
    const first = (user as any)?.firstName;
    const last = (user as any)?.lastName;
    const full = [first, last].filter(Boolean).join(' ').trim();
    return full || (user as any)?.username || '—';
  }, [user]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
  <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
  <SchoolAppbar rightActions={<Appbar.Action icon="logout" onPress={logout} color={theme.dark ? theme.colors.error : '#fff'} />} />

      <View style={styles.content}>
        <Card style={styles.card}>
          <Card.Title title="Messages" subtitle="Chat with instructors" left={(props) => <List.Icon {...props} icon="message-text" />} />
          <Card.Content>
            <Text>Stay updated with real-time messages and notifications.</Text>
          </Card.Content>
          <Card.Actions>
            <Button mode="contained" onPress={() => navigation.navigate('Chats')}>Open Messages</Button>
          </Card.Actions>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Attendance" subtitle="Summary & History" left={(props) => <List.Icon {...props} icon="calendar-check" />} />
          <Card.Content>
            <Text>View today’s entries and your recent attendance history.</Text>
          </Card.Content>
          <Card.Actions>
            <Button mode="contained" onPress={() => navigation.navigate('Attendance')}>View Attendance</Button>
          </Card.Actions>
        </Card>

        <Card style={styles.card}>
          <Card.Title title="Student Info" subtitle="Overview" left={(props) => <List.Icon {...props} icon="account" />} />
          <Card.Content>
            <List.Item title={`Name: ${displayName}`} left={(p) => <List.Icon {...p} icon="account-circle" />} />
            <Divider />
            <List.Item title={`School: ${school?.name ?? '—'}`} left={(p) => <List.Icon {...p} icon="office-building" />} />
            <Divider />
            <List.Item title={`Subjects enrolled: ${subjectsCount ?? '—'}`} left={(p) => <List.Icon {...p} icon="book-open-variant" />} />
            <Divider />
            <List.Item title={`Instructors: ${instructorsCount ?? '—'}`} left={(p) => <List.Icon {...p} icon="teach" />} />
          </Card.Content>
        </Card>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16 },
  card: { marginBottom: 12 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' }
});
