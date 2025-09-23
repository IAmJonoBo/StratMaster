/**
 * StratMaster Mobile App
 * Main application component with navigation and authentication
 */

import React, { useEffect, useState } from 'react';
import {
  SafeAreaProvider,
  SafeAreaView,
} from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
  StatusBar,
  StyleSheet,
  useColorScheme,
  Alert,
} from 'react-native';
import messaging from '@react-native-firebase/messaging';
import { Colors } from 'react-native/Libraries/NewAppScreen';
import Icon from 'react-native-vector-icons/MaterialIcons';

// Screens
import LoginScreen from './src/screens/LoginScreen';
import ApprovalsScreen from './src/screens/ApprovalsScreen';
import ApprovalDetailScreen from './src/screens/ApprovalDetailScreen';
import StrategiesScreen from './src/screens/StrategiesScreen';
import StrategyDetailScreen from './src/screens/StrategyDetailScreen';
import NotificationsScreen from './src/screens/NotificationsScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import SettingsScreen from './src/screens/SettingsScreen';

// Services
import { AuthService } from './src/services/AuthService';
import { NotificationService } from './src/services/NotificationService';
import { useAuthStore } from './src/stores/authStore';

// Navigation types
export type RootStackParamList = {
  Login: undefined;
  Main: undefined;
  ApprovalDetail: { approvalId: string };
  StrategyDetail: { strategyId: string };
  Settings: undefined;
};

export type MainTabParamList = {
  Approvals: undefined;
  Strategies: undefined;
  Notifications: undefined;
  Profile: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

const MainTabs: React.FC = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Approvals':
              iconName = 'approval';
              break;
            case 'Strategies':
              iconName = 'lightbulb';
              break;
            case 'Notifications':
              iconName = 'notifications';
              break;
            case 'Profile':
              iconName = 'person';
              break;
            default:
              iconName = 'help';
          }

          return <Icon name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#1E40AF',
        tabBarInactiveTintColor: '#6B7280',
        headerStyle: {
          backgroundColor: '#1E40AF',
        },
        headerTintColor: '#FFFFFF',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen 
        name="Approvals" 
        component={ApprovalsScreen}
        options={{
          title: 'Approvals',
          tabBarBadge: undefined, // Will be set by notification count
        }}
      />
      <Tab.Screen 
        name="Strategies" 
        component={StrategiesScreen}
        options={{
          title: 'Strategies',
        }}
      />
      <Tab.Screen 
        name="Notifications" 
        component={NotificationsScreen}
        options={{
          title: 'Notifications',
          tabBarBadge: undefined, // Will be set by unread count
        }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        options={{
          title: 'Profile',
        }}
      />
    </Tab.Navigator>
  );
};

const App: React.FC = () => {
  const isDarkMode = useColorScheme() === 'dark';
  const { isAuthenticated, isLoading, initializeAuth } = useAuthStore();
  const [initializing, setInitializing] = useState(true);

  const backgroundStyle = {
    backgroundColor: isDarkMode ? Colors.darker : Colors.lighter,
    flex: 1,
  };

  useEffect(() => {
    // Initialize authentication
    const initAuth = async () => {
      try {
        await initializeAuth();
      } catch (error) {
        console.error('Failed to initialize auth:', error);
      } finally {
        setInitializing(false);
      }
    };

    initAuth();
  }, [initializeAuth]);

  useEffect(() => {
    // Initialize push notifications
    const setupNotifications = async () => {
      try {
        await NotificationService.initialize();
        await NotificationService.requestPermission();
        
        // Handle notification when app is in foreground
        const unsubscribeOnMessage = messaging().onMessage(async remoteMessage => {
          Alert.alert(
            remoteMessage.notification?.title || 'Notification',
            remoteMessage.notification?.body || 'You have a new notification'
          );
        });

        // Handle notification tap when app is in background
        messaging().onNotificationOpenedApp(remoteMessage => {
          console.log('Notification caused app to open from background:', remoteMessage);
          // Navigate to appropriate screen based on notification data
          if (remoteMessage.data?.approval_id) {
            // Navigate to approval detail
          }
        });

        // Handle notification tap when app is closed
        messaging()
          .getInitialNotification()
          .then(remoteMessage => {
            if (remoteMessage) {
              console.log('Notification caused app to open from quit state:', remoteMessage);
              // Navigate to appropriate screen based on notification data
            }
          });

        return () => {
          unsubscribeOnMessage();
        };
      } catch (error) {
        console.error('Failed to setup notifications:', error);
      }
    };

    if (isAuthenticated && !isLoading) {
      setupNotifications();
    }
  }, [isAuthenticated, isLoading]);

  if (initializing || isLoading) {
    // Show loading screen
    return (
      <SafeAreaProvider>
        <SafeAreaView style={[backgroundStyle, styles.center]}>
          <StatusBar
            barStyle={isDarkMode ? 'light-content' : 'dark-content'}
            backgroundColor={backgroundStyle.backgroundColor}
          />
          {/* Loading component would go here */}
        </SafeAreaView>
      </SafeAreaProvider>
    );
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <StatusBar
          barStyle={isDarkMode ? 'light-content' : 'dark-content'}
          backgroundColor={backgroundStyle.backgroundColor}
        />
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
          }}
        >
          {!isAuthenticated ? (
            <Stack.Screen 
              name="Login" 
              component={LoginScreen}
              options={{
                headerShown: false,
              }}
            />
          ) : (
            <>
              <Stack.Screen 
                name="Main" 
                component={MainTabs}
                options={{
                  headerShown: false,
                }}
              />
              <Stack.Screen 
                name="ApprovalDetail" 
                component={ApprovalDetailScreen}
                options={{
                  headerShown: true,
                  title: 'Approval Details',
                  headerStyle: {
                    backgroundColor: '#1E40AF',
                  },
                  headerTintColor: '#FFFFFF',
                }}
              />
              <Stack.Screen 
                name="StrategyDetail" 
                component={StrategyDetailScreen}
                options={{
                  headerShown: true,
                  title: 'Strategy Details',
                  headerStyle: {
                    backgroundColor: '#1E40AF',
                  },
                  headerTintColor: '#FFFFFF',
                }}
              />
              <Stack.Screen 
                name="Settings" 
                component={SettingsScreen}
                options={{
                  headerShown: true,
                  title: 'Settings',
                  headerStyle: {
                    backgroundColor: '#1E40AF',
                  },
                  headerTintColor: '#FFFFFF',
                }}
              />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

const styles = StyleSheet.create({
  center: {
    justifyContent: 'center',
    alignItems: 'center',
  },
});

export default App;