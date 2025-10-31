import React from 'react';
import { createBottomTabNavigator, BottomTabNavigationOptions } from '@react-navigation/bottom-tabs';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import SchoolScreen from '@screens/SchoolScreen';
import ChatListScreen from '@screens/ChatListScreen';
import ProfileScreen from '@screens/ProfileScreen';
import { useAuth } from '@context/AuthContext';

export type TabParamList = {
  Home: undefined;
  Chats: undefined;
  Profile: undefined;
};

const Tab = createBottomTabNavigator<TabParamList>();

export default function AppTabs() {
  const { user } = useAuth();
  return (
    <Tab.Navigator
      initialRouteName="Chats"
      screenOptions={({ route }: { route: { name: keyof TabParamList } }): BottomTabNavigationOptions => ({
        headerShown: false,
        tabBarIcon: ({ color, size }: { color: string; size: number }) => {
          const icon = route.name === 'Home' ? 'home-variant' : route.name === 'Chats' ? 'message-text' : 'account-circle';
          return <MaterialCommunityIcons name={icon} color={color} size={size} />;
        }
      })}
    >
      <Tab.Screen name="Home" component={SchoolScreen} options={{ title: 'Home' }} />
      <Tab.Screen name="Chats" component={ChatListScreen} options={{ title: user?.role === 'parent' ? 'Notifications' : 'Chats' }} />
      <Tab.Screen name="Profile" component={ProfileScreen} options={{ title: 'Profile' }} />
    </Tab.Navigator>
  );
}
