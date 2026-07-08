import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata = {
  title: "Scova - AI Essay Grader",
  description: "Revolutionize the way you grade essays with AI.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={cn(inter.className, "min-h-screen bg-slate-50 antialiased")}>
        {children}
        <Toaster position="top-center" richColors />
      </body>
    </html>
  );
}
