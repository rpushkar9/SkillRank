"use client"

import { Search, Sparkles } from "lucide-react"
import { NavBar } from "@/components/ui/tubelight-navbar"

const NAV_ITEMS = [
  { name: "Search", url: "/", icon: Search },
  { name: "Recommend", url: "/recommend", icon: Sparkles },
]

export function AppNavBar() {
  return <NavBar items={NAV_ITEMS} />
}
