import React, { useEffect, useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, Button, Card, ActivityIndicator, MD3Colors, Appbar, List, Divider } from 'react-native-paper';
import { useNavigation } from '@react-navigation/native';
import api from '@services/api.service';
import { useAuth } from '@context/AuthContext';

export default function SchoolScreen() {
  const navigation = useNavigation<any>();
  const { user, logout } = useAuth();
  const [loading, setLoading] = useState(true);
  const [school, setSchool] = useState<any>(null);

  useEffect(() => {
    (async () => {
      try {
        const sid = (user as any)?.schoolId ?? (user as any)?.school_id;
        if (sid) {
          const data = await api.get(`/api/schools/${sid}`);
          setSchool(data);
        }
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Appbar.Header mode="small" elevated>
        <Appbar.Content title={school?.name || 'Your School'} subtitle={school?.schoolCode ? `Code: ${school.schoolCode}` : undefined} />
        <Appbar.Action icon="logout" onPress={logout} />
      </Appbar.Header>

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
          <Card.Title title="School Stats" subtitle="Overview" left={(props) => <List.Icon {...props} icon="chart-bar" />} />
          <Card.Content>
            <List.Item title={`Students: ${school?.stats?.students ?? '-'}`} left={(p) => <List.Icon {...p} icon="account-school" />} />
            <Divider />
            <List.Item title={`Instructors: ${school?.stats?.instructors ?? '-'}`} left={(p) => <List.Icon {...p} icon="teach" />} />
            <Divider />
            <List.Item title={`Subjects: ${school?.stats?.subjects ?? '-'}`} left={(p) => <List.Icon {...p} icon="book-open-variant" />} />
            <Divider />
            <List.Item title={`Sections: ${school?.stats?.sections ?? '-'}`} left={(p) => <List.Icon {...p} icon="view-list" />} />
          </Card.Content>
        </Card>

        <Button style={{ marginTop: 16 }} icon="logout" textColor={MD3Colors.error50} onPress={logout}>Logout</Button>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f6f7fb' },
  content: { padding: 16 },
  card: { marginBottom: 12 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' }
});
