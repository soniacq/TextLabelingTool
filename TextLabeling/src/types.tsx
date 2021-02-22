export interface DataSample {
  id: string;
  words: Metadata;
  entities: Metadata;
  samples: TextInfo[];
}
export interface TextSample {
  id: string;
  samples: TextInfo[];
  performance_history: number[];
}
export interface RequestResult {
  updated_data: DataSample;
}

export interface Metadata {
  entity_type?: string;
  word: string;
  category: string;
  normalized_frequency: number;
  frequency: number;
  normalized_frequency_diff_pos_neg: number;
  frequency_diff_pos_neg: number;
  sample: string[];
}

export interface TextInfo {
  text: string;
  label: string;
}

export interface PerformanceHistory {
  Iterations: number;
  F1: number;
}
