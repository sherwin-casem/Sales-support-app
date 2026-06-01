import { apiRequest } from "@/lib/api-client";
import type { AnalyticsOverview } from "@/types/analytics";

export const analyticsService = {
  getOverview(token: string) {
    return apiRequest<AnalyticsOverview>("/analytics/overview", { token });
  },
};
