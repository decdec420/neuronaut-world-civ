/**
 * Notification System
 *
 * Displays important events in the top-right corner.
 */

'use client';

import React, { useState, useEffect } from 'react';

export type NotificationType = 'discovery' | 'construction' | 'birth' | 'death' | 'event';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  timestamp: number;
  location?: { x: number; y: number };
}

interface NotificationSystemProps {
  notifications: Notification[];
  onNotificationClick?: (notification: Notification) => void;
  onDismiss?: (id: string) => void;
  maxVisible?: number;
  autoDismissDelay?: number;
}

const NOTIFICATION_ICONS: Record<NotificationType, string> = {
  discovery: '🎓',
  construction: '🏗️',
  birth: '👶',
  death: '💀',
  event: '⚡',
};

const NOTIFICATION_COLORS: Record<NotificationType, string> = {
  discovery: '#22d3ee',
  construction: '#fbbf24',
  birth: '#22c55e',
  death: '#ef4444',
  event: '#a855f7',
};

export default function NotificationSystem({
  notifications,
  onNotificationClick,
  onDismiss,
  maxVisible = 5,
  autoDismissDelay = 10000,
}: NotificationSystemProps) {
  const [visibleNotifications, setVisibleNotifications] = useState<Notification[]>([]);

  // Update visible notifications
  useEffect(() => {
    setVisibleNotifications(notifications.slice(-maxVisible));
  }, [notifications, maxVisible]);

  // Auto-dismiss old notifications
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now();
      visibleNotifications.forEach((notif) => {
        if (now - notif.timestamp > autoDismissDelay && onDismiss) {
          onDismiss(notif.id);
        }
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [visibleNotifications, autoDismissDelay, onDismiss]);

  if (visibleNotifications.length === 0) {
    return null;
  }

  return (
    <div
      className="fixed top-20 right-4 z-30 space-y-2"
      style={{
        maxWidth: '320px',
      }}
    >
      {visibleNotifications.map((notification, index) => {
        const age = Date.now() - notification.timestamp;
        const ageSeconds = Math.floor(age / 1000);
        const color = NOTIFICATION_COLORS[notification.type];
        const icon = NOTIFICATION_ICONS[notification.type];

        return (
          <div
            key={notification.id}
            className="transition-all hover:scale-105 cursor-pointer"
            style={{
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%)',
              backdropFilter: 'blur(20px)',
              border: `1px solid ${color}60`,
              borderRadius: '12px',
              padding: '12px',
              boxShadow: `0 4px 12px ${color}30, inset 0 1px 0 rgba(255, 255, 255, 0.1)`,
              animation: `slideIn 0.3s ease-out ${index * 0.1}s both`,
            }}
            onClick={() => {
              if (onNotificationClick) {
                onNotificationClick(notification);
              }
            }}
          >
            <div className="flex items-start gap-3">
              {/* Icon */}
              <div
                className="flex-shrink-0"
                style={{
                  fontSize: '24px',
                  filter: `drop-shadow(0 0 4px ${color})`,
                }}
              >
                {icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div
                  className="text-sm font-semibold"
                  style={{
                    color: '#ffffff',
                    lineHeight: '1.4',
                  }}
                >
                  {notification.message}
                </div>
                <div
                  className="text-xs mt-1"
                  style={{
                    color: 'rgba(148, 163, 184, 0.8)',
                  }}
                >
                  {ageSeconds < 60 ? `${ageSeconds}s ago` : `${Math.floor(ageSeconds / 60)}m ago`}
                </div>
              </div>

              {/* Dismiss button */}
              {onDismiss && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDismiss(notification.id);
                  }}
                  className="flex-shrink-0 hover:scale-110 transition-transform"
                  style={{
                    width: '20px',
                    height: '20px',
                    borderRadius: '50%',
                    background: 'rgba(100, 116, 139, 0.2)',
                    border: '1px solid rgba(100, 116, 139, 0.4)',
                    color: '#94a3b8',
                    fontSize: '12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  ✕
                </button>
              )}
            </div>

            {/* Progress bar (auto-dismiss indicator) */}
            <div
              className="mt-2 h-1 rounded-full overflow-hidden"
              style={{
                background: 'rgba(100, 116, 139, 0.2)',
              }}
            >
              <div
                className="h-full transition-all duration-1000"
                style={{
                  width: `${Math.max(0, 100 - (age / autoDismissDelay) * 100)}%`,
                  background: color,
                  boxShadow: `0 0 4px ${color}`,
                }}
              />
            </div>
          </div>
        );
      })}

      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  );
}

// Hook for managing notifications
export function useNotifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);

  const addNotification = (
    type: NotificationType,
    message: string,
    location?: { x: number; y: number }
  ) => {
    const notification: Notification = {
      id: `notif-${Date.now()}-${Math.random()}`,
      type,
      message,
      timestamp: Date.now(),
      location,
    };

    setNotifications((prev) => [...prev, notification]);
  };

  const dismissNotification = (id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  return {
    notifications,
    addNotification,
    dismissNotification,
    clearAll,
  };
}
