export type AIMessageRole = "user" | "assistant";

export interface AIChatMessage {
  id: string | number;
  user_id?: string | number;
  role: AIMessageRole;
  content: string;
  created_at: string;
}

export interface AIChatRequest {
  question: string;
}

export interface AIChatResponse {
  answer: string;
  message?: AIChatMessage;
}

export interface ChatHistoryResponse {
  items: AIChatMessage[];
}

export interface LocalityRecommendationRequest {
  city: string;
  budget: number;
  occupation: string;
  transport: string;
}

export interface LocalityRecommendation {
  id: string | number;
  locality: string;
  city: string;
  match_score?: number;
  average_rent: number;
  safety_score: number;
  transport_score?: number;
  affordability_score?: number;
  commute_minutes?: number;
  commute_summary?: string;
  nearest_metro?: string;
  nearby_metro?: string;
  distance_to_metro_km?: number;
  reasons?: string[];
  nearby_essentials?: string[];
  pros?: string[];
  cons?: string[];
}

export interface LocalityRecommendationResponse {
  summary?: string;
  recommendations: LocalityRecommendation[];
}

export type ScamRiskLevel = "Low" | "Medium" | "High";

export interface ScamCheckRequest {
  content: string;
}

export interface ScamCheckResponse {
  risk_level: ScamRiskLevel;
  risk_score: number;
  summary: string;
  red_flags: string[];
  positive_signals: string[];
  recommendations: string[];
  disclaimer: string;
}

export interface BudgetAdviceRequest {
  monthly_income: number;
  monthly_budget: number;
  rent: number;
  food: number;
  transport: number;
  utilities: number;
  other_expenses: number;
  savings: number;
}

export interface BudgetExpenseBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

export interface BudgetAdviceResponse {
  advice?: string;
  total_expenses?: number;
  remaining_amount?: number;
  savings_rate?: number;
  spending_alerts?: string[];
  savings_suggestions?: string[];
  status?: "Safe" | "Manageable" | "Tight" | "Risky";
  summary?: string;
  monthly_income?: number;
  recommended_housing_budget?: number;
  current_housing_budget?: number;
  estimated_total_expenses?: number;
  estimated_savings?: number;
  housing_percentage?: number;
  expense_breakdown?: BudgetExpenseBreakdown[];
  recommendations?: string[];
  warnings?: string[];
}

export type AISuggestionType =
  | "housing"
  | "roommate"
  | "expense"
  | "budget"
  | "locality"
  | "safety"
  | "transport"
  | "general";

export interface PersonalizedSuggestion {
  id: string | number;
  type: AISuggestionType;
  title: string;
  description: string;
  reason?: string;
  priority?: "Low" | "Medium" | "High";
  action_label?: string;
  action_url?: string;
  created_at?: string;
}

export interface PersonalizedSuggestionsResponse {
  suggestions?: PersonalizedSuggestion[];
  items?: PersonalizedSuggestion[];
}

export interface AIErrorResponse {
  detail: string;
}