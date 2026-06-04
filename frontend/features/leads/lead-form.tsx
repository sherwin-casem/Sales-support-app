"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { LEAD_STATUSES, LEAD_STATUS_LABELS } from "@/lib/constants";
import type { Lead, LeadCreateInput, LeadStatus, LeadUpdateInput } from "@/types/leads";

interface LeadFormProps {
  initial?: Lead | null;
  onSubmit: (data: LeadCreateInput | LeadUpdateInput) => Promise<void>;
  onCancel: () => void;
  submitLabel?: string;
}

const emptyForm = {
  company_name: "",
  website: "",
  email: "",
  phone: "",
  industry: "",
  employee_count: "",
  revenue: "",
  country: "",
  status: "NEW" as LeadStatus,
};

export function LeadForm({ initial, onSubmit, onCancel, submitLabel = "Save" }: LeadFormProps) {
  const [form, setForm] = useState(emptyForm);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (initial) {
      setForm({
        company_name: initial.company_name,
        website: initial.website ?? "",
        email: initial.email ?? "",
        phone: initial.phone ?? "",
        industry: initial.industry ?? "",
        employee_count: initial.employee_count?.toString() ?? "",
        revenue: initial.revenue ?? "",
        country: initial.country ?? "",
        status: initial.status,
      });
    } else {
      setForm(emptyForm);
    }
  }, [initial]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const payload: LeadCreateInput = {
        company_name: form.company_name.trim(),
        website: form.website.trim() || null,
        email: form.email.trim() || null,
        phone: form.phone.trim() || null,
        industry: form.industry.trim() || null,
        employee_count: form.employee_count ? Number(form.employee_count) : null,
        revenue: form.revenue ? Number(form.revenue) : null,
        country: form.country.trim() || null,
        status: form.status,
      };
      await onSubmit(payload);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save lead");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="company_name">Company name *</Label>
          <Input
            id="company_name"
            required
            value={form.company_name}
            onChange={(e) => setForm({ ...form, company_name: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="website">Website</Label>
          <Input
            id="website"
            value={form.website}
            onChange={(e) => setForm({ ...form, website: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="phone">Phone</Label>
          <Input
            id="phone"
            value={form.phone}
            onChange={(e) => setForm({ ...form, phone: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="industry">Industry</Label>
          <Input
            id="industry"
            value={form.industry}
            onChange={(e) => setForm({ ...form, industry: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="country">Country</Label>
          <Input
            id="country"
            value={form.country}
            onChange={(e) => setForm({ ...form, country: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="employee_count">Employees</Label>
          <Input
            id="employee_count"
            type="number"
            min={0}
            value={form.employee_count}
            onChange={(e) => setForm({ ...form, employee_count: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="revenue">Revenue</Label>
          <Input
            id="revenue"
            type="number"
            min={0}
            step="0.01"
            value={form.revenue}
            onChange={(e) => setForm({ ...form, revenue: e.target.value })}
          />
        </div>
        <div className="space-y-2">
          <Label>Status</Label>
          <Select value={form.status} onValueChange={(value: LeadStatus) => setForm({ ...form, status: value })}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {LEAD_STATUSES.map((status) => (
                <SelectItem key={status} value={status}>
                  {LEAD_STATUS_LABELS[status]}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Saving..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
