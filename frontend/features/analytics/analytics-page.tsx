"use client";

import { useEffect, useState } from "react";
import { BarChart3, Mail, Target, TrendingUp, Users } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api-client";
import { LEAD_STATUS_LABELS } from "@/lib/constants";
import { useAuth } from "@/lib/auth-context";
import { formatNumber, formatPercent } from "@/lib/utils";
import { analyticsService } from "@/services/analytics.service";
import type { AnalyticsOverview } from "@/types/analytics";

export function AnalyticsPageContent() {
  const { token } = useAuth();
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!token) return;
      setIsLoading(true);
      try {
        const overview = await analyticsService.getOverview(token);
        setData(overview);
      } catch (error) {
        toast.error(error instanceof ApiClientError ? error.message : "Failed to load analytics");
      } finally {
        setIsLoading(false);
      }
    }
    void load();
  }, [token]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <PageHeader title="Analytics" description="Performance metrics and pipeline insights">
        <p className="text-muted-foreground">Unable to load analytics data.</p>
      </PageHeader>
    );
  }

  const statusEntries = Object.entries(data.leads_by_status).filter(([, count]) => count > 0);

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Performance metrics and pipeline insights" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard icon={<Users className="h-4 w-4" />} title="Total leads" value={formatNumber(data.total_leads)} />
        <MetricCard icon={<Target className="h-4 w-4" />} title="Campaigns" value={formatNumber(data.total_campaigns)} />
        <MetricCard icon={<Mail className="h-4 w-4" />} title="Sent messages" value={formatNumber(data.sent_messages)} />
        <MetricCard
          icon={<TrendingUp className="h-4 w-4" />}
          title="Reply rate"
          value={formatPercent(data.reply_rate)}
          sub={`Conversion ${formatPercent(data.conversion_rate)}`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Pipeline breakdown
            </CardTitle>
            <CardDescription>Leads by status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {statusEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No lead data yet.</p>
            ) : (
              statusEntries.map(([status, count]) => {
                const pct = data.total_leads ? Math.round((count / data.total_leads) * 100) : 0;
                return (
                  <div key={status} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <Badge variant="secondary">{LEAD_STATUS_LABELS[status as keyof typeof LEAD_STATUS_LABELS] ?? status}</Badge>
                      <span>
                        {formatNumber(count)} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Conversion funnel</CardTitle>
            <CardDescription>Outreach performance summary</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FunnelRow label="Total pipeline" value={formatNumber(data.total_leads)} />
            <FunnelRow label="Outreach sent" value={formatNumber(data.sent_messages)} />
            <FunnelRow label="Reply rate" value={formatPercent(data.reply_rate)} />
            <FunnelRow label="Conversion rate" value={formatPercent(data.conversion_rate)} highlight />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  title,
  value,
  sub,
}: {
  icon: React.ReactNode;
  title: string;
  value: string;
  sub?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {sub ? <p className="text-xs text-muted-foreground">{sub}</p> : null}
      </CardContent>
    </Card>
  );
}

function FunnelRow({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={highlight ? "text-lg font-semibold text-primary" : "font-medium"}>{value}</span>
    </div>
  );
}
