/**
 * Validation utilities using Zod for runtime validation
 */
import { z } from 'zod';
import { ValidationResult } from '../types/commonTypes';

/**
 * Validate data against a Zod schema
 * @param schema Zod schema to validate against
 * @param data Data to validate
 * @returns ValidationResult with validity status and any errors
 */
export function validateWithSchema<T>(schema: z.ZodType<T>, data: unknown): ValidationResult {
  const result = schema.safeParse(data);

  if (result.success) {
    return {
      valid: true,
      errors: [],
    };
  }

  const errors = result.error.issues.map((issue) => 
    `${issue.path.join('.')}: ${issue.message}`
  );

  return {
    valid: false,
    errors,
  };
}

/**
 * Validate an email address
 * @param email Email address to validate
 * @returns ValidationResult with validity status and any errors
 */
export function validateEmail(email: string): ValidationResult {
  const emailSchema = z.string().email('Invalid email address');
  return validateWithSchema(emailSchema, email);
}

/**
 * Validate a URL
 * @param url URL to validate
 * @returns ValidationResult with validity status and any errors
 */
export function validateUrl(url: string): ValidationResult {
  const urlSchema = z.string().url('Invalid URL');
  return validateWithSchema(urlSchema, url);
}

/**
 * Validate a required string
 * @param value String to validate
 * @param minLength Minimum length (default: 1)
 * @param maxLength Maximum length (default: none)
 * @returns ValidationResult with validity status and any errors
 */
export function validateRequiredString(
  value: string,
  minLength = 1,
  maxLength?: number
): ValidationResult {
  let schema = z.string().min(minLength, `Must be at least ${minLength} character${minLength === 1 ? '' : 's'}`);

  if (maxLength !== undefined) {
    schema = schema.max(maxLength, `Must be at most ${maxLength} character${maxLength === 1 ? '' : 's'}`);
  }

  return validateWithSchema(schema, value);
}

/**
 * Validate a number within a range
 * @param value Number to validate
 * @param min Minimum value (default: none)
 * @param max Maximum value (default: none)
 * @returns ValidationResult with validity status and any errors
 */
export function validateNumber(
  value: number,
  min?: number,
  max?: number
): ValidationResult {
  let schema = z.number();

  if (min !== undefined) {
    schema = schema.min(min, `Must be at least ${min}`);
  }

  if (max !== undefined) {
    schema = schema.max(max, `Must be at most ${max}`);
  }

  return validateWithSchema(schema, value);
}

/**
 * Validate that a value is one of an allowed set of values
 * @param value Value to validate
 * @param allowedValues Array of allowed values
 * @returns ValidationResult with validity status and any errors
 */
export function validateEnum<T extends string | number>(
  value: T,
  allowedValues: T[]
): ValidationResult {
  // Use a simpler approach with a custom validation
  const isValid = allowedValues.includes(value);
  
  if (isValid) {
    return { valid: true, errors: [] };
  } else {
    const allowedList = allowedValues.map(v => String(v)).join(', ');
    return {
      valid: false,
      errors: [`Value must be one of: ${allowedList}`]
    };
  }
}

/**
 * Validate an array of items against a schema
 * @param items Array of items to validate
 * @param itemSchema Schema for each item
 * @param minItems Minimum number of items (default: none)
 * @param maxItems Maximum number of items (default: none)
 * @returns ValidationResult with validity status and any errors
 */
export function validateArray<T>(
  items: unknown[],
  itemSchema: z.ZodType<T>,
  minItems?: number,
  maxItems?: number
): ValidationResult {
  let schema = z.array(itemSchema);

  if (minItems !== undefined) {
    schema = schema.min(minItems, `Must have at least ${minItems} item${minItems === 1 ? '' : 's'}`);
  }

  if (maxItems !== undefined) {
    schema = schema.max(maxItems, `Must have at most ${maxItems} item${maxItems === 1 ? '' : 's'}`);
  }

  return validateWithSchema(schema, items);
} 