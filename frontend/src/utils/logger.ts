/**
 * Logger utility for consistent logging across the application
 * Enhanced with local storage persistence and telemetry support
 */
import { LogLevel, LogEntry } from '../types/commonTypes';
import axios from 'axios';

/**
 * Configuration for the logger
 */
interface LoggerConfig {
  minLevel: LogLevel;
  enableConsole: boolean;
  storeLogs: boolean;
  maxLogSize: number;
  persistToLocalStorage: boolean;
  sendTelemetry: boolean;
  telemetryEndpoint?: string;
  telemetryFilter?: (entry: LogEntry) => boolean;
}

/**
 * Default logger configuration
 */
const defaultConfig: LoggerConfig = {
  minLevel: LogLevel.INFO,
  enableConsole: process.env.NODE_ENV !== 'production',
  storeLogs: true,
  maxLogSize: 100,
  persistToLocalStorage: true,
  sendTelemetry: process.env.REACT_APP_ENABLE_TELEMETRY === 'true',
  telemetryEndpoint: process.env.REACT_APP_TELEMETRY_ENDPOINT || 'http://localhost:5000/api/telemetry',
  telemetryFilter: (entry: LogEntry) => entry.message.includes('DEPRECATED_USAGE')
};

/**
 * Storage key for local storage
 */
const STORAGE_KEY = 'bms_onboarding_logs';

/**
 * Function to serialize a LogEntry for storage
 */
function serializeLogEntry(entry: LogEntry): string {
  return JSON.stringify({
    ...entry,
    timestamp: entry.timestamp.toISOString()
  });
}

/**
 * Function to deserialize a LogEntry from storage
 */
function deserializeLogEntry(serialized: string): LogEntry {
  const parsed = JSON.parse(serialized);
  return {
    ...parsed,
    timestamp: new Date(parsed.timestamp)
  };
}

/**
 * Initialize the log storage from local storage if available
 */
function initializeLogStorage(): LogEntry[] {
  if (typeof window === 'undefined' || !window.localStorage) {
    return [];
  }
  
  try {
    const storedLogs = window.localStorage.getItem(STORAGE_KEY);
    if (!storedLogs) {
      return [];
    }
    
    const serializedEntries = JSON.parse(storedLogs) as string[];
    return serializedEntries.map(deserializeLogEntry);
  } catch (error) {
    console.error('Failed to load logs from local storage:', error);
    return [];
  }
}

/**
 * In-memory storage for logs
 */
let logStorage: LogEntry[] = initializeLogStorage();

/**
 * Current logger configuration
 */
let config: LoggerConfig = { ...defaultConfig };

/**
 * Configure the logger
 */
export function configureLogger(newConfig: Partial<LoggerConfig>): void {
  config = { ...config, ...newConfig };
}

/**
 * Get all stored logs
 */
export function getLogs(): LogEntry[] {
  return [...logStorage];
}

/**
 * Clear stored logs
 */
