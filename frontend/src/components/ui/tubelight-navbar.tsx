"use client"

import React, { useEffect, useState } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface NavItem {
  name: string
  url: string
  icon: LucideIcon
}

interface NavBarProps {
  items: NavItem[]
  className?: string
}

export function NavBar({ items, className }: NavBarProps) {
  const pathname = usePathname()
  const [activeTab, setActiveTab] = useState(
    items.find((i) => i.url === pathname)?.name ?? items[0].name
  )
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const match = items.find((i) => i.url === pathname)
    if (match) setActiveTab(match.name)
  }, [pathname, items])

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    handleResize()
    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  return (
    <div
      className={cn(
        "fixed bottom-0 sm:top-0 left-1/2 -translate-x-1/2 z-50 mb-6 sm:pt-6",
        className,
      )}
    >
      <div
        style={{
          background: "rgb(255 255 255 / 4%)",
          border: "1px solid rgb(255 255 255 / 10%)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
        className="flex items-center gap-1 py-1 px-1 rounded-full shadow-lg"
      >
        {items.map((item) => {
          const Icon = item.icon
          const isActive = activeTab === item.name

          return (
            <Link
              key={item.name}
              href={item.url}
              onClick={() => setActiveTab(item.name)}
              style={{
                color: isActive ? "#818cf8" : "#94a3b8",
              }}
              className={cn(
                "relative cursor-pointer text-sm font-semibold px-6 py-2 rounded-full transition-colors duration-200",
                "hover:text-white",
              )}
            >
              <span className="hidden md:inline">{item.name}</span>
              <span className="md:hidden">
                <Icon size={18} strokeWidth={2.5} />
              </span>

              {isActive && (
                <motion.div
                  layoutId="lamp"
                  className="absolute inset-0 w-full rounded-full -z-10"
                  style={{ background: "rgb(129 140 248 / 8%)" }}
                  initial={false}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                >
                  {/* Tubelight bar */}
                  <div
                    className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-1 rounded-t-full"
                    style={{ background: "#818cf8" }}
                  >
                    <div
                      className="absolute w-12 h-6 rounded-full blur-md -top-2 -left-2"
                      style={{ background: "rgb(129 140 248 / 25%)" }}
                    />
                    <div
                      className="absolute w-8 h-6 rounded-full blur-md -top-1"
                      style={{ background: "rgb(129 140 248 / 20%)" }}
                    />
                    <div
                      className="absolute w-4 h-4 rounded-full blur-sm top-0 left-2"
                      style={{ background: "rgb(129 140 248 / 20%)" }}
                    />
                  </div>
                </motion.div>
              )}
            </Link>
          )
        })}
      </div>
    </div>
  )
}
