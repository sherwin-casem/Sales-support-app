import { apiRequest } from "@/lib/api-client";
import type {
  CrawlRun,
  DiscoveryProfile,
  DiscoveryProfileInput,
  RunDiscoveryResponse,
} from "@/types/discovery";

export const discoveryService = {
  listProfiles(token: string) {
    return apiRequest<DiscoveryProfile[]>("/discovery/profiles", { token });
  },

  createProfile(token: string, payload: DiscoveryProfileInput) {
    return apiRequest<DiscoveryProfile>("/discovery/profiles", {
      method: "POST",
      token,
      body: JSON.stringify(payload),
    });
  },

  updateProfile(token: string, id: string, payload: Partial<DiscoveryProfileInput>) {
    return apiRequest<DiscoveryProfile>(`/discovery/profiles/${id}`, {
      method: "PATCH",
      token,
      body: JSON.stringify(payload),
    });
  },

  deleteProfile(token: string, id: string) {
    return apiRequest<void>(`/discovery/profiles/${id}`, { method: "DELETE", token });
  },

  listRuns(token: string, profileId: string) {
    return apiRequest<CrawlRun[]>(`/discovery/profiles/${profileId}/runs`, { token });
  },

  runNow(token: string, profileId: string) {
    return apiRequest<RunDiscoveryResponse>(`/discovery/profiles/${profileId}/run`, {
      method: "POST",
      token,
    });
  },
};