export function clearLogs(): void {
  logStorage = [];
  
  // Clear from local storage if available
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

/**
 * Send telemetry to server
 */
async function sendTelemetry(entry: LogEntry): Promise<void> {
  if (!config.sendTelemetry || !config.telemetryEndpoint) {
    return;
  }
  
  // Apply filter if configured
  if (config.telemetryFilter && !config.telemetryFilter(entry)) {
    return;
  }
  
  try {
    // Manually handle throttling to avoid spamming the server
    const now = Date.now();
    const lastSent = Number(localStorage.getItem('last_telemetry_sent') || '0');
    const minInterval = 5000; // Minimum 5 seconds between telemetry sends
    
    if (now - lastSent < minInterval) {
      // Skip this telemetry, we're sending too frequently
      return;
    }
    
    // Store batch telemetry if we can't send now
    const batchKey = 'pending_telemetry';
    let pendingBatch: LogEntry[] = [];
    
    try {
      const storedBatch = localStorage.getItem(batchKey);
      if (storedBatch) {
        pendingBatch = JSON.parse(storedBatch).map((e: any) => ({
          ...e,
          timestamp: new Date(e.timestamp)
        }));
      }
    } catch (e) {
      // If parsing fails, start with empty batch
      pendingBatch = [];
    }
    
    // Add current entry to batch
    pendingBatch.push(entry);
    
    // Store updated batch
    localStorage.setItem(batchKey, JSON.stringify(pendingBatch.map(e => ({
      ...e,
      timestamp: e.timestamp.toISOString()
    }))));
    
    // Update last sent time
    localStorage.setItem('last_telemetry_sent', now.toString());
    
    // Send the telemetry data to the endpoint
    await axios.post(config.telemetryEndpoint, {
      timestamp: entry.timestamp.toISOString(),
      level: entry.level,
      message: entry.message,
      data: entry.data,
      clientInfo: {
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString(),
        sessionId: getOrCreateSessionId()
      }
    });
    
    // Clear the batch if successful
    localStorage.removeItem(batchKey);
  } catch (error) {
    // Silently fail - don't log to avoid infinite loops
    console.error('Failed to send telemetry:', error);
  }
}

/**
 * Get or create a session ID for telemetry
 */
function getOrCreateSessionId(): string {
  const storageKey = 'bms_session_id';
  
  if (typeof window === 'undefined' || !window.localStorage) {
    return `session-${Date.now()}`;
  }
  
  let sessionId = window.localStorage.getItem(storageKey);
  
  if (!sessionId) {
    sessionId = `session-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    window.localStorage.setItem(storageKey, sessionId);
  }
  
  return sessionId;
}

/**
 * Save logs to local storage
 */
function persistLogsToLocalStorage(): void {
  if (typeof window === 'undefined' || !window.localStorage) {
    return;
  }
  
  try {
    const serializedLogs = logStorage.map(serializeLogEntry);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(serializedLogs));
  } catch (error) {
    console.error('Failed to persist logs to local storage:', error);
  }
}

/**
 * Add a log entry
 */
function addLogEntry(level: LogLevel, message: string, data?: Record<string, unknown>): void {
  // Check if we should log at this level
  if (!shouldLog(level)) {
    return;
  }

  const logEntry: LogEntry = {
    timestamp: new Date(),
    level,
    message,
    data,
  };

  // Output to console if enabled
  if (config.enableConsole) {
    logToConsole(logEntry);
  }

  // Store logs if enabled
  if (config.storeLogs) {
    storeLog(logEntry);
    
    // Persist to local storage if enabled
    if (config.persistToLocalStorage) {
      persistLogsToLocalStorage();
    }
  }
  
  // Send telemetry if enabled
  if (config.sendTelemetry) {
    void sendTelemetry(logEntry);
  }
}

/**
 * Check if we should log at the given level
 */
function shouldLog(level: LogLevel): boolean {
  const levels: LogLevel[] = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR];
  const configLevelIndex = levels.indexOf(config.minLevel);
  const currentLevelIndex = levels.indexOf(level);

  return currentLevelIndex >= configLevelIndex;
}

/**
 * Log to the console
 */
function logToConsole(logEntry: LogEntry): void {
  const { level, message, data, timestamp } = logEntry;
  const timeString = timestamp.toISOString();

  switch (level) {
    case LogLevel.DEBUG:
      // eslint-disable-next-line no-console
      console.debug(`[${timeString}] 🐞 DEBUG: ${message}`, data || '');
      break;
    case LogLevel.INFO:
      // eslint-disable-next-line no-console
      console.info(`[${timeString}] ℹ️ INFO: ${message}`, data || '');
      break;
    case LogLevel.WARN:
      // eslint-disable-next-line no-console
      console.warn(`[${timeString}] ⚠️ WARNING: ${message}`, data || '');
      break;
    case LogLevel.ERROR:
      // eslint-disable-next-line no-console
      console.error(`[${timeString}] 🔴 ERROR: ${message}`, data || '');
      break;
    default:
      // eslint-disable-next-line no-console
      console.log(`[${timeString}] ${level}: ${message}`, data || '');
  }
}

/**
 * Store log in memory
 */
function storeLog(logEntry: LogEntry): void {
  logStorage.push(logEntry);

  // Trim log size if needed
  if (logStorage.length > config.maxLogSize) {
    logStorage = logStorage.slice(-config.maxLogSize);
  }
}

/**
 * Logger object with methods for each log level
 */
export const logger = {
  debug: (message: string, data?: Record<string, unknown>): void => {
    addLogEntry(LogLevel.DEBUG, message, data);
  },
  info: (message: string, data?: Record<string, unknown>): void => {
    addLogEntry(LogLevel.INFO, message, data);
  },
  warn: (message: string, data?: Record<string, unknown>): void => {
    addLogEntry(LogLevel.WARN, message, data);
  },
  error: (message: string, data?: Record<string, unknown>): void => {
    addLogEntry(LogLevel.ERROR, message, data);
  },
};

export default logger; 