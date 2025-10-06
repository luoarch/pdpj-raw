'use client';

import { ReactNode, useEffect } from 'react';
import { useAuthStore } from '@/store/auth-store';
import { useAppStore } from '@/store/app-store';
import { Sidebar } from './sidebar';
import { Header } from './header';
import { LoadingSpinner } from '../ui/loading-spinner';
import { NotificationToast } from '../ui/notification-toast';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const { sidebarOpen, notifications, setTheme } = useAppStore();

  // Verificar autenticação ao carregar
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Aplicar tema do sistema
  useEffect(() => {
    setTheme('system');
  }, [setTheme]);

  // Se ainda está verificando autenticação
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  // Se não está autenticado, redirecionar para login
  if (!isAuthenticated) {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main Content */}
      <div className={`transition-all duration-300 ${
        sidebarOpen ? 'lg:ml-64' : 'lg:ml-16'
      }`}>
        {/* Header */}
        <Header />
        
        {/* Page Content */}
        <main className="p-6">
          {children}
        </main>
      </div>

      {/* Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map((notification) => (
          <NotificationToast
            key={notification.id}
            notification={notification}
          />
        ))}
      </div>
    </div>
  );
}
