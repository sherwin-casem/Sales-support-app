"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { DashboardOverview } from "@/features/dashboard/dashboard-overview";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { analyticsService } from "@/services/analytics.service";
import type { AnalyticsOverview } from "@/types/analytics";

export default function DashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadOverview() {
      if (!token) return;
      setIsLoading(true);
      try {
        const overview = await analyticsService.getOverview(token);
        setData(overview);
      } catch (error) {
        const message =
          error instanceof ApiClientError ? error.message : "Failed to load dashboard data";
        toast.error(message);
        setData(null);
      } finally {
        setIsLoading(false);
      }
    }

    void loadOverview();
  }, [token]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Overview of your sales pipeline and outreach performance</p>
      </div>
      <DashboardOverview data={data} isLoading={isLoading} />
    </div>
  );
}
