/**
 * Parse API timestamps consistently.
 *
 * SQLite CURRENT_TIMESTAMP values are UTC but do not include a timezone suffix.
 * Browsers otherwise interpret them as local time, which shifts relative times by
 * eight hours in China Standard Time.
 */
export function parseApiDate(value: string | Date): Date {
  if (value instanceof Date) return value;

  const normalized = /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?$/.test(value)
    ? `${value.replace(" ", "T")}Z`
    : value;

  return new Date(normalized);
}
