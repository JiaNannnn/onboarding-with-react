/**
 * Date and time formatting utilities
 */
import { format, parseISO, isValid, differenceInSeconds, differenceInMinutes, 
  differenceInHours, differenceInDays, differenceInMonths } from 'date-fns';

/**
 * Available date formats
 */
export enum DateFormat {
  SHORT = 'MM/dd/yyyy',
  MEDIUM = 'MMM d, yyyy',
  LONG = 'MMMM d, yyyy',
  ISO = 'yyyy-MM-dd',
}

/**
 * Available time formats
 */
export enum TimeFormat {
  SHORT = 'h:mm a',
  MEDIUM = 'h:mm:ss a',
  LONG = 'h:mm:ss.SSS a',
  MILITARY = 'HH:mm:ss',
}

/**
 * Available datetime formats
 */
export enum DateTimeFormat {
  SHORT = 'MM/dd/yyyy h:mm a',
  MEDIUM = 'MMM d, yyyy h:mm:ss a',
  LONG = 'MMMM d, yyyy h:mm:ss a',
  ISO = 'yyyy-MM-dd HH:mm:ss',
}

/**
 * Format a date to a string
 * @param date Date to format
 * @param formatStr Format string or DateFormat enum
 * @returns Formatted date string or empty string if date is invalid
 */
export function formatDate(
  date: Date | string | number | null | undefined,
  formatStr: string | DateFormat = DateFormat.MEDIUM
): string {
  if (!date) return '';

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
    
    if (!isValid(dateObj)) {
      return '';
    }
    
    return format(dateObj, formatStr);
  } catch (error) {
    return '';
  }
}

/**
 * Format a time to a string
 * @param date Date to extract time from
 * @param formatStr Format string or TimeFormat enum
 * @returns Formatted time string or empty string if date is invalid
 */
export function formatTime(
  date: Date | string | number | null | undefined,
  formatStr: string | TimeFormat = TimeFormat.SHORT
): string {
  return formatDate(date, formatStr);
}

/**
 * Format a datetime to a string
 * @param date Date to format
 * @param formatStr Format string or DateTimeFormat enum
 * @returns Formatted datetime string or empty string if date is invalid
 */
export function formatDateTime(
  date: Date | string | number | null | undefined,
  formatStr: string | DateTimeFormat = DateTimeFormat.MEDIUM
): string {
  return formatDate(date, formatStr);
}

/**
 * Get a relative time string (e.g. "2 hours ago", "in 3 days")
 * @param date Date to compare to now
 * @param baseDate Optional base date to compare to (defaults to now)
 * @returns Relative time string
 */
export function getRelativeTimeString(
  date: Date | string | number | null | undefined,
  baseDate: Date | string | number = new Date()
): string {
  if (!date) return '';

  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : new Date(date);
    const baseDateObj = typeof baseDate === 'string' ? parseISO(baseDate) : new Date(baseDate);
    
    if (!isValid(dateObj) || !isValid(baseDateObj)) {
      return '';
    }
    
    const isPast = dateObj < baseDateObj;
    const suffix = isPast ? 'ago' : 'from now';
    
    const diffInSeconds = Math.abs(differenceInSeconds(dateObj, baseDateObj));
    const diffInMinutes = Math.abs(differenceInMinutes(dateObj, baseDateObj));
    const diffInHours = Math.abs(differenceInHours(dateObj, baseDateObj));
    const diffInDays = Math.abs(differenceInDays(dateObj, baseDateObj));
    const diffInMonths = Math.abs(differenceInMonths(dateObj, baseDateObj));
    
    if (diffInSeconds < 60) {
      return diffInSeconds === 1 ? `1 second ${suffix}` : `${diffInSeconds} seconds ${suffix}`;
    } else if (diffInMinutes < 60) {
      return diffInMinutes === 1 ? `1 minute ${suffix}` : `${diffInMinutes} minutes ${suffix}`;
    } else if (diffInHours < 24) {
      return diffInHours === 1 ? `1 hour ${suffix}` : `${diffInHours} hours ${suffix}`;
    } else if (diffInDays < 30) {
      return diffInDays === 1 ? `1 day ${suffix}` : `${diffInDays} days ${suffix}`;
    } else if (diffInMonths < 12) {
      return diffInMonths === 1 ? `1 month ${suffix}` : `${diffInMonths} months ${suffix}`;
    } else {
      const diffInYears = Math.floor(diffInMonths / 12);
      return diffInYears === 1 ? `1 year ${suffix}` : `${diffInYears} years ${suffix}`;
    }
  } catch (error) {
    return '';
  }
} 