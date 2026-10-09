'use client'

import React, { useRef, useState, MouseEvent } from 'react'
import Link from 'next/link'

interface SpatialCardProps {
  href: string
  title: string
  description: string
  icon: string | React.ReactNode
  badge?: string
  accentColor?: string
  ctaText?: string
  stat?: string
  statLabel?: string
  className?: string
}

export default function SpatialCard({
  href,
  title,
  description,
  icon,
  badge,
  accentColor = '#00f0ff',
  ctaText = 'Explore Module',
  stat,
  statLabel,
  className = '',
}: SpatialCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)
  const [rotateX, setRotateX] = useState(0)
  const [rotateY, setRotateY] = useState(0)
  const [spotlightPos, setSpotlightPos] = useState({ x: 50, y: 50 })
  const [isHovered, setIsHovered] = useState(false)

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    const centerX = rect.width / 2
    const centerY = rect.height / 2

    // Moderate tilt angles for comfortable, premium feel
    const tiltY = ((x - centerX) / centerX) * 8
    const tiltX = -((y - centerY) / centerY) * 8

    setRotateX(tiltX)
    setRotateY(tiltY)
    setSpotlightPos({
      x: Math.round((x / rect.width) * 100),
      y: Math.round((y / rect.height) * 100),
    })
  }

  const handleMouseEnter = () => setIsHovered(true)

  const handleMouseLeave = () => {
    setIsHovered(false)
    setRotateX(0)
    setRotateY(0)
  }

  return (
    <Link href={href} className="group block focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 rounded-2xl">
      <div
        ref={cardRef}
        onMouseMove={handleMouseMove}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{
          transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(${isHovered ? 1.02 : 1}, ${isHovered ? 1.02 : 1}, 1)`,
          transition: isHovered ? 'transform 0.1s ease-out' : 'transform 0.5s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
        className={`relative h-full flex flex-col justify-between p-6 sm:p-7 rounded-2xl border border-white/10 bg-[#0c0e17]/80 backdrop-blur-xl overflow-hidden transition-shadow duration-500 hover:border-cyan-500/40 hover:shadow-[0_12px_40px_rgba(0,0,0,0.6)] ${className}`}
      >
        {/* Cursor-responsive Dynamic Spotlight */}
        <div
          className="pointer-events-none absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-0"
          style={{
            background: `radial-gradient(400px circle at ${spotlightPos.x}% ${spotlightPos.y}%, rgba(0, 240, 255, 0.12), transparent 80%)`,
          }}
        />

        {/* Ambient Top Glow Line */}
        <div
          className="absolute top-0 left-0 right-0 h-[1px] opacity-20 group-hover:opacity-100 transition-opacity duration-300"
          style={{
            background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
          }}
        />

        {/* Header: Icon & Category Badge */}
        <div className="relative z-10 flex items-start justify-between gap-4 mb-4">
          <div
            className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl transition-transform duration-300 group-hover:scale-110 shadow-lg"
            style={{
              background: `linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02))`,
              border: `1px solid rgba(255, 255, 255, 0.12)`,
            }}
          >
            {typeof icon === 'string' ? (
              <span dangerouslySetInnerHTML={{ __html: icon }} />
            ) : (
              icon
            )}
          </div>

          {badge && (
            <span
              className="text-[10px] font-mono font-semibold uppercase tracking-wider px-2.5 py-1 rounded-full border backdrop-blur-md"
              style={{
                borderColor: `${accentColor}40`,
                backgroundColor: `${accentColor}15`,
                color: accentColor,
              }}
            >
              {badge}
            </span>
          )}
        </div>

        {/* Body: Title & Description */}
        <div className="relative z-10 flex-1">
          <h3 className="text-lg font-bold text-white mb-2 group-hover:text-cyan-300 transition-colors duration-200">
            {title}
          </h3>
          <p className="text-sm text-slate-400 leading-relaxed line-clamp-3">
            {description}
          </p>
        </div>

        {/* Optional Live Telemetry Metric */}
        {stat && (
          <div className="relative z-10 mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs font-mono">
            <span className="text-slate-500">{statLabel || 'Benchmark'}</span>
            <span className="text-cyan-400 font-semibold">{stat}</span>
          </div>
        )}

        {/* Footer: Action Trigger */}
        <div className="relative z-10 mt-5 pt-3 flex items-center justify-between text-xs font-semibold text-slate-300 group-hover:text-white transition-colors">
          <span className="tracking-wide uppercase text-[11px] font-mono text-slate-400 group-hover:text-cyan-400 transition-colors">
            {ctaText}
          </span>
          <span className="inline-block transform transition-transform duration-300 group-hover:translate-x-1.5 text-cyan-400 font-bold">
            →
          </span>
        </div>
      </div>
    </Link>
  )
}
