// Form and input validation helpers
export const validateRequired = (value: string): boolean => value.trim().length > 0;

export const validateEmail = (email: string): boolean =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
