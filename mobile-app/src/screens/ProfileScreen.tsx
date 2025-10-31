import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, List, RadioButton, Button, Divider, Avatar } from 'react-native-paper';
import { useAuth } from '@context/AuthContext';
import { useThemeMode } from '@context/ThemeContext';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const { mode, setMode } = useThemeMode();

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Avatar.Text size={56} label={(user?.username || 'U').slice(0,2).toUpperCase()} style={{ marginRight: 12 }} />
        <View style={{ flex: 1 }}>
          <Text variant="titleMedium">{user?.username || 'User'}</Text>
          <Text variant="bodySmall" style={{ opacity: 0.7 }}>{user?.role}</Text>
        </View>
      </View>
      <Divider />

      <List.Section title="Appearance">
        <RadioButton.Group onValueChange={(v) => setMode(v as any)} value={mode}>
          <List.Item title="Light" right={() => <RadioButton value="light" />} onPress={() => setMode('light')} />
          <List.Item title="Dark" right={() => <RadioButton value="dark" />} onPress={() => setMode('dark')} />
          <List.Item title="Use device theme" right={() => <RadioButton value="system" />} onPress={() => setMode('system')} />
        </RadioButton.Group>
      </List.Section>

      <Button mode="contained-tonal" onPress={logout} style={{ marginTop: 12 }}>Logout</Button>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16 },
  header: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12 }
});
