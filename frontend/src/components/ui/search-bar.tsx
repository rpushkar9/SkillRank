"use client"

import type React from "react"
import { useRef, useEffect, useState, useMemo } from "react"
import { Search } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

const GooeyFilter = () => (
  <svg style={{ position: "absolute", width: 0, height: 0 }} aria-hidden="true">
    <defs>
      <filter id="gooey-effect">
        <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="blur" />
        <feColorMatrix
          in="blur"
          type="matrix"
          values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 19 -8"
          result="goo"
        />
        <feComposite in="SourceGraphic" in2="goo" operator="atop" />
      </filter>
    </defs>
  </svg>
)

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  placeholder?: string
  isLoading?: boolean
  submitLabel?: string
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  placeholder = "Search...",
  isLoading = false,
  submitLabel = "Search",
}: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isFocused, setIsFocused] = useState(false)
  const [isAnimating, setIsAnimating] = useState(false)
  const [isClicked, setIsClicked] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })

  const isUnsupportedBrowser = useMemo(() => {
    if (typeof window === "undefined") return false
    const ua = navigator.userAgent.toLowerCase()
    return (ua.includes("safari") && !ua.includes("chrome")) || ua.includes("crios")
  }, [])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (value.trim() && !isLoading) {
      onSubmit()
      setIsAnimating(true)
      setTimeout(() => setIsAnimating(false), 1000)
    }
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isFocused) {
      const rect = e.currentTarget.getBoundingClientRect()
      setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })
    }
  }

  const handleClick = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setMousePosition({ x: e.clientX - rect.left, y: e.clientY - rect.top })
    setIsClicked(true)
    setTimeout(() => setIsClicked(false), 800)
  }

  useEffect(() => {
    if (isFocused && inputRef.current) inputRef.current.focus()
  }, [isFocused])

  const searchIconVariants = {
    initial: { scale: 1 },
    animate: {
      rotate: isAnimating ? [0, -15, 15, -10, 10, 0] : 0,
      scale: isAnimating ? [1, 1.3, 1] : 1,
      transition: { duration: 0.6, ease: "easeInOut" as const },
    },
  }

  // Floating gooey particles (indigo/violet spectrum)
  const particles = Array.from({ length: isFocused ? 16 : 0 }, (_, i) => (
    <motion.div
      key={i}
      initial={{ scale: 0 }}
      animate={{
        x: [0, (Math.random() - 0.5) * 40],
        y: [0, (Math.random() - 0.5) * 40],
        scale: [0, Math.random() * 0.7 + 0.3],
        opacity: [0, 0.7, 0],
      }}
      transition={{
        duration: Math.random() * 1.5 + 1.5,
        ease: "easeInOut",
        repeat: Infinity,
        repeatType: "reverse",
      }}
      className="absolute w-3 h-3 rounded-full"
      style={{
        left: `${Math.random() * 100}%`,
        top: `${Math.random() * 100}%`,
        filter: "blur(2px)",
        background: `linear-gradient(135deg, #818cf8, #a78bfa)`,
      }}
    />
  ))

  // Click burst particles
  const clickParticles = isClicked
    ? Array.from({ length: 12 }, (_, i) => (
        <motion.div
          key={`click-${i}`}
          initial={{ x: mousePosition.x, y: mousePosition.y, scale: 0, opacity: 1 }}
          animate={{
            x: mousePosition.x + (Math.random() - 0.5) * 140,
            y: mousePosition.y + (Math.random() - 0.5) * 140,
            scale: Math.random() * 0.6 + 0.2,
            opacity: [1, 0],
          }}
          transition={{ duration: Math.random() * 0.7 + 0.4, ease: "easeOut" }}
          className="absolute w-2.5 h-2.5 rounded-full"
          style={{
            background: ["#818cf8", "#a78bfa", "#c084fc", "#60a5fa", "#e0e7ff"][i % 5],
            boxShadow: "0 0 6px rgba(129, 140, 248, 0.6)",
          }}
        />
      ))
    : null

  return (
    <div className="relative w-full">
      <GooeyFilter />
      <motion.form
        onSubmit={handleSubmit}
        className="relative flex items-center justify-center w-full mx-auto"
        animate={{ scale: isFocused ? 1.02 : 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        onMouseMove={handleMouseMove}
      >
        <motion.div
          className={cn(
            "flex items-center w-full rounded-full relative overflow-hidden",
            isFocused
              ? "border-transparent shadow-xl"
              : "border border-white/[0.08]",
          )}
          style={{
            background: isFocused ? "rgb(9 9 11 / 80%)" : "rgb(9 9 11 / 60%)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
          }}
          animate={{
            boxShadow: isClicked
              ? "0 0 40px rgba(129, 140, 248, 0.35), 0 0 12px rgba(167, 139, 250, 0.5) inset"
              : isFocused
                ? "0 0 0 1.5px rgba(129, 140, 248, 0.3), 0 12px 30px rgba(0, 0, 0, 0.3)"
                : "0 0 0 rgba(0, 0, 0, 0)",
          }}
          onClick={handleClick}
        >
          {/* Animated gradient bg on focus */}
          {isFocused && (
            <motion.div
              className="absolute inset-0 -z-10"
              initial={{ opacity: 0 }}
              animate={{
                opacity: 0.08,
                background: [
                  "linear-gradient(90deg, #818cf8 0%, #60a5fa 100%)",
                  "linear-gradient(90deg, #a78bfa 0%, #818cf8 100%)",
                  "linear-gradient(90deg, #c084fc 0%, #a78bfa 100%)",
                  "linear-gradient(90deg, #818cf8 0%, #60a5fa 100%)",
                ],
              }}
              transition={{ duration: 12, repeat: Infinity, ease: "linear" }}
            />
          )}

          {/* Gooey particle layer */}
          <div
            className="absolute inset-0 overflow-hidden rounded-full -z-[5]"
            style={{ filter: isUnsupportedBrowser ? "none" : "url(#gooey-effect)" }}
          >
            {particles}
          </div>

          {/* Click ripple */}
          {isClicked && (
            <>
              <motion.div
                className="absolute inset-0 -z-[5] rounded-full"
                style={{ background: "rgba(129, 140, 248, 0.1)" }}
                initial={{ scale: 0, opacity: 0.7 }}
                animate={{ scale: 2, opacity: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
              />
              <motion.div
                className="absolute inset-0 -z-[5] rounded-full bg-white/[0.06]"
                initial={{ opacity: 0.4 }}
                animate={{ opacity: 0 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </>
          )}

          {clickParticles}

          {/* Search icon */}
          <motion.div
            className="pl-4 py-3 flex-shrink-0"
            variants={searchIconVariants}
            initial="initial"
            animate="animate"
          >
            <Search
              size={18}
              strokeWidth={isFocused ? 2.5 : 2}
              className={cn(
                "transition-all duration-300",
                isAnimating
                  ? "text-[#a78bfa]"
                  : isFocused
                    ? "text-[#818cf8]"
                    : "text-[#64748b]",
              )}
            />
          </motion.div>

          {/* Input */}
          <input
            ref={inputRef}
            type="text"
            placeholder={placeholder}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setTimeout(() => setIsFocused(false), 200)}
            autoComplete="off"
            className={cn(
              "w-full py-3 px-2 bg-transparent outline-none font-medium text-[0.92rem] relative z-10",
              "placeholder:text-[#4a5568]",
              isFocused ? "text-[#f1f5f9] tracking-wide" : "text-[#94a3b8]",
            )}
          />

          {/* Animated submit button */}
          <AnimatePresence>
            {value.trim() && (
              <motion.button
                type="submit"
                disabled={isLoading}
                initial={{ opacity: 0, scale: 0.8, x: -20 }}
                animate={{ opacity: 1, scale: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.8, x: -20 }}
                whileHover={{
                  scale: 1.05,
                  boxShadow: "0 8px 20px -4px rgba(129, 140, 248, 0.4)",
                }}
                whileTap={{ scale: 0.95 }}
                className={cn(
                  "px-5 py-2 mr-2 text-[0.82rem] font-semibold rounded-full text-white transition-all shadow-lg flex-shrink-0",
                  isLoading ? "opacity-60 cursor-not-allowed" : "cursor-pointer",
                )}
                style={{
                  background: "linear-gradient(135deg, #6366f1, #818cf8)",
                }}
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <motion.span
                      className="inline-block w-3 h-3 border-2 border-white/30 border-t-white rounded-full"
                      animate={{ rotate: 360 }}
                      transition={{ duration: 0.7, repeat: Infinity, ease: "linear" }}
                    />
                    {submitLabel}
                  </span>
                ) : (
                  submitLabel
                )}
              </motion.button>
            )}
          </AnimatePresence>

          {/* Shimmer sweep on focus */}
          {isFocused && (
            <motion.div
              className="absolute inset-0 rounded-full pointer-events-none"
              initial={{ opacity: 0 }}
              animate={{
                opacity: [0, 0.08, 0.15, 0.08, 0],
                background:
                  "radial-gradient(circle at 50% 0%, rgba(129,140,248,0.4) 0%, transparent 70%)",
              }}
              transition={{ duration: 2.5, repeat: Infinity, repeatType: "loop" }}
            />
          )}
        </motion.div>
      </motion.form>
    </div>
  )
}
