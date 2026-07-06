import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
}

export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('ar-IQ', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}
