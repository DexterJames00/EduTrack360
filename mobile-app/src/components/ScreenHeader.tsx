import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Text, useTheme, List } from 'react-native-paper';

interface ScreenHeaderProps {
  title: string;
  subtitle?: string;
  icon?: string; // MaterialCommunityIcons name
}

export default function ScreenHeader({ title, subtitle, icon }: ScreenHeaderProps) {
  const theme = useTheme();
  return (
    <View style={[styles.container, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outline }]}> 
      <View style={styles.row}>
        {icon ? <List.Icon icon={icon} color={theme.colors.primary} /> : null}
        <View style={{ flex: 1 }}>
          <Text variant="headlineSmall" style={{ fontWeight: '800', color: theme.colors.onSurface }}>{title}</Text>
          {subtitle ? (
            <Text variant="bodySmall" style={{ opacity: 0.7, color: theme.colors.onSurface }}>{subtitle}</Text>
          ) : null}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 12,
    marginBottom: 8,
    marginTop: 8,
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderWidth: StyleSheet.hairlineWidth,
  },
  row: { flexDirection: 'row', alignItems: 'center' }
});
