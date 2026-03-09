"use client"

import { useRef, useEffect, useCallback } from "react"

interface LogoParticlesProps {
  text?: string
  className?: string
  width?: number
  height?: number
}

export function LogoParticles({
  text = "SR",
  className,
  width = 220,
  height = 100,
}: LogoParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const mouseRef = useRef({ x: -9999, y: -9999 })
  const particlesRef = useRef<
    {
      x: number
      y: number
      baseX: number
      baseY: number
      size: number
      color: string
      scattered: string
    }[]
  >([])

  const init = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return () => {}

    const ctx = canvas.getContext("2d")
    if (!ctx) return () => {}

    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    canvas.width = width * dpr
    canvas.height = height * dpr
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
    ctx.scale(dpr, dpr)

    // Render text to an offscreen canvas to sample pixels
    const offscreen = document.createElement("canvas")
    offscreen.width = width
    offscreen.height = height
    const offCtx = offscreen.getContext("2d")!
    offCtx.fillStyle = "#000"
    offCtx.fillRect(0, 0, width, height)

    // Draw the text
    const fontSize = Math.round(height * 0.72)
    offCtx.font = `700 ${fontSize}px 'Sora', 'Geist', system-ui, sans-serif`
    offCtx.textAlign = "center"
    offCtx.textBaseline = "middle"
    offCtx.fillStyle = "#fff"
    offCtx.fillText(text, width / 2, height / 2 + 2)

    const imageData = offCtx.getImageData(0, 0, width, height)
    const data = imageData.data

    // Create particles from bright pixels
    const particles: typeof particlesRef.current = []
    const gap = 2 // sample every 2 pixels
    const colors = ["#818cf8", "#a78bfa", "#c084fc", "#60a5fa", "#e0e7ff"]
    const scatteredColors = ["#c4b5fd", "#e0e7ff", "#a5b4fc"]

    for (let y = 0; y < height; y += gap) {
      for (let x = 0; x < width; x += gap) {
        const i = (y * width + x) * 4
        if (data[i] > 128) {
          particles.push({
            x,
            y,
            baseX: x,
            baseY: y,
            size: Math.random() * 1.6 + 0.6,
            color: colors[Math.floor(Math.random() * colors.length)],
            scattered: scatteredColors[Math.floor(Math.random() * scatteredColors.length)],
          })
        }
      }
    }

    particlesRef.current = particles

    const maxDist = 35
    let frameId = 0

    function animate() {
      if (!ctx) return
      ctx.clearRect(0, 0, width, height)

      const mx = mouseRef.current.x
      const my = mouseRef.current.y

      for (const p of particlesRef.current) {
        const dx = mx - p.x
        const dy = my - p.y
        const dist = Math.sqrt(dx * dx + dy * dy)

        if (dist < maxDist) {
          const force = (maxDist - dist) / maxDist
          const angle = Math.atan2(dy, dx)
          p.x = p.baseX - Math.cos(angle) * force * 22
          p.y = p.baseY - Math.sin(angle) * force * 22
          ctx.fillStyle = p.scattered
        } else {
          p.x += (p.baseX - p.x) * 0.1
          p.y += (p.baseY - p.y) * 0.1
          ctx.fillStyle = p.color
        }

        ctx.fillRect(p.x, p.y, p.size, p.size)
      }

      frameId = requestAnimationFrame(animate)
    }

    animate()
    return () => cancelAnimationFrame(frameId)
  }, [text, width, height])

  useEffect(() => {
    const cleanup = init()
    return cleanup
  }, [init])

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect()
    if (!rect) return
    mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top }
  }

  const handleMouseLeave = () => {
    mouseRef.current = { x: -9999, y: -9999 }
  }

  return (
    <canvas
      ref={canvasRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={className}
      style={{ width, height, cursor: "default" }}
      aria-label={`${text} logo`}
    />
  )
}
