export class NotificationService {
  static async initialize(): Promise<void> {
    console.log('Notification service initialized');
  }

  static async requestPermission(): Promise<boolean> {
    console.log('Requesting notification permission');
    return true;
  }
}