/**
 * Pattern Analytics — TypeScript types matching backend API responses.
 */

/* ── Pattern Overview (from /patterns/overview/{job_type_id}) ── */

export interface TopicTrend {
  topic_id: string;
  topic_name: string;
  display_name: string;
  percentage: number;
  question_count: number;
  trend_direction: 'rising' | 'falling' | 'stable' | null;
}

export interface DueTopic {
  topic_id: string;
  topic_name: string;
  display_name: string;
  absent_papers: number;
}

export interface HighFrequencyFact {
  fact: string;
  paper_count: number;
  total_appearances: number;
}

export interface RepeatQuestionSummary {
  total_groups: number;
  total_repeated_questions: number;
}

export interface PatternOverviewResponse {
  job_type_id: string;
  job_type_name: string;
  snapshot_date: string | null;
  paper_count: number;
  confidence_score: number;
  topic_trends: TopicTrend[];
  due_topics: DueTopic[];
  high_frequency_facts: HighFrequencyFact[];
  repeat_summary: RepeatQuestionSummary;
  predicted_topic_ratios: Record<string, number> | null;
  snapshot_id: string | null;
  snapshot_created_at: string | null;
}

/* ── Year-by-Year (from /admin/pattern-analytics/year-by-year) ── */

export interface TopicMeta {
  name: string;
  display_name: string;
}

export interface YearByYearResponse {
  job_type_id: string;
  job_type_name: string;
  years: number[];
  topics: TopicMeta[];
  series: Record<string, number | string>[]; // { year: 2023, pak_studies: 12.5, ... }
}

/* ── Repeat Questions (from /admin/pattern-analytics/repeat-questions) ── */

export interface RepeatQuestion {
  id: string;
  question_text: string;
  topic_name: string;
  topic_display_name: string;
  repeat_count: number;
  similarity_group_id: string | null;
  year_appeared: number | null;
  difficulty_score: number;
  fact_extracted: string | null;
}

export interface RepeatQuestionsResponse {
  items: RepeatQuestion[];
  total: number;
  page: number;
  per_page: number;
}

/* ── Compare Job Types (from /admin/pattern-analytics/compare-job-types) ── */

export interface JobTypeMeta {
  id: string;
  name: string;
}

export interface CompareJobTypesResponse {
  job_types: JobTypeMeta[];
  topics: string[];
  series: Record<string, number | string>[]; // { topic: "Pak Studies", "PCS": 15.2, "ASI": 8.5 }
}

/* ── Prediction Accuracy (from /admin/pattern-analytics/prediction-accuracy) ── */

export interface TopicComparison {
  topic: string;
  predicted_pct: number;
  actual_pct: number;
  difference: number;
}

export interface PredictionAccuracyResponse {
  prediction_id: string;
  prediction_title: string;
  prediction_date: string;
  confidence_score: number;
  paper_count_basis: number;
  actual_paper: { id: string; year: number; title: string } | null;
  comparison: TopicComparison[];
  accuracy_score: number | null;
  total_predicted_topics: number;
  total_actual_topics: number;
}

/* ── Shared ── */

export interface JobType {
  id: string;
  name: string;
  slug: string;
  department: string | null;
  total_papers: number;
  avg_questions_per_paper: number;
  topic_ratios: Record<string, number> | null;
  is_active: boolean;
}

export interface PredictionSummary {
  id: string;
  title: string;
  prediction_date: string;
  job_type_id: string;
  job_type_name: string | null;
  confidence_score: number;
  status: string;
  is_published: boolean;
  topic_distribution: Record<string, number> | null;
}

export interface PaperSummary {
  id: string;
  title: string;
  year: number;
  job_type_id: string;
}
