import axios from 'axios';
import { ComparisonResult, ChangeRecord, RecentComparisonItem } from '../types/comparison';

const envApiUrl = (import.meta as any).env?.VITE_API_URL;
const API_BASE_URL = envApiUrl ? `${envApiUrl.replace(/\/$/, '')}/api/v1` : '/api/v1';

export const api = {
  async getHealth() {
    const res = await axios.get(`${API_BASE_URL}/health`);
    return res.data;
  },

  async compareDocuments(
    oldFile: File,
    newFile: File,
    provider: string = 'deterministic',
    threshold: number = 0.65,
    useLanggraph: boolean = true,
    geminiApiKey?: string
  ): Promise<ComparisonResult> {
    const formData = new FormData();
    formData.append('old_file', oldFile);
    formData.append('new_file', newFile);
    formData.append('provider', provider);
    formData.append('threshold', threshold.toString());
    formData.append('use_langgraph', useLanggraph ? 'true' : 'false');
    if (geminiApiKey && geminiApiKey.trim()) {
      formData.append('gemini_api_key', geminiApiKey.trim());
    }

    const res = await axios.post<ComparisonResult>(`${API_BASE_URL}/comparisons`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async getComparison(comparisonId: string): Promise<ComparisonResult> {
    const res = await axios.get<ComparisonResult>(`${API_BASE_URL}/comparisons/${comparisonId}`);
    return res.data;
  },

  async getChanges(
    comparisonId: string,
    filters?: {
      change_type?: string;
      priority?: string;
      category?: string;
      search?: string;
      include_unchanged?: boolean;
    }
  ): Promise<ChangeRecord[]> {
    const res = await axios.get<ChangeRecord[]>(`${API_BASE_URL}/comparisons/${comparisonId}/changes`, {
      params: filters,
    });
    return res.data;
  },

  async listRecentComparisons(): Promise<RecentComparisonItem[]> {
    const res = await axios.get<RecentComparisonItem[]>(`${API_BASE_URL}/comparisons`);
    return res.data;
  },

  getExportUrl(comparisonId: string, format: 'csv' | 'html'): string {
    return `${API_BASE_URL}/comparisons/${comparisonId}/export?format=${format}`;
  }
};

