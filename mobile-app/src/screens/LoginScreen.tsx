import React, { useState } from 'react';
import { View, StyleSheet, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { Text, TextInput, Button, HelperText, Surface } from 'react-native-paper';
import { StackScreenProps } from '@react-navigation/stack';
import { RootStackParamList } from '../../App';
import { useAuth } from '@context/AuthContext';

export default function LoginScreen({ navigation }: StackScreenProps<RootStackParamList, 'Login'>) {
  const { login, loading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    setError(null);
    try {
  await login({ username, password });
  // No manual navigation; authenticated state will render the Main tabs
    } catch (e: any) {
      setError(e?.message || 'Login failed');
    }
  };

  return (
    <KeyboardAvoidingView behavior={Platform.select({ ios: 'padding', android: undefined })} style={{ flex: 1 }}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.container}>
          <Text variant="displaySmall" style={styles.brand}>EduTrack360</Text>
          <Text variant="bodyMedium" style={styles.subtitle}>Sign in to continue</Text>

          <Surface elevation={2} style={styles.card}>
            {!!error && (
              <HelperText type="error" visible={!!error} style={{ marginBottom: 8 }}>
                {error}
              </HelperText>
            )}
            <TextInput
              mode="outlined"
              label="Username"
              value={username}
              onChangeText={setUsername}
              autoCapitalize="none"
              left={<TextInput.Icon icon="account" />}
              style={styles.input}
            />
            <TextInput
              mode="outlined"
              label="Password"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              left={<TextInput.Icon icon="lock" />}
              right={<TextInput.Icon icon={showPassword ? 'eye-off' : 'eye'} onPress={() => setShowPassword(v => !v)} />}
              style={styles.input}
            />
            <Button mode="contained" onPress={handleLogin} loading={loading} disabled={loading} style={{ marginTop: 4 }}>Login</Button>

            <Text variant="bodySmall" style={styles.hint}>
              Parent? Use your Student ID as username and the code provided by school as password.
            </Text>
          </Surface>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 16 },
  container: { width: '100%', maxWidth: 480, alignSelf: 'center' },
  brand: { fontWeight: '800', textAlign: 'center', color: '#111' },
  subtitle: { textAlign: 'center', opacity: 0.7, marginTop: 4, marginBottom: 16 },
  card: { borderRadius: 12, padding: 16 },
  input: { marginBottom: 12 },
  hint: { textAlign: 'center', opacity: 0.7, marginTop: 12 }
});
