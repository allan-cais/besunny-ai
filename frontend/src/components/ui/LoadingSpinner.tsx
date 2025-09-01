import React from 'react';
import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
  xl: 'h-12 w-12',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className,
  text 
}) => {
  return (
    <div className="flex flex-col items-center justify-center">
      <div
        className={cn(
          'animate-spin rounded-full border-2 border-gray-300 border-t-blue-600',
          sizeClasses[size],
          className
        )}
      />
      {text && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          {text}
        </p>
      )}
    </div>
  );
};

// Page loading spinner
export const PageSpinner: React.FC<{ text?: string }> = ({ text = 'Loading...' }) => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="xl" text={text} />
  </div>
);

// Inline loading spinner
export const InlineSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'sm' }) => (
  <LoadingSpinner size={size} />
);

// Button loading spinner
export const ButtonSpinner: React.FC<{ size?: 'sm' | 'md' | 'lg' }> = ({ size = 'sm' }) => (
  <LoadingSpinner size={size} />
);
