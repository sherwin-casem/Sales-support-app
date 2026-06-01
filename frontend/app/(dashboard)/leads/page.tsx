import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function LeadsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Leads</h2>
        <p className="text-muted-foreground">Manage and enrich your sales pipeline</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Coming soon</CardTitle>
          <CardDescription>Lead table with search, filters, and CSV import/export will be added next.</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
