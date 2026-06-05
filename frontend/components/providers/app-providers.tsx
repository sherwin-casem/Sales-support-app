"use client";

import { Toaster } from "sonner";

import { AppLoadingShell } from "@/components/layout/app-loading-shell";
import { ClientOnly } from "@/components/client-only";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/lib/theme-provider";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <ClientOnly fallback={<AppLoadingShell />}>
      <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
        <AuthProvider>
          {children}
          <Toaster richColors closeButton position="top-right" />
        </AuthProvider>
      </ThemeProvider>
    </ClientOnly>
  );
}
