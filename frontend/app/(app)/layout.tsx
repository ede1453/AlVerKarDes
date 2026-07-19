import { redirect } from "next/navigation";
import { getSessionToken } from "@/lib/session";

// Auth guard for everything under the (app) route group: dashboard,
// watchlist, etc. No session cookie -> redirect to /giris.
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const token = await getSessionToken();
  if (!token) {
    redirect("/giris");
  }

  return <>{children}</>;
}
