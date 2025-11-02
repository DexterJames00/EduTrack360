import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { MD3DarkTheme, MD3LightTheme, MD3Theme, adaptNavigationTheme } from 'react-native-paper';
import { DarkTheme as NavigationDarkTheme, DefaultTheme as NavigationLightTheme, Theme as NavigationTheme } from '@react-navigation/native';
import { useColorScheme } from 'react-native';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeContextShape {
  theme: MD3Theme;
  navTheme: NavigationTheme;
  mode: ThemeMode;
  setMode: (m: ThemeMode) => Promise<void>;
}

const ThemeContext = createContext<ThemeContextShape | undefined>(undefined);

export const ThemeProvider: React.FC<{children: React.ReactNode}> = ({ children }) => {
  const system = useColorScheme();
  const [mode, setModeState] = useState<ThemeMode>('system');

  useEffect(() => {
    (async () => {
      const saved = await AsyncStorage.getItem('theme_mode');
      if (saved === 'light' || saved === 'dark' || saved === 'system') setModeState(saved);
    })();
  }, []);

  const setMode = async (m: ThemeMode) => {
    setModeState(m);
    await AsyncStorage.setItem('theme_mode', m);
  };

  const theme = useMemo(() => {
    const isDark = (mode === 'dark' || (mode === 'system' && system === 'dark'));
    const base = isDark ? MD3DarkTheme : MD3LightTheme;
    // Brand palette (blue + white)
  const brandPrimary = '#2563eb'; // blue-600
  const brandPrimaryDark = '#2563eb'; // use same strong blue in dark mode
  const bgLight = '#ffffff';
  const bgDark = '#000000'; // pure black for dark mode background
  const surfaceDark = '#0a0a0a'; // near-black surface

    const colors = {
      ...base.colors,
  primary: isDark ? brandPrimaryDark : brandPrimary,
      secondary: isDark ? '#38bdf8' : '#0ea5e9',
      background: isDark ? bgDark : bgLight,
      surface: isDark ? surfaceDark : bgLight,
      elevation: base.colors.elevation,
      onPrimary: '#ffffff',
      error: '#d32f2f',
      onError: '#ffffff',
      onSurface: isDark ? '#e5e7eb' : '#111827',
      onBackground: isDark ? '#e5e7eb' : '#111827',
      outline: isDark ? '#334155' : '#e5e7eb',
    } as MD3Theme['colors'];
    return { ...base, colors } as MD3Theme;
  }, [mode, system]);

  // Create a matching navigation theme using Paper's adapter
  const { LightTheme: AdaptedLight, DarkTheme: AdaptedDark } = adaptNavigationTheme({
    reactNavigationLight: NavigationLightTheme,
    reactNavigationDark: NavigationDarkTheme,
  });
  const navTheme: NavigationTheme = useMemo(() => {
    const isDark = (mode === 'dark' || (mode === 'system' && system === 'dark'));
    const adapted = isDark ? AdaptedDark : AdaptedLight;
    const primary = theme.colors.primary;
    return {
      ...adapted,
      colors: {
        ...adapted.colors,
        primary,
        background: theme.colors.background,
        card: theme.colors.surface,
        text: theme.colors.onBackground,
        border: theme.colors.outline,
      }
    } as NavigationTheme;
  }, [mode, system, AdaptedDark, AdaptedLight, theme]);

  const value = useMemo(() => ({ theme, navTheme, mode, setMode }), [theme, navTheme, mode]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export function useThemeMode() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useThemeMode must be used within ThemeProvider');
  return ctx;
}
