const ONE_OR_TWO_DIGITS = /^\d{1,2}$/;
const TWO_DIGITS = /^\d{2}$/;

export function formatDuration(totalSeconds: number): string {
  const rounded = Math.round(totalSeconds);
  const hours = Math.floor(rounded / 3600);
  const minutes = Math.floor((rounded % 3600) / 60);
  const seconds = rounded % 60;
  return hours ? `${hours}:${pad(minutes)}:${pad(seconds)}` : `${minutes}:${pad(seconds)}`;
}

export function parseDuration(value: string): number | null {
  const parts = value.trim().split(':');
  if (parts.length === 2) {
    parts.unshift('0');
  }
  if (parts.length !== 3) {
    return null;
  }
  const [hours, minutes, seconds] = parts;
  if (!ONE_OR_TWO_DIGITS.test(hours) || !ONE_OR_TWO_DIGITS.test(minutes) || !TWO_DIGITS.test(seconds)) {
    return null;
  }
  if (Number(minutes) > 59 || Number(seconds) > 59) {
    return null;
  }
  return Number(hours) * 3600 + Number(minutes) * 60 + Number(seconds);
}

export function formatPace(secondsPerKm: number): string {
  return `${formatDuration(secondsPerKm)} /km`;
}

export function formatDistance(meters: number): string {
  if (meters < 1000) {
    return `${Math.round(meters)} m`;
  }
  const km = (meters / 1000).toFixed(1);
  return `${km} km`;
}

export function plural(count: number, one: string, many: string): string {
  if (count === 1) {
    return one;
  }
  return many;
}

function pad(value: number): string {
  return String(value).padStart(2, '0');
}
