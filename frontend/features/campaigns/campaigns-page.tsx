"use client";

import { useCallback, useEffect, useState } from "react";
import { Copy, Mail, Plus, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { campaignsService } from "@/services/campaigns.service";
import type { Campaign, CampaignAnalytics, GeneratedMessage } from "@/types/campaigns";

export function CampaignsPageContent() {
  const { token, user } = useAuth();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null);
  const [messages, setMessages] = useState<GeneratedMessage[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState("");
  const [leadIdForAi, setLeadIdForAi] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await campaignsService.list(token);
      setCampaigns(data);
      if (data.length && !selectedId) setSelectedId(data[0].id);
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to load campaigns");
    } finally {
      setIsLoading(false);
    }
  }, [token, selectedId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    async function loadDetail() {
      if (!token || !selectedId) return;
      try {
        const [stats, msgs] = await Promise.all([
          campaignsService.getCampaignAnalytics(token, selectedId),
          campaignsService.listMessages(token, { campaign_id: selectedId }),
        ]);
        setAnalytics(stats);
        setMessages(msgs);
      } catch {
        setAnalytics(null);
        setMessages([]);
      }
    }
    void loadDetail();
  }, [token, selectedId, campaigns]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      await campaignsService.create(token, { name: name.trim(), channel: "EMAIL" });
      toast.success("Campaign created");
      setDialogOpen(false);
      setName("");
      await load();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to create campaign");
    }
  }

  async function handleSend(campaignId: string) {
    if (!token) return;
    try {
      const result = await campaignsService.sendNow(token, campaignId);
      toast.success(`Enqueued ${result.enqueued} emails (dry-run if SMTP not configured)`);
      await load();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Send failed");
    }
  }

  async function handleGenerateAi(campaignId: string) {
    if (!token || !leadIdForAi.trim()) {
      toast.error("Enter a lead ID for AI message generation");
      return;
    }
    try {
      const msg = await campaignsService.generateMessage(token, {
        lead_id: leadIdForAi.trim(),
        channel: "EMAIL",
        campaign_id: campaignId,
      });
      setMessages((prev) => [msg, ...prev]);
      toast.success("Message generated");
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Generation failed");
    }
  }

  function copyMessage(body: string) {
    void navigator.clipboard.writeText(body);
    toast.success("Copied to clipboard");
  }

  const selected = campaigns.find((c) => c.id === selectedId);
  const isManager = user?.role === "ADMIN" || user?.role === "MANAGER";

  return (
    <div className="space-y-6">
      <PageHeader title="Campaigns" description="Email outreach with AI-generated copy">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New campaign
        </Button>
      </PageHeader>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : campaigns.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No campaigns yet</CardTitle>
            <CardDescription>Create a campaign, add leads from the Leads page, then send email outreach.</CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-2">
            {campaigns.map((c) => (
              <Card
                key={c.id}
                className={`cursor-pointer ${selectedId === c.id ? "border-primary" : ""}`}
                onClick={() => setSelectedId(c.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex justify-between">
                    <CardTitle className="text-base">{c.name}</CardTitle>
                    <Badge>{c.status}</Badge>
                  </div>
                  <CardDescription>{c.lead_count} leads · {c.channel}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>

          {selected && analytics ? (
            <div className="space-y-4 lg:col-span-2">
              <Card>
                <CardHeader className="flex flex-row justify-between">
                  <div>
                    <CardTitle>{selected.name}</CardTitle>
                    <CardDescription>Performance metrics</CardDescription>
                  </div>
                  {isManager ? (
                    <Button size="sm" onClick={() => void handleSend(selected.id)}>
                      <Send className="mr-1 h-4 w-4" />
                      Send emails
                    </Button>
                  ) : null}
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4 sm:grid-cols-4 text-center">
                  <Stat label="Total" value={analytics.total_leads} />
                  <Stat label="Sent" value={analytics.sent} />
                  <Stat label="Replied" value={analytics.replied} />
                  <Stat label="Reply rate" value={`${(analytics.reply_rate * 100).toFixed(1)}%`} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    AI messages
                  </CardTitle>
                  <CardDescription>Generate personalized copy; LinkedIn/WhatsApp: copy and paste manually.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input placeholder="Lead UUID for AI generation" value={leadIdForAi} onChange={(e) => setLeadIdForAi(e.target.value)} />
                    <Button variant="outline" onClick={() => void handleGenerateAi(selected.id)}>Generate</Button>
                  </div>
                  {messages.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No messages yet.</p>
                  ) : (
                    messages.map((msg) => (
                      <div key={msg.id} className="rounded border p-3 text-sm">
                        <div className="mb-2 flex items-center justify-between">
                          <Badge variant="outline">{msg.channel}</Badge>
                          <Button size="sm" variant="ghost" onClick={() => copyMessage(msg.body)}>
                            <Copy className="h-4 w-4" />
                          </Button>
                        </div>
                        {msg.subject ? <p className="font-medium">{msg.subject}</p> : null}
                        <p className="mt-2 whitespace-pre-wrap text-muted-foreground">{msg.body}</p>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>New campaign</DialogTitle>
            <DialogDescription>Email campaigns use your SMTP server (configure in .env).</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="cname">Name</Label>
              <Input id="cname" required value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <Button type="submit" className="w-full">
              <Mail className="mr-2 h-4 w-4" />
              Create email campaign
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
