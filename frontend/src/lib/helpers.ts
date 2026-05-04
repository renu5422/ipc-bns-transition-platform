// Utility helper functions
export const formatDate = (date: Date): string => date.toISOString().split('T')[0];

export const truncate = (text: string, length: number): string =>
  text.length > length ? `${text.slice(0, length)}...` : text;
