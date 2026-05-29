export type Citation = {
  title: string;
  url: string;
  snippet: string;
};

export type ChatResponse = {
  answer: string;
  citations: Citation[];
  grounded: boolean;
};

// Made with Bob
