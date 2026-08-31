import { Bell, Languages, Menu, Search } from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-20 items-center gap-4 border-b border-slate-200 bg-white/95 px-5 backdrop-blur md:px-8">
      <Button
        variant="ghost"
        size="icon"
        className="text-slate-500 lg:hidden"
      >
        <Menu className="size-5" />
      </Button>

      <div className="relative hidden w-full max-w-md md:block">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search event, IP, CVE, IOC..."
          className="border-slate-200 bg-slate-50 pl-10 text-slate-900 placeholder:text-slate-400"
        />
      </div>

      <div className="ml-auto flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          className="hidden gap-2 text-slate-600 sm:flex"
        >
          <Languages className="size-4" />
          EN
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="relative text-slate-500"
        >
          <Bell className="size-5" />
          <span className="absolute right-2 top-2 size-2 rounded-full bg-red-500" />
        </Button>

        <div className="mx-1 h-8 w-px bg-slate-200" />

        <div className="flex items-center gap-3">
          <Avatar className="size-9 border border-cyan-100">
            <AvatarFallback className="bg-cyan-50 text-xs font-semibold text-cyan-700">
              SA
            </AvatarFallback>
          </Avatar>

          <div className="hidden sm:block">
            <p className="text-sm font-medium text-slate-900">
              SOC Analyst
            </p>
            <p className="text-xs text-slate-500">
              Senior Analyst
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
