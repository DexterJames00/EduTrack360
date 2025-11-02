import React, { useEffect, useState } from 'react';
import { Appbar, useTheme } from 'react-native-paper';
import { useAuth } from '@context/AuthContext';
import api from '@services/api.service';

interface Props {
  rightActions?: React.ReactNode;
}

export default function SchoolAppbar({ rightActions }: Props) {
  const { user } = useAuth();
  const [school, setSchool] = useState<any>(null);
  const theme = useTheme();

  useEffect(() => {
    (async () => {
      try {
        const sid = (user as any)?.schoolId ?? (user as any)?.school_id;
        if (!sid) return;
        const data = await api.get(`/api/schools/${sid}`);
        setSchool(data);
      } catch {
        // ignore
      }
    })();
  }, [user]);

  return (
    <Appbar.Header mode="small" elevated style={{ backgroundColor: theme.colors.primary }}>
      <Appbar.Content
        title={school?.name || 'Your School'}
        subtitle={school?.schoolCode ? `Code: ${school.schoolCode}` : undefined}
        titleStyle={{ color: theme.colors.onPrimary }}
        subtitleStyle={{ color: theme.colors.onPrimary, opacity: 0.8 }}
      />
      {rightActions}
    </Appbar.Header>
  );
}
