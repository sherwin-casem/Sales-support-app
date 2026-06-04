import { apiRequest } from "@/lib/api-client";
import type { PaginatedResponse } from "@/types/api";
import type { UserRole } from "@/types/auth";

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export const usersService = {
  list(token: string, page = 1) {
    return apiRequest<PaginatedResponse<AdminUser>>(`/users?page=${page}`, { token });
  },

  update(token: string, userId: string, payload: { role?: UserRole; is_active?: boolean }) {
    return apiRequest<AdminUser>(`/users/${userId}`, {
      method: "PATCH",
      token,
      body: JSON.stringify(payload),
    });
  },

  deactivate(token: string, userId: string) {
    return apiRequest<void>(`/users/${userId}`, { method: "DELETE", token });
  },
};
