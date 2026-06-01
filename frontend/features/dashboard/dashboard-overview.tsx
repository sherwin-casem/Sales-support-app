"use client";

import { Mail, MessageSquare, Target, TrendingUp, Users } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatNumber, formatPercent } from "@/lib/utils";
import type { AnalyticsOverview } from "@/types/analytics";

const STATUS_LABELS: Record<string, string> = {
  NEW: "New",
  ENRICHED: "Enriched",
  CONTACTED: "Contacted",
  REPLIED: "Replied",
  CONVERTED: "Converted",
};

interface KpiCardProps {
  title: string;
  value: string;
  description: string;
  icon: React.ReactNode;
}

function KpiCard({ title, value, description, icon }: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Card key={index}>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
              <Skeleton className="mt-2 h-3 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-40" />
        </CardHeader>
        <CardContent className="space-y-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <Skeleton key={index} className="h-10 w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

interface DashboardOverviewProps {
  data: AnalyticsOverview | null;
  isLoading: boolean;
}

export function DashboardOverview({ data, isLoading }: DashboardOverviewProps) {
  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Unable to load dashboard</CardTitle>
          <CardDescription>Check your connection and try refreshing the page.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const statusEntries = Object.entries(data.leads_by_status).filter(([, count]) => count > 0);

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          title="Total Leads"
          value={formatNumber(data.total_leads)}
          description="All leads in your pipeline"
          icon={<Users className="h-4 w-4" />}
        />
        <KpiCard
          title="Campaigns"
          value={formatNumber(data.total_campaigns)}
          description="Active and completed campaigns"
          icon={<Target className="h-4 w-4" />}
        />
        <KpiCard
          title="Sent Messages"
          value={formatNumber(data.sent_messages)}
          description="Outreach messages delivered"
          icon={<Mail className="h-4 w-4" />}
        />
        <KpiCard
          title="Reply Rate"
          value={formatPercent(data.reply_rate)}
          description={`Conversion: ${formatPercent(data.conversion_rate)}`}
          icon={<TrendingUp className="h-4 w-4" />}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Lead Pipeline</CardTitle>
            <CardDescription>Leads grouped by status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {statusEntries.length === 0 ? (
              <p className="text-sm text-muted-foreground">No leads yet. Import or create your first lead.</p>
            ) : (
              statusEntries.map(([status, count]) => {
                const percentage = data.total_leads ? Math.round((count / data.total_leads) * 100) : 0;
                return (
                  <div key={status} className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">{STATUS_LABELS[status] ?? status}</Badge>
                        <span className="text-muted-foreground">{formatNumber(count)} leads</span>
                      </div>
                      <span className="font-medium">{percentage}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${percentage}%` }} />
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Common workflows to get started</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <ActionItem
              title="Import leads"
              description="Upload a CSV to populate your pipeline"
              href="/leads"
            />
            <ActionItem
              title="Create campaign"
              description="Set up outreach for enriched leads"
              href="/campaigns"
            />
            <ActionItem
              title="View analytics"
              description="Track reply and conversion performance"
              href="/analytics"
            />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Outreach Snapshot
          </CardTitle>
          <CardDescription>High-level performance indicators for your team</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <Metric label="Contacted + Replied" value={formatNumber(data.sent_messages)} />
          <Metric label="Reply Rate" value={formatPercent(data.reply_rate)} />
          <Metric label="Conversion Rate" value={formatPercent(data.conversion_rate)} />
        </CardContent>
      </Card>
    </div>
  );
}

function ActionItem({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <a
      href={href}
      className="block rounded-lg border p-4 transition-colors hover:bg-accent"
    >
      <p className="font-medium">{title}</p>
      <p className="text-sm text-muted-foreground">{description}</p>
    </a>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </div>
  );
}
