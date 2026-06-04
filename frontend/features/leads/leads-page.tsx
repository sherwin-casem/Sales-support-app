"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Download, Plus, Search, Trash2, Upload } from "lucide-react";
import { toast } from "sonner";

import { LeadStatusBadge } from "@/components/shared/lead-status-badge";
import { PageHeader } from "@/components/shared/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LeadForm } from "@/features/leads/lead-form";
import { ApiClientError } from "@/lib/api-client";
import { LEAD_STATUSES, LEAD_STATUS_LABELS } from "@/lib/constants";
import { useAuth } from "@/lib/auth-context";
import { leadsService } from "@/services/leads.service";
import type { Lead, LeadCreateInput, LeadStatus, LeadUpdateInput } from "@/types/leads";

export function LeadsPageContent() {
  const { token, user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);

  const canDelete = user?.role === "ADMIN" || user?.role === "MANAGER";

  const loadLeads = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const result = await leadsService.list(token, {
        page,
        page_size: 10,
        search: search || undefined,
        status: statusFilter !== "all" ? (statusFilter as LeadStatus) : undefined,
      });
      setLeads(result.items);
      setTotal(result.total);
      setPages(result.pages);
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to load leads");
    } finally {
      setIsLoading(false);
    }
  }, [token, page, search, statusFilter]);

  useEffect(() => {
    void loadLeads();
  }, [loadLeads]);

  function openCreate() {
    setEditingLead(null);
    setDialogOpen(true);
  }

  function openEdit(lead: Lead) {
    setEditingLead(lead);
    setDialogOpen(true);
  }

  async function handleSave(data: LeadCreateInput | LeadUpdateInput) {
    if (!token) return;
    if (editingLead) {
      await leadsService.update(token, editingLead.id, data as LeadUpdateInput);
      toast.success("Lead updated");
    } else {
      await leadsService.create(token, data as LeadCreateInput);
      toast.success("Lead created");
    }
    setDialogOpen(false);
    await loadLeads();
  }

  async function handleDelete(lead: Lead) {
    if (!token || !canDelete) return;
    if (!window.confirm(`Delete ${lead.company_name}?`)) return;
    try {
      await leadsService.delete(token, lead.id);
      toast.success("Lead deleted");
      await loadLeads();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to delete lead");
    }
  }

  async function handleImport(file: File) {
    if (!token) return;
    try {
      const result = await leadsService.importCsv(token, file);
      toast.success(`Imported ${result.created} leads (${result.failed} failed)`);
      if (result.errors.length) {
        toast.error(result.errors.slice(0, 3).join("; "));
      }
      await loadLeads();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Import failed");
    }
  }

  async function handleExport() {
    if (!token) return;
    try {
      const blob = await leadsService.exportCsv(token, {
        search: search || undefined,
        status: statusFilter !== "all" ? (statusFilter as LeadStatus) : undefined,
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "leads.csv";
      anchor.click();
      URL.revokeObjectURL(url);
      toast.success("Export downloaded");
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Export failed");
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Leads" description="Manage and enrich your sales pipeline">
        <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
          <Upload className="h-4 w-4" />
          Import CSV
        </Button>
        <Button variant="outline" onClick={() => void handleExport()}>
          <Download className="h-4 w-4" />
          Export
        </Button>
        <Button onClick={openCreate}>
          <Plus className="h-4 w-4" />
          Add lead
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleImport(file);
            e.target.value = "";
          }}
        />
      </PageHeader>

      <Card>
        <CardContent className="pt-6">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search company, email, website..."
                className="pl-9"
                value={search}
                onChange={(e) => {
                  setPage(1);
                  setSearch(e.target.value);
                }}
              />
            </div>
            <Select
              value={statusFilter}
              onValueChange={(value) => {
                setPage(1);
                setStatusFilter(value);
              }}
            >
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {LEAD_STATUSES.map((status) => (
                  <SelectItem key={status} value={status}>
                    {LEAD_STATUS_LABELS[status]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : leads.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              No leads found. Create one or import a CSV file.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Company</TableHead>
                  <TableHead className="hidden md:table-cell">Industry</TableHead>
                  <TableHead className="hidden lg:table-cell">Country</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead) => (
                  <TableRow key={lead.id}>
                    <TableCell>
                      <Link href={`/leads/${lead.id}`} className="font-medium hover:underline">
                        {lead.company_name}
                      </Link>
                      {lead.email ? (
                        <p className="text-xs text-muted-foreground">{lead.email}</p>
                      ) : null}
                    </TableCell>
                    <TableCell className="hidden md:table-cell">{lead.industry ?? "—"}</TableCell>
                    <TableCell className="hidden lg:table-cell">{lead.country ?? "—"}</TableCell>
                    <TableCell>
                      <LeadStatusBadge status={lead.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="sm" onClick={() => openEdit(lead)}>
                          Edit
                        </Button>
                        {canDelete ? (
                          <Button variant="ghost" size="sm" onClick={() => void handleDelete(lead)}>
                            <Trash2 className="h-4 w-4 text-destructive" />
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          {pages > 1 ? (
            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                {total} lead{total !== 1 ? "s" : ""} · page {page} of {pages}
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>
                  Previous
                </Button>
                <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>
                  Next
                </Button>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>{editingLead ? "Edit lead" : "Create lead"}</DialogTitle>
            <DialogDescription>
              {editingLead ? "Update lead details in your pipeline." : "Add a new company to your pipeline."}
            </DialogDescription>
          </DialogHeader>
          <LeadForm
            initial={editingLead}
            onSubmit={handleSave}
            onCancel={() => setDialogOpen(false)}
            submitLabel={editingLead ? "Update" : "Create"}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
