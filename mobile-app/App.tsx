import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Provider as PaperProvider } from 'react-native-paper';
import { AuthProvider } from './src/context/AuthContext';
import { MessagingProvider } from './src/context/MessagingContext';
import { ThemeProvider, useThemeMode } from './src/context/ThemeContext';
import LoginScreen from './src/screens/LoginScreen';
import ChatDetailScreen from './src/screens/ChatDetailScreen';
import AppTabs from './src/navigation/AppTabs';
import { useAuth } from './src/context/AuthContext';

export type RootStackParamList = {
  Login: undefined;
  Main: undefined; // Tab navigator
  ChatDetail: { conversationId: number; title: string };
  Attendance: undefined;
};
import AttendanceScreen from './src/screens/AttendanceScreen';

const Stack = createStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <ThemedApp />
      </ThemeProvider>
    </SafeAreaProvider>
  );
}

function ThemedApp() {
  const { theme, navTheme } = useThemeMode();
  return (
    <PaperProvider theme={theme}>
      <AuthProvider>
        <MessagingProvider>
          <NavigationContainer theme={navTheme}>
            <MainNavigator />
          </NavigationContainer>
        </MessagingProvider>
      </AuthProvider>
    </PaperProvider>
  );
}

function MainNavigator() {
  const { user } = useAuth();
  return (
    <Stack.Navigator>
      {user ? (
        <>
          <Stack.Screen name="Main" component={AppTabs} options={{ headerShown: false }} />
          <Stack.Screen
            name="ChatDetail"
            component={ChatDetailScreen}
            options={({ route }: { route: { params: { title: string } } }) => ({ title: route.params.title })}
          />
          <Stack.Screen name="Attendance" component={AttendanceScreen} options={{ headerShown: false }} />
        </>
      ) : (
        <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
      )}
    </Stack.Navigator>
  );
}
