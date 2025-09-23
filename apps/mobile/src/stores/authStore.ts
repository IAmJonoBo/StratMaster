import { create } from 'zustand';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  isLoading: false,
  user: null,
  
  initializeAuth: async () => {
    set({ isLoading: true });
    
    // Mock authentication - in real app would check stored tokens
    setTimeout(() => {
      set({
        isAuthenticated: true,
        isLoading: false,
        user: {
          id: '1',
          name: 'John Doe',
          email: 'john@example.com'
        }
      });
    }, 1000);
  }
}));