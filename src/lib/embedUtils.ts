// Text chunking utilities for embedding
export const chunkText = (text: string, maxChunkSize: number = 1000, overlap: number = 200): string[] => {
  const chunks: string[] = [];
  let start = 0;

  while (start < text.length) {
    const end = Math.min(start + maxChunkSize, text.length);
    let chunk = text.slice(start, end);

    // Try to break at sentence boundaries
    if (end < text.length) {
      const lastPeriod = chunk.lastIndexOf('.');
      const lastNewline = chunk.lastIndexOf('\n');
      const breakPoint = Math.max(lastPeriod, lastNewline);
      
      if (breakPoint > start + maxChunkSize * 0.7) {
        chunk = chunk.slice(0, breakPoint + 1);
        start = start + breakPoint + 1;
      } else {
        start = end - overlap;
      }
    } else {
      start = end;
    }

    if (chunk.trim()) {
      chunks.push(chunk.trim());
    }
  }

  return chunks;
};

// Clean text for embedding
export const cleanText = (text: string): string => {
  return text
    .replace(/\s+/g, ' ') // Replace multiple whitespace with single space
    .replace(/[^\w\s.,!?-]/g, '') // Remove special characters except basic punctuation
    .trim();
};

// Extract metadata from text
export const extractMetadata = (text: string) => {
  const metadata: Record<string, any> = {};
  
  // Extract dates
  const dateRegex = /\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/g;
  const dates = text.match(dateRegex);
  if (dates) {
    metadata.dates = dates;
  }
  
  // Extract email addresses
  const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
  const emails = text.match(emailRegex);
  if (emails) {
    metadata.emails = emails;
  }
  
  // Extract phone numbers
  const phoneRegex = /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g;
  const phones = text.match(phoneRegex);
  if (phones) {
    metadata.phones = phones;
  }
  
  return metadata;
};

// Calculate text similarity (simple cosine similarity)
export const calculateSimilarity = (text1: string, text2: string): number => {
  const words1 = new Set(text1.toLowerCase().split(/\s+/));
  const words2 = new Set(text2.toLowerCase().split(/\s+/));
  
  const intersection = new Set([...words1].filter(x => words2.has(x)));
  const union = new Set([...words1, ...words2]);
  
  return intersection.size / union.size;
}; 