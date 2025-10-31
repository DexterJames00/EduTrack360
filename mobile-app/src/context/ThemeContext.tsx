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
    const base = (mode === 'dark' || (mode === 'system' && system === 'dark')) ? MD3DarkTheme : MD3LightTheme;
    return {
      ...base,
      colors: {
        ...base.colors,
        primary: '#2563eb',
        secondary: '#10b981',
      }
    } as MD3Theme;
  }, [mode, system]);

  // Create a matching navigation theme using Paper's adapter
  const { LightTheme: AdaptedLight, DarkTheme: AdaptedDark } = adaptNavigationTheme({
    reactNavigationLight: NavigationLightTheme,
    reactNavigationDark: NavigationDarkTheme,
  });
  const navTheme: NavigationTheme = useMemo(() => (
    (mode === 'dark' || (mode === 'system' && system === 'dark')) ? AdaptedDark : AdaptedLight
  ), [mode, system, AdaptedDark, AdaptedLight]);

  const value = useMemo(() => ({ theme, navTheme, mode, setMode }), [theme, navTheme, mode]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export function useThemeMode() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useThemeMode must be used within ThemeProvider');
  return ctx;
}
