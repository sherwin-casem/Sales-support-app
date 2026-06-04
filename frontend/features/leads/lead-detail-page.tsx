"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Plus, ShieldCheck, Sparkles, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { LeadStatusBadge } from "@/components/shared/lead-status-badge";
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
import { leadsService } from "@/services/leads.service";
import { enrichmentService } from "@/services/enrichment.service";
import type { DecisionMakerInput, LeadDetail } from "@/types/leads";

export function LeadDetailPageContent() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { token } = useAuth();
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEnriching, setIsEnriching] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [dmDialogOpen, setDmDialogOpen] = useState(false);
  const [dmForm, setDmForm] = useState({ name: "", role: "", email: "", linkedin: "" });

  const loadLead = useCallback(async () => {
    if (!token || !params.id) return;
    setIsLoading(true);
    try {
      const data = await leadsService.get(token, params.id);
      setLead(data);
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Lead not found");
      router.push("/leads");
    } finally {
      setIsLoading(false);
    }
  }, [token, params.id, router]);

  useEffect(() => {
    void loadLead();
  }, [loadLead]);

  async function handleAddDecisionMaker(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !lead) return;
    const payload: DecisionMakerInput = {
      name: dmForm.name.trim(),
      role: dmForm.role.trim() || null,
      email: dmForm.email.trim() || null,
      linkedin: dmForm.linkedin.trim() || null,
    };
    try {
      await leadsService.addDecisionMaker(token, lead.id, payload);
      toast.success("Decision maker added");
      setDmDialogOpen(false);
      setDmForm({ name: "", role: "", email: "", linkedin: "" });
      await loadLead();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to add decision maker");
    }
  }

  async function handleEnrich() {
    if (!token || !lead) return;
    setIsEnriching(true);
    try {
      const job = await enrichmentService.enrichLead(token, lead.id);
      toast.success("Enrichment started");
      setTimeout(async () => {
        try {
          const status = await enrichmentService.getJobStatus(token, job.task_id);
          if (status.status === "SUCCESS") {
            toast.success("Lead enriched");
            await loadLead();
          } else if (status.status === "FAILURE") {
            toast.error("Enrichment failed");
          }
        } catch {
          await loadLead();
        }
      }, 3000);
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Enrichment failed");
    } finally {
      setIsEnriching(false);
    }
  }

  async function handleVerify() {
    if (!token || !lead) return;
    setIsVerifying(true);
    try {
      const updated = await leadsService.verify(token, lead.id);
      setLead({ ...lead, ...updated });
      toast.success("Contact verification updated");
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Verification failed");
    } finally {
      setIsVerifying(false);
    }
  }

  async function handleRemoveDecisionMaker(dmId: string) {
    if (!token || !lead) return;
    try {
      await leadsService.removeDecisionMaker(token, lead.id, dmId);
      toast.success("Decision maker removed");
      await loadLead();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to remove");
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (!lead) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/leads">
            <ArrowLeft className="h-4 w-4" />
            Back to leads
          </Link>
        </Button>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-2xl font-bold">{lead.company_name}</h2>
            <LeadStatusBadge status={lead.status} />
          </div>
          {lead.website ? (
            <a
              href={lead.website.startsWith("http") ? lead.website : `https://${lead.website}`}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-primary hover:underline"
            >
              {lead.website}
            </a>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          {lead.website ? (
            <Button size="sm" variant="outline" disabled={isEnriching} onClick={() => void handleEnrich()}>
              <Sparkles className="mr-1 h-4 w-4" />
              {isEnriching ? "Enriching…" : "Enrich"}
            </Button>
          ) : null}
          <Button size="sm" variant="outline" disabled={isVerifying} onClick={() => void handleVerify()}>
            <ShieldCheck className="mr-1 h-4 w-4" />
            {isVerifying ? "Verifying…" : "Verify contacts"}
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Company details</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm">
            <DetailRow label="Email" value={lead.email} />
            <DetailRow label="Phone" value={lead.phone} />
            <DetailRow label="Email verified" value={lead.email_verification_status} />
            <DetailRow label="Phone verified" value={lead.phone_verification_status} />
            <DetailRow label="Intent score" value={lead.intent_score?.toString()} />
            <DetailRow label="Source" value={lead.source} />
            <DetailRow label="Industry" value={lead.industry} />
            <DetailRow label="Country" value={lead.country} />
            <DetailRow label="Employees" value={lead.employee_count?.toString()} />
            <DetailRow label="Revenue" value={lead.revenue} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Decision makers</CardTitle>
              <CardDescription>Contacts identified at this company</CardDescription>
            </div>
            <Button size="sm" onClick={() => setDmDialogOpen(true)}>
              <Plus className="h-4 w-4" />
              Add
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {lead.decision_makers.length === 0 ? (
              <p className="text-sm text-muted-foreground">No decision makers yet.</p>
            ) : (
              lead.decision_makers.map((dm) => (
                <div key={dm.id} className="flex items-start justify-between rounded-lg border p-3">
                  <div>
                    <p className="font-medium">{dm.name}</p>
                    {dm.role ? <p className="text-sm text-muted-foreground">{dm.role}</p> : null}
                    {dm.email ? <p className="text-sm">{dm.email}</p> : null}
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => void handleRemoveDecisionMaker(dm.id)}>
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={dmDialogOpen} onOpenChange={setDmDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add decision maker</DialogTitle>
            <DialogDescription>Record a key contact at {lead.company_name}.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddDecisionMaker} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="dm_name">Name *</Label>
              <Input
                id="dm_name"
                required
                value={dmForm.name}
                onChange={(e) => setDmForm({ ...dmForm, name: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dm_role">Role</Label>
              <Input
                id="dm_role"
                value={dmForm.role}
                onChange={(e) => setDmForm({ ...dmForm, role: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dm_email">Email</Label>
              <Input
                id="dm_email"
                type="email"
                value={dmForm.email}
                onChange={(e) => setDmForm({ ...dmForm, email: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="dm_linkedin">LinkedIn</Label>
              <Input
                id="dm_linkedin"
                value={dmForm.linkedin}
                onChange={(e) => setDmForm({ ...dmForm, linkedin: e.target.value })}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setDmDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit">Add</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string | null | undefined }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium">{value ?? "—"}</span>
    </div>
  );
}
