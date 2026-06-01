"use client";

import { LogOut } from "lucide-react";

import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-4 md:px-6">
      <div>
        <h1 className="text-lg font-semibold md:text-xl">Welcome back{user ? `, ${user.full_name.split(" ")[0]}` : ""}</h1>
        <p className="text-sm text-muted-foreground">
          {user ? `${user.role} · ${user.email}` : "Loading..."}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <ThemeToggle />
        {user && (
          <>
            <Avatar className="hidden sm:flex">
              <AvatarFallback>{initials(user.full_name)}</AvatarFallback>
            </Avatar>
            <Button variant="outline" size="sm" onClick={() => void logout()}>
              <LogOut className="h-4 w-4" />
              <span className="hidden sm:inline">Sign out</span>
            </Button>
          </>
        )}
      </div>
    </header>
  );
}
