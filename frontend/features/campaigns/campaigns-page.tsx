"use client";

import { Calendar, Mail, Megaphone, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const upcomingFeatures = [
  {
    icon: Megaphone,
    title: "Campaign builder",
    description: "Create email campaigns and attach leads from your pipeline.",
  },
  {
    icon: Mail,
    title: "Email sending",
    description: "Schedule and track outbound messages with delivery status.",
  },
  {
    icon: Sparkles,
    title: "AI message drafts",
    description: "Generate personalized outreach copy per lead and channel.",
  },
  {
    icon: Calendar,
    title: "Scheduling",
    description: "Plan send times and automate follow-up sequences.",
  },
];

export function CampaignsPageContent() {
  return (
    <div className="space-y-6">
      <PageHeader title="Campaigns" description="Create and track outreach campaigns">
        <Badge variant="secondary">Coming in Phase 4</Badge>
      </PageHeader>

      <Card className="border-dashed">
        <CardHeader>
          <CardTitle>Campaign module in development</CardTitle>
          <CardDescription>
            The backend campaign API is not yet available. This page previews the upcoming workflow.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2">
            {upcomingFeatures.map(({ icon: Icon, title, description }) => (
              <div key={title} className="rounded-lg border bg-muted/30 p-4">
                <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
                <p className="font-medium">{title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{description}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
