"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Target } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { LoginForm } from "@/features/auth/login-form";
import { SignupForm } from "@/features/auth/signup-form";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

type AuthTab = "login" | "signup";

export default function LoginPage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [tab, setTab] = useState<AuthTab>("login");

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [isLoading, user, router]);

  if (isLoading) {
    return (
      <div className="w-full max-w-md space-y-4">
        <Skeleton className="mx-auto h-12 w-12 rounded-xl" />
        <Skeleton className="h-8 w-48 mx-auto" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (user) {
    return null;
  }

  return (
    <div className="flex w-full max-w-md flex-col items-center gap-6">
      <div className="flex flex-col items-center gap-2 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
          <Target className="h-6 w-6" />
        </div>
        <h1 className="text-2xl font-bold">Sales Intelligence</h1>
        <p className="text-sm text-muted-foreground">Web platform for leads, outreach, and analytics</p>
      </div>

      <div className="flex w-full rounded-lg border bg-muted/40 p-1">
        <button
          type="button"
          className={cn(
            "flex-1 rounded-md py-2 text-sm font-medium transition-colors",
            tab === "login" ? "bg-background shadow-sm" : "text-muted-foreground",
          )}
          onClick={() => setTab("login")}
        >
          Sign in
        </button>
        <button
          type="button"
          className={cn(
            "flex-1 rounded-md py-2 text-sm font-medium transition-colors",
            tab === "signup" ? "bg-background shadow-sm" : "text-muted-foreground",
          )}
          onClick={() => setTab("signup")}
        >
          Sign up
        </button>
      </div>

      {tab === "login" ? <LoginForm /> : <SignupForm />}
    </div>
  );
}
