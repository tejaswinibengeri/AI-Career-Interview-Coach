import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import api, {
  getStoredToken,
  removeStoredToken,
  setStoredToken,
  type AuthResponseData,
  type UserData,
} from "../lib/api";
import { AuthContext, type AuthContextType } from "./auth-context-def";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserData | null>(null);
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async (): Promise<UserData | null> => {
    const activeToken = getStoredToken();
    if (!activeToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return null;
    }

    try {
      const response = await api.get<UserData>("/api/v1/auth/me");
      if (response.data) {
        setUser(response.data);
        setToken(activeToken);
        return response.data;
      }
      throw new Error("Failed to load user profile");
    } catch {
      removeStoredToken();
      setUser(null);
      setToken(null);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback((authData: AuthResponseData) => {
    setStoredToken(authData.access_token);
    setToken(authData.access_token);
    setUser(authData.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post("/api/v1/auth/logout");
    } catch {
      // Ignore network errors on logout
    } finally {
      removeStoredToken();
      setToken(null);
      setUser(null);
    }
  }, []);

  const updateUser = useCallback((updatedUser: UserData) => {
    setUser(updatedUser);
  }, []);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: Boolean(user && token),
    login,
    logout,
    updateUser,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
