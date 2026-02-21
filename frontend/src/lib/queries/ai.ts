/**
 * React Query hooks for AI-powered configuration assistance
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../api-client';
import { queryKeys } from './queryKeys';

// Types
export interface OnboardingSuggestionRequest {
  industry: string;
  region?: string;
  currency?: string;
  custom_context?: string;
}

export interface TeamMemberSuggestion {
  name: string;
  role: string;
  salary_monthly_brute: number;
  currency: string;
  billable_hours_per_week: number;
  is_active?: boolean;
}

export interface ServiceSuggestion {
  name: string;
  description?: string;
  default_margin_target: number;
  pricing_type: 'hourly' | 'fixed' | 'recurring' | 'project_value';
  is_active?: boolean;
}

export interface FixedCostSuggestion {
  name: string;
  amount_monthly: number;
  currency: string;
  category: string;
  description?: string;
}

export interface OnboardingSuggestionResponse {
  suggested_roles: TeamMemberSuggestion[];
  suggested_services: ServiceSuggestion[];
  suggested_fixed_costs: FixedCostSuggestion[];
  confidence_scores: {
    roles?: number;
    services?: number;
    costs?: number;
  };
  reasoning?: string;
}

export interface NaturalLanguageCommandRequest {
  command: string;
  context?: Record<string, unknown>;
}

export interface NaturalLanguageCommandResponse {
  action_type: string;
  action_data: Record<string, unknown>;
  confidence: number;
  requires_confirmation: boolean;
  reasoning?: string;
}

/**
 * Hook to get AI-powered onboarding suggestions
 */
export function useAISuggestions() {
  return useMutation({
    mutationFn: async (request: OnboardingSuggestionRequest): Promise<OnboardingSuggestionResponse> => {
      const response = await apiRequest<OnboardingSuggestionResponse>('/ai/suggest-config', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data!;
    },
    onError: (error) => {
      console.error('Error getting AI suggestions:', error);
    },
  });
}

/**
 * Hook to check AI service status
 */
export function useAIStatus() {
  return useQuery({
    queryKey: queryKeys.ai.status(),
    queryFn: async () => {
      const response = await apiRequest<{ available: boolean; message: string }>('/ai/status', {
        method: 'GET',
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data!;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to process natural language commands into structured actions.
 */
export function useProcessCommand() {
  return useMutation({
    mutationFn: async (request: NaturalLanguageCommandRequest): Promise<NaturalLanguageCommandResponse> => {
      const response = await apiRequest<NaturalLanguageCommandResponse>('/ai/process-command', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data!;
    },
    onError: (error) => {
      console.error('Error processing natural language command:', error);
    },
  });
}

// Types for document parsing
export interface DocumentParseRequest {
  text: string;
  document_type?: 'payroll' | 'expenses' | 'mixed';
}

export interface ParsedTeamMember {
  name: string;
  role: string;
  salary_monthly_brute: string; // Decimal as string from API
  currency: string;
  billable_hours_per_week: number;
  is_active?: boolean;
}

export interface ParsedFixedCost {
  name: string;
  amount_monthly: string; // Decimal as string from API
  currency: string;
  category: string;
  description?: string;
}

export interface ParsedSubscription {
  name: string;
  amount_monthly: number;
  currency: string;
}

export interface DocumentParseResponse {
  team_members: ParsedTeamMember[];
  fixed_costs: ParsedFixedCost[];
  subscriptions: ParsedSubscription[];
  confidence_scores: {
    team_members?: number;
    fixed_costs?: number;
    subscriptions?: number;
  };
  warnings: string[];
}

/**
 * Hook to parse unstructured document data
 */
export function useParseDocument() {
  return useMutation({
    mutationFn: async (request: DocumentParseRequest): Promise<DocumentParseResponse> => {
      const response = await apiRequest<DocumentParseResponse>('/ai/parse-document', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data!;
    },
    onError: (error) => {
      console.error('Error parsing document:', error);
    },
  });
}

export interface NaturalLanguageCommandRequest {
  command: string;
  context?: Record<string, unknown>;
}

export interface NaturalLanguageCommandResponse {
  action_type: string;
  action_data: Record<string, unknown>;
  confidence: number;
  requires_confirmation: boolean;
  reasoning?: string;
}

/**
 * Hook to process natural language commands and return structured actions.
 */
export function useProcessCommand() {
  return useMutation({
    mutationFn: async (
      request: NaturalLanguageCommandRequest
    ): Promise<NaturalLanguageCommandResponse> => {
      const response = await apiRequest<NaturalLanguageCommandResponse>('/ai/process-command', {
        method: 'POST',
        body: JSON.stringify(request),
      });

      if (response.error) {
        throw new Error(response.error);
      }

      return response.data!;
    },
    onError: (error) => {
      console.error('Error processing natural language command:', error);
    },
  });
}




