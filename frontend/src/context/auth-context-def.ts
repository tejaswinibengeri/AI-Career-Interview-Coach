import { createContext } from "react";
import type { AuthResponseData, UserData } from "../lib/api";

export interface AuthContextType {
  user: UserData | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (authData: AuthResponseData) => void;
  logout: () => Promise<void>;
  updateUser: (user: UserData) => void;
  refreshUser: () => Promise<UserData | null>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
