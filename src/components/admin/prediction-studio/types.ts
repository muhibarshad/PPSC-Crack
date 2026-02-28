/**
 * Prediction Studio — Shared Types
 * ==================================
 */

export interface JobType {
  id: string;
  name: string;
  slug: string;
  department: string | null;
  total_papers: number;
  is_active: boolean;
}

export interface PredictedQuestion {
  question_number: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  correct_answer: string;
  topic_name: string;
  topic_id: string | null;
  subtopic: string | null;
  difficulty_score: number;
  fact_basis: string | null;
  source_question_id: string | null;
  is_current_affairs: boolean;
  confidence: number;
}

export type QuestionStatus = 'pending' | 'accepted' | 'rejected';

export interface ReviewableQuestion extends PredictedQuestion {
  status: QuestionStatus;
  admin_note: string;
}

export interface GenerationConfig {
  job_type_id: string;
  prediction_date: string;       // "YYYY-MM-DD"
  include_current_affairs: boolean;
  total_questions: number;
}

export type StudioPhase = 'configure' | 'generating' | 'review' | 'published';

export interface SSEStatusEvent {
  message: string;
  step?: string;
  progress?: number;
}

export interface SSEQuestionEvent extends PredictedQuestion {}

export interface SSEConfidenceEvent {
  confidence_score: number;
  paper_count_basis: number;
  pattern_consistency: number;
  explanation: string;
}

export interface SSECompleteEvent {
  prediction_id: string;
  status: string;
  total_questions_generated: number;
  current_affairs_count: number;
  confidence_score: number;
  message: string;
}
