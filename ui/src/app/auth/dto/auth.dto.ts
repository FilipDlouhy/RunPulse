export interface LoginRequest {
  username: string;
  password: string;
}

export type Role = 'RUNNER' | 'GYM_ADMIN';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}
