"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { leadsService } from "@/services/leads.service";
import { usersService, type AdminUser } from "@/services/users.service";
import type { Lead } from "@/types/leads";
import type { UserRole } from "@/types/auth";

export default function SettingsPage() {
  const { user, token } = useAuth();
  const [adminUsers, setAdminUsers] = useState<AdminUser[]>([]);
  const [duplicates, setDuplicates] = useState<Lead[]>([]);
  const [loadingAdmin, setLoadingAdmin] = useState(false);

  const loadAdmin = useCallback(async () => {
    if (!token || user?.role !== "ADMIN") return;
    setLoadingAdmin(true);
    try {
      const data = await usersService.list(token);
      setAdminUsers(data.items);
    } catch {
      setAdminUsers([]);
    } finally {
      setLoadingAdmin(false);
    }
  }, [token, user?.role]);

  useEffect(() => {
    void loadAdmin();
  }, [loadAdmin]);

  useEffect(() => {
    async function loadDupes() {
      if (!token || (user?.role !== "ADMIN" && user?.role !== "MANAGER")) return;
      try {
        const data = await leadsService.listDuplicates(token);
        setDuplicates(data.items);
      } catch {
        setDuplicates([]);
      }
    }
    void loadDupes();
  }, [token, user?.role]);

  async function handleRoleChange(userId: string, role: UserRole) {
    if (!token) return;
    try {
      await usersService.update(token, userId, { role });
      toast.success("Role updated");
      await loadAdmin();
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Update failed");
    }
  }

  async function dismissDuplicate(leadId: string) {
    if (!token) return;
    try {
      await leadsService.dismissDuplicate(token, leadId);
      setDuplicates((prev) => prev.filter((l) => l.id !== leadId));
      toast.success("Duplicate removed");
    } catch (error) {
      toast.error(error instanceof ApiClientError ? error.message : "Failed to dismiss");
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Settings</h2>
        <p className="text-muted-foreground">Profile, team management, and data quality</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Profile</CardTitle>
          <CardDescription>Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1">
            <Label>Name</Label>
            <p className="text-sm">{user?.full_name}</p>
          </div>
          <div className="space-y-1">
            <Label>Email</Label>
            <p className="text-sm">{user?.email}</p>
          </div>
          <div className="space-y-1">
            <Label>Role</Label>
            <Badge>{user?.role}</Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
          <CardDescription>Toggle light or dark mode</CardDescription>
        </CardHeader>
        <CardContent>
          <ThemeToggle />
        </CardContent>
      </Card>

      {(user?.role === "ADMIN" || user?.role === "MANAGER") && (
        <Card>
          <CardHeader>
            <CardTitle>Duplicate leads</CardTitle>
            <CardDescription>Review and remove flagged duplicates from discovery or imports</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {duplicates.length === 0 ? (
              <p className="text-sm text-muted-foreground">No duplicates pending review.</p>
            ) : (
              duplicates.map((lead) => (
                <div key={lead.id} className="flex items-center justify-between rounded border p-3 text-sm">
                  <div>
                    <p className="font-medium">{lead.company_name}</p>
                    <p className="text-muted-foreground">{lead.website || lead.email || "—"}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" asChild>
                      <Link href={`/leads/${lead.duplicate_of_id}`}>View original</Link>
                    </Button>
                    <Button size="sm" variant="destructive" onClick={() => void dismissDuplicate(lead.id)}>
                      Dismiss
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {user?.role === "ADMIN" && (
        <Card>
          <CardHeader>
            <CardTitle>Team members</CardTitle>
            <CardDescription>Manage user roles (admin only)</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {loadingAdmin ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              adminUsers.map((u) => (
                <div key={u.id} className="flex items-center justify-between rounded border p-3 text-sm">
                  <div>
                    <p className="font-medium">{u.full_name}</p>
                    <p className="text-muted-foreground">{u.email}</p>
                  </div>
                  <select
                    className="rounded border bg-background px-2 py-1 text-sm"
                    value={u.role}
                    onChange={(e) => void handleRoleChange(u.id, e.target.value as UserRole)}
                  >
                    <option value="SALES">SALES</option>
                    <option value="MANAGER">MANAGER</option>
                    <option value="ADMIN">ADMIN</option>
                  </select>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
