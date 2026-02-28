/**
 * Admin Dashboard — Types
 * ========================
 * Shared TypeScript interfaces for the admin dashboard home screen.
 */

export interface AdminStats {
  total_papers: number;
  total_questions: number;
  topics_discovered: number;
  avg_confidence_score: number;
}

export interface TimelinePaperPoint {
  id: string;
  title: string;
  paper_year: number;
  paper_month: number | null;
  total_questions: number;
  ingestion_status: string;
  job_type_name: string;
  job_type_slug: string;
  created_at: string;
}

export interface PredictionHealthItem {
  job_type_id: string;
  job_type_name: string;
  job_type_slug: string;
  paper_count: number;
  health: 'green' | 'orange' | 'blue';
  confidence_score: number;
}

export interface RecentActivityItem {
  paper_id: string;
  title: string;
  status: 'completed' | 'processing' | 'pending' | 'failed';
  job_type_name: string;
  total_questions: number;
  created_at: string;
}

export interface AdminDashboardData {
  stats: AdminStats;
  timeline: TimelinePaperPoint[];
  prediction_health: PredictionHealthItem[];
  recent_activity: RecentActivityItem[];
}
