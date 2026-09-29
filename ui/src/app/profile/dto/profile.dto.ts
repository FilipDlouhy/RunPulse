export type RaceDistance = 5000 | 10000 | 21097;

export const RACE_DISTANCES: { value: RaceDistance; label: string }[] = [
  { value: 5000, label: '5 km' },
  { value: 10000, label: '10 km' },
  { value: 21097, label: 'Half marathon' },
];

export interface Profile {
  weight_kg: number | null;
  birth_date: string | null;
  hr_rest: number | null;
  hr_max: number | null;
  goal_distance: RaceDistance | null;
  goal_time_s: number | null;
}
