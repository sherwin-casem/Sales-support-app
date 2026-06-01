import { apiRequest } from "@/lib/api-client";
import type { AuthResponse, LoginRequest, SignupRequest, TokenResponse, User } from "@/types/auth";

export const authService = {
  login(payload: LoginRequest) {
    return apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  signup(payload: SignupRequest) {
    return apiRequest<AuthResponse>("/auth/signup", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  refresh() {
    return apiRequest<TokenResponse>("/auth/refresh", {
      method: "POST",
    });
  },

  logout(token: string) {
    return apiRequest<void>("/auth/logout", {
      method: "POST",
      token,
    });
  },

  me(token: string) {
    return apiRequest<User>("/auth/me", { token });
  },
};
