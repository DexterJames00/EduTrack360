import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import { Text, List, RadioButton, Button, Divider, TextInput, HelperText, useTheme } from 'react-native-paper';
import SchoolAppbar from '@components/SchoolAppbar';
import { useAuth } from '@context/AuthContext';
import { useThemeMode } from '@context/ThemeContext';
import api from '@services/api.service';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const { mode, setMode } = useThemeMode();
  const theme = useTheme();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [expAccount, setExpAccount] = useState(true);
  const [expAppearance, setExpAppearance] = useState(true);
  const [expSecurity, setExpSecurity] = useState(true);
  const [schoolName, setSchoolName] = useState<string | null>(null);
  

  useEffect(() => {
    const sid = (user as any)?.schoolId ?? (user as any)?.school_id;
    if (!sid) return;
    (async () => {
      try {
        const data = await api.get<any>(`/api/schools/${sid}`);
        setSchoolName(data?.name || null);
      } catch {
        setSchoolName(null);
      }
    })();
  }, [user]);

  

  const onChangePassword = async () => {
    setSaving(true); setMessage(null); setError(null);
    try {
      const res = await api.post<any>('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });
      if (!res?.success) throw new Error(res?.message || 'Failed to change password');
      setMessage('Password updated successfully.');
      setCurrentPassword(''); setNewPassword(''); setConfirmPassword('');
    } catch (e: any) {
      setError(e?.response?.data?.message || e?.message || 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  return (
  <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <SchoolAppbar />
  <ScrollView contentContainerStyle={[styles.content, { paddingBottom: 32 }]}> 
      {/* Account Info */}
      <List.Section>
        <List.Accordion
          title="Account"
          expanded={expAccount}
          onPress={() => setExpAccount(!expAccount)}
          left={() => null}
        >
          {user?.role === 'parent' ? (
            <List.Item title="Student" description={`${(user as any)?.firstName ?? ''} ${(user as any)?.lastName ?? ''}`.trim() || (user as any)?.username || '-'} />
          ) : (
            <List.Item title="Username" description={user?.username || '-'} />
          )}
          <List.Item title="Role" description={user?.role || '-'} />
          {(((user as any)?.schoolId ?? (user as any)?.school_id)) ? (
            <List.Item title="School" description={schoolName || '-'} />
          ) : null}
        </List.Accordion>
      </List.Section>

      {/* Appearance */}
      <List.Section>
        <List.Accordion
          title="Appearance"
          expanded={expAppearance}
          onPress={() => setExpAppearance(!expAppearance)}
          left={() => null}
        >
          <RadioButton.Group onValueChange={(v) => setMode(v as any)} value={mode}>
            <List.Item title="Light" right={() => <RadioButton value="light" />} onPress={() => setMode('light')} />
            <List.Item title="Dark" right={() => <RadioButton value="dark" />} onPress={() => setMode('dark')} />
            <List.Item title="Use device theme" right={() => <RadioButton value="system" />} onPress={() => setMode('system')} />
          </RadioButton.Group>
        </List.Accordion>
      </List.Section>

      

      {/* Security */}
      <List.Section>
        <List.Accordion
          title="Security"
          expanded={expSecurity}
          onPress={() => setExpSecurity(!expSecurity)}
          left={() => null}
        >
          {user?.role === 'parent' ? (
            <Text style={{ marginHorizontal: 16, opacity: 0.7 }}>
              Parents use the student code to sign in. Password change isn’t available for parent accounts.
            </Text>
          ) : (
            <View style={{ paddingHorizontal: 16 }}>
              <TextInput
                label="Current password"
                value={currentPassword}
                onChangeText={setCurrentPassword}
                secureTextEntry
                style={{ marginBottom: 8 }}
              />
              <TextInput
                label="New password"
                value={newPassword}
                onChangeText={setNewPassword}
                secureTextEntry
                style={{ marginBottom: 8 }}
              />
              <TextInput
                label="Confirm new password"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry
                style={{ marginBottom: 8 }}
              />
              {!!message && <HelperText type="info" visible>{message}</HelperText>}
              {!!error && <HelperText type="error" visible>{error}</HelperText>}
              <Button mode="contained" loading={saving} disabled={saving} onPress={onChangePassword}>
                Change Password
              </Button>
            </View>
          )}
        </List.Accordion>
      </List.Section>

      <View style={{ paddingTop: 8 }}>
        <Button mode="contained" icon="logout" buttonColor={theme.colors.error} textColor={theme.colors.onPrimary} onPress={logout}>
          Logout
        </Button>
      </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f6f7fb' },
  content: { padding: 16 },
  header: { flexDirection: 'row', alignItems: 'center', paddingVertical: 12 }
});
