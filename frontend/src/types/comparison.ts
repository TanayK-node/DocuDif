export type ChangeType = 'added' | 'removed' | 'modified' | 'unchanged';
export type PriorityLevel = 'low' | 'medium' | 'high' | 'critical';

export interface RuleFlag {
  rule_id: string;
  category: string;
  description: string;
  severity: PriorityLevel;
  old_value?: string | null;
  new_value?: string | null;
}

export interface TokenDiff {
  operation: 'equal' | 'insert' | 'delete';
  text: string;
}

export interface ChangeRecord {
  change_id: string;
  change_type: ChangeType;
  old_text: string;
  new_text: string;
  old_source?: string | null;
  new_source?: string | null;
  similarity?: number | null;
  match_method: string;
  semantic_class: string;
  category: string;
  rule_flags: RuleFlag[];
  priority: PriorityLevel;
  priority_reasons: string[];
  explanation: string;
  implication: string;
  confidence: number;
  requires_human_review: boolean;
  analysis_status: string;
  diff_tokens: TokenDiff[];
  warnings: string[];
}

export interface ComparisonSummary {
  comparison_id: string;
  old_filename: string;
  new_filename: string;
  created_at: string;
  total_changes: number;
  added: number;
  removed: number;
  modified: number;
  unchanged: number;
  priority_breakdown: Record<string, number>;
  category_breakdown: Record<string, number>;
  model: string;
  embedding_model: string;
  processing_duration_seconds: number;
  langgraph_used: boolean;
}

export interface ComparisonResult {
  summary: ComparisonSummary;
  changes: ChangeRecord[];
  warnings: string[];
}

export interface RecentComparisonItem {
  comparison_id: string;
  old_filename: string;
  new_filename: string;
  created_at: string;
  total_changes: number;
  model: string;
  duration: number;
}
