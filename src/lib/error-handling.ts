// Standardized Error Handling
// Provides consistent error handling patterns across the application

import { features } from '../config';

// Error types
export enum ErrorType {
  AUTHENTICATION = 'authentication',
  AUTHORIZATION = 'authorization',
  VALIDATION = 'validation',
  NETWORK = 'network',
  DATABASE = 'database',
  EXTERNAL_API = 'external_api',
  UNKNOWN = 'unknown',
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

// Error context interface
export interface ErrorContext {
  userId?: string;
  projectId?: string;
  action?: string;
  component?: string;
  timestamp: string;
  userAgent?: string;
  url?: string;
  // Additional context properties for specific services
  type?: string;
  documentId?: string;
  query?: string;
  limit?: number;
  watchActive?: boolean;
}

// Application error class
export class AppError extends Error {
  public readonly type: ErrorType;
  public readonly severity: ErrorSeverity;
  public readonly context: ErrorContext;
  public readonly originalError?: Error;
  public readonly isOperational: boolean;

  constructor(
    message: string,
    type: ErrorType = ErrorType.UNKNOWN,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Partial<ErrorContext> = {},
    originalError?: Error,
    isOperational: boolean = true
  ) {
    super(message);
    this.name = 'AppError';
    this.type = type;
    this.severity = severity;
    this.context = {
      timestamp: new Date().toISOString(),
      ...context,
    };
    this.originalError = originalError;
    this.isOperational = isOperational;

    // Maintain proper stack trace
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, AppError);
    }
  }
}

// Error handler interface
export interface ErrorHandler {
  handle(error: AppError): void;
  report(error: AppError): void;
  log(error: AppError): void;
}

// Default error handler implementation
export class DefaultErrorHandler implements ErrorHandler {
  handle(error: AppError): void {
    // Log the error
    this.log(error);

    // Report critical errors
    if (error.severity === ErrorSeverity.CRITICAL) {
      this.report(error);
    }

    // Handle operational errors gracefully
    if (error.isOperational) {
      this.handleOperationalError(error);
    } else {
      this.handleProgrammerError(error);
    }
  }

  report(error: AppError): void {
    if (features.isErrorReportingEnabled()) {
      // Send to error reporting service (e.g., Sentry)
      try {
        // This would integrate with your error reporting service
        console.error('Error reported:', {
          message: error.message,
          type: error.type,
          severity: error.severity,
          context: error.context,
          stack: error.stack,
        });
      } catch (reportingError) {
        console.error('Failed to report error:', reportingError);
      }
    }
  }

  log(error: AppError): void {
    const logLevel = this.getLogLevel(error.severity);
    const logMessage = this.formatLogMessage(error);

    if (logLevel === 'error') {
      console.error(logMessage);
    } else if (logLevel === 'warn') {
      console.warn(logMessage);
    } else if (logLevel === 'info') {
      // Use console.info for informational messages
      console.info(logMessage);
    }
  }

  private handleOperationalError(error: AppError): void {
    // Operational errors are expected and can be handled gracefully
    // They don't indicate a bug in the code
    if (features.isDebugMode()) {
      console.log('Operational error handled:', error.message);
    }
  }

  private handleProgrammerError(error: AppError): void {
    // Programmer errors indicate bugs in the code
    // They should be logged and reported
    console.error('Programmer error detected:', error);
    
    if (features.isDebugMode()) {
      // In development, show more details
      console.error('Stack trace:', error.stack);
      console.error('Context:', error.context);
    }
  }

  private getLogLevel(severity: ErrorSeverity): 'info' | 'warn' | 'error' {
    switch (severity) {
      case ErrorSeverity.LOW:
        return 'info';
      case ErrorSeverity.MEDIUM:
        return 'warn';
      case ErrorSeverity.HIGH:
      case ErrorSeverity.CRITICAL:
        return 'error';
      default:
        return 'info';
    }
  }

  private formatLogMessage(error: AppError): string {
    return `[${error.type.toUpperCase()}] ${error.message} | Severity: ${error.severity} | Context: ${JSON.stringify(error.context)}`;
  }
}

// Error factory functions
export const createError = {
  authentication: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.AUTHENTICATION, ErrorSeverity.HIGH, context, originalError),

  authorization: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.AUTHORIZATION, ErrorSeverity.HIGH, context, originalError),

  validation: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.VALIDATION, ErrorSeverity.MEDIUM, context, originalError),

  network: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.NETWORK, ErrorSeverity.MEDIUM, context, originalError),

  database: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.DATABASE, ErrorSeverity.HIGH, context, originalError),

  externalApi: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.EXTERNAL_API, ErrorSeverity.MEDIUM, context, originalError),

  unknown: (message: string, context?: Partial<ErrorContext>, originalError?: Error): AppError =>
    new AppError(message, ErrorType.UNKNOWN, ErrorSeverity.MEDIUM, context, originalError),
};

// Error handling utilities
export const errorUtils = {
  // Safely execute async functions with error handling
  async safeExecute<T>(
    fn: () => Promise<T>,
    context: Partial<ErrorContext> = {},
    fallback?: T
  ): Promise<T | undefined> {
    try {
      return await fn();
    } catch (error) {
      const appError = error instanceof AppError ? error : createError.unknown(
        error instanceof Error ? error.message : 'Unknown error occurred',
        context,
        error instanceof Error ? error : undefined
      );
      
      errorHandler.handle(appError);
      return fallback;
    }
  },

  // Safely execute sync functions with error handling
  safeExecuteSync<T>(
    fn: () => T,
    context: Partial<ErrorContext> = {},
    fallback?: T
  ): T | undefined {
    try {
      return fn();
    } catch (error) {
      const appError = error instanceof AppError ? error : createError.unknown(
        error instanceof Error ? error.message : 'Unknown error occurred',
        context,
        error instanceof Error ? error : undefined
      );
      
      errorHandler.handle(appError);
      return fallback;
    }
  },

  // Check if an error is operational
  isOperationalError(error: unknown): boolean {
    return error instanceof AppError && error.isOperational;
  },

  // Check if an error is a specific type
  isErrorType(error: unknown, type: ErrorType): boolean {
    return error instanceof AppError && error.type === type;
  },

  // Extract error message safely
  getErrorMessage(error: unknown): string {
    if (error instanceof AppError) {
      return error.message;
    }
    if (error instanceof Error) {
      return error.message;
    }
    return String(error);
  },
};

// Global error handler instance
export const errorHandler = new DefaultErrorHandler();

// Global error event handlers
if (typeof window !== 'undefined') {
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    const error = createError.unknown(
      'Unhandled promise rejection',
      { action: 'unhandled_promise_rejection' },
      event.reason instanceof Error ? event.reason : undefined
    );
    errorHandler.handle(error);
  });

  // Handle global errors
  window.addEventListener('error', (event) => {
    const error = createError.unknown(
      event.message || 'Global error occurred',
      { 
        action: 'global_error',
        url: event.filename,
        userAgent: navigator.userAgent,
      },
      event.error
    );
    errorHandler.handle(error);
  });
}

// Export default error handler for convenience
export default errorHandler;
