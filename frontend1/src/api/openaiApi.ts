/**
 * OpenAI API client for AI operations.
 */

import { request } from './apiClient';
import { ApiResponse, OpenAIMessage, OpenAIRequest, OpenAIResponse } from '../types';

/**
 * Test OpenAI API configuration
 */
export const testOpenAI = async (): Promise<ApiResponse<any>> => {
  return request<ApiResponse<any>>({
    method: 'GET',
    url: '/api/v1/openai/test',
  });
};

/**
 * Complete a prompt using OpenAI
 */
export const completePrompt = async (
  messages: OpenAIMessage[],
  model?: string,
  temperature?: number,
  max_tokens?: number,
  response_format?: { type: string }
): Promise<OpenAIResponse> => {
  const requestData: OpenAIRequest = {
    messages,
  };

  if (model) requestData.model = model;
  if (temperature !== undefined) requestData.temperature = temperature;
  if (max_tokens) requestData.max_tokens = max_tokens;
  if (response_format) requestData.response_format = response_format;

  return request<OpenAIResponse>({
    method: 'POST',
    url: '/api/v1/openai/complete',
    data: requestData,
  });
};
