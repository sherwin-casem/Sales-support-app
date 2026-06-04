"use client";

import { useCallback, useEffect, useState } from "react";
import { Play, Plus, Radar, Trash2 } from "lucide-react";
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
import { discoveryService } from "@/services/discovery.service";
import type { CrawlRun, DiscoveryProfile } from "@/types/discovery";

export function DiscoveryPageContent() {
  const { token } = useAuth();
  const [profiles, setProfiles] = useState<DiscoveryProfile[]>([]);
  const [runs, setRuns] = useState<CrawlRun[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    industries: "",
    countries: "",
    seed_urls: "",
    crawl_depth: "2",
    max_pages: "50",
  });

  const loadProfiles = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await discoveryService.listProfiles(token);
      setProfiles(data);
      if (data.length && !selectedId) setSelectedId(data[0].id);
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to load profiles");
    } finally {
      setIsLoading(false);
    }
  }, [token, selectedId]);

  useEffect(() => {
    void loadProfiles();
  }, [loadProfiles]);

  useEffect(() => {
    async function loadRuns() {
      if (!token || !selectedId) return;
      try {
        const data = await discoveryService.listRuns(token, selectedId);
        setRuns(data);
      } catch {
        setRuns([]);
      }
    }
    void loadRuns();
  }, [token, selectedId, profiles]);

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      await discoveryService.createProfile(token, {
        name: form.name.trim(),
        description: form.description.trim() || null,
        industries: form.industries.split(",").map((s) => s.trim()).filter(Boolean),
        countries: form.countries.split(",").map((s) => s.trim()).filter(Boolean),
        seed_urls: form.seed_urls.split("\n").map((s) => s.trim()).filter(Boolean),
        crawl_depth: Number(form.crawl_depth),
        max_pages: Number(form.max_pages),
      });
      toast.success("Discovery profile created");
      setDialogOpen(false);
      setForm({ name: "", description: "", industries: "", countries: "", seed_urls: "", crawl_depth: "2", max_pages: "50" });
      await loadProfiles();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to create profile");
    }
  }

  async function handleRunNow(profileId: string) {
    if (!token) return;
    try {
      const result = await discoveryService.runNow(token, profileId);
      toast.success(`Crawl started (task ${result.task_id.slice(0, 8)}…)`);
      const data = await discoveryService.listRuns(token, profileId);
      setRuns(data);
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to start crawl");
    }
  }

  async function handleDelete(profileId: string) {
    if (!token) return;
    try {
      await discoveryService.deleteProfile(token, profileId);
      toast.success("Profile deleted");
      setSelectedId(null);
      await loadProfiles();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to delete");
    }
  }

  const selected = profiles.find((p) => p.id === selectedId);

  return (
    <div className="space-y-6">
      <PageHeader title="Lead Discovery" description="Automatically find companies from seed URLs and target industries">
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New profile
        </Button>
      </PageHeader>

      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : profiles.length === 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>No discovery profiles</CardTitle>
            <CardDescription>
              Create a profile with seed URLs (trade directories, association lists) to auto-discover leads.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-2 lg:col-span-1">
            {profiles.map((profile) => (
              <Card
                key={profile.id}
                className={`cursor-pointer transition-colors ${selectedId === profile.id ? "border-primary" : ""}`}
                onClick={() => setSelectedId(profile.id)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{profile.name}</CardTitle>
                    <Badge variant={profile.is_active ? "default" : "secondary"}>
                      {profile.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </div>
                  <CardDescription>{profile.seed_urls.length} seed URLs</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>

          {selected ? (
            <div className="space-y-4 lg:col-span-2">
              <Card>
                <CardHeader className="flex flex-row items-start justify-between">
                  <div>
                    <CardTitle>{selected.name}</CardTitle>
                    <CardDescription>{selected.description || "No description"}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => void handleRunNow(selected.id)}>
                      <Play className="mr-1 h-4 w-4" />
                      Run now
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => void handleDelete(selected.id)}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p><span className="text-muted-foreground">Industries:</span> {selected.industries.join(", ") || "—"}</p>
                  <p><span className="text-muted-foreground">Countries:</span> {selected.countries.join(", ") || "—"}</p>
                  <p><span className="text-muted-foreground">Last run:</span> {selected.last_run_at ? new Date(selected.last_run_at).toLocaleString() : "Never"}</p>
                  <div>
                    <p className="text-muted-foreground mb-1">Seed URLs:</p>
                    <ul className="list-inside list-disc text-xs">
                      {selected.seed_urls.map((url) => (
                        <li key={url}>{url}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Radar className="h-5 w-5" />
                    Recent crawl runs
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {runs.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No runs yet. Click Run now to start.</p>
                  ) : (
                    runs.map((run) => (
                      <div key={run.id} className="flex items-center justify-between rounded border p-3 text-sm">
                        <div>
                          <Badge variant={run.status === "COMPLETED" ? "default" : run.status === "FAILED" ? "warning" : "secondary"}>
                            {run.status}
                          </Badge>
                          <p className="mt-1 text-muted-foreground">
                            {run.pages_crawled} pages · {run.leads_created} leads created · {run.leads_found} found
                          </p>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {new Date(run.created_at).toLocaleString()}
                        </span>
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
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>New discovery profile</DialogTitle>
            <DialogDescription>Configure seed URLs and filters for automatic lead discovery.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name *</Label>
              <Input id="name" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="industries">Industries (comma-separated)</Label>
              <Input id="industries" placeholder="manufacturing, water treatment" value={form.industries} onChange={(e) => setForm({ ...form, industries: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="countries">Countries (comma-separated)</Label>
              <Input id="countries" placeholder="US, IN" value={form.countries} onChange={(e) => setForm({ ...form, countries: e.target.value })} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="seeds">Seed URLs (one per line) *</Label>
              <textarea
                id="seeds"
                required
                rows={4}
                className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="https://example.com/directory"
                value={form.seed_urls}
                onChange={(e) => setForm({ ...form, seed_urls: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="depth">Crawl depth</Label>
                <Input id="depth" type="number" min={1} max={5} value={form.crawl_depth} onChange={(e) => setForm({ ...form, crawl_depth: e.target.value })} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max">Max pages</Label>
                <Input id="max" type="number" min={1} max={500} value={form.max_pages} onChange={(e) => setForm({ ...form, max_pages: e.target.value })} />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit">Create</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
