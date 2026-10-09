'use client'

import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

interface SkillNodeData {
  name: string
  color: number
  radius: number
  speed: number
  phase: number
  elevation: number
}

const SKILL_NODES: SkillNodeData[] = [
  { name: 'LangGraph Engine', color: 0x00f0ff, radius: 4.8, speed: 0.5, phase: 0, elevation: 1.2 },
  { name: 'PGVector 1536d', color: 0x8b5cf6, radius: 5.6, speed: -0.4, phase: 1.1, elevation: -1.0 },
  { name: 'System Design', color: 0x38bdf8, radius: 6.2, speed: 0.35, phase: 2.3, elevation: 1.8 },
  { name: 'Audio Biometrics', color: 0x10b981, radius: 5.0, speed: -0.45, phase: 3.5, elevation: -1.4 },
  { name: 'Adaptive Coding', color: 0xf59e0b, radius: 6.6, speed: 0.3, phase: 4.6, elevation: 0.6 },
  { name: 'Salary Simulator', color: 0xec4899, radius: 5.3, speed: -0.38, phase: 5.5, elevation: -0.8 },
]

export default function ThreeIntelligenceCore() {
  const mountRef = useRef<HTMLDivElement>(null)
  const [activeNode, setActiveNode] = useState<string | null>(null)
  const [webGlSupported, setWebGlSupported] = useState(true)

  useEffect(() => {
    const container = mountRef.current
    if (!container) return

    // Verify WebGL availability
    try {
      const testCanvas = document.createElement('canvas')
      const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl')
      if (!gl) {
        setWebGlSupported(false)
        return
      }
    } catch {
      setWebGlSupported(false)
      return
    }

    const width = container.clientWidth || 600
    const height = container.clientHeight || 550

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x07080c, 0.04)

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0, 15)

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.2
    container.appendChild(renderer.domElement)

    // 2. Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4)
    scene.add(ambientLight)

    const cyanPoint = new THREE.PointLight(0x00f0ff, 4, 30)
    cyanPoint.position.set(8, 8, 10)
    scene.add(cyanPoint)

    const violetPoint = new THREE.PointLight(0x8b5cf6, 4, 30)
    violetPoint.position.set(-8, -8, 8)
    scene.add(violetPoint)

    const centralLight = new THREE.PointLight(0x00f0ff, 2.5, 12)
    centralLight.position.set(0, 0, 0)
    scene.add(centralLight)

    // 3. Central Intelligence Core
    const coreGroup = new THREE.Group()
    scene.add(coreGroup)

    // Inner Nucleus
    const innerNucleusGeo = new THREE.SphereGeometry(1.2, 32, 32)
    const innerNucleusMat = new THREE.MeshStandardMaterial({
      color: 0x00f0ff,
      emissive: 0x0088ff,
      emissiveIntensity: 0.9,
      roughness: 0.1,
      metalness: 0.8,
      transparent: true,
      opacity: 0.92,
    })
    const innerNucleus = new THREE.Mesh(innerNucleusGeo, innerNucleusMat)
    coreGroup.add(innerNucleus)

    // Middle Faceted Lattice (Dodecahedron)
    const midGeo = new THREE.DodecahedronGeometry(1.9, 0)
    const midMat = new THREE.MeshPhysicalMaterial({
      color: 0x8b5cf6,
      emissive: 0x4c1d95,
      emissiveIntensity: 0.5,
      roughness: 0.2,
      metalness: 0.3,
      transmission: 0.6,
      transparent: true,
      opacity: 0.45,
      wireframe: false,
    })
    const midPoly = new THREE.Mesh(midGeo, midMat)
    coreGroup.add(midPoly)

    // Outer Wireframe Shield (Icosahedron)
    const outerGeo = new THREE.IcosahedronGeometry(2.7, 1)
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x00f0ff,
      wireframe: true,
      transparent: true,
      opacity: 0.35,
    })
    const outerWire = new THREE.Mesh(outerGeo, wireMat)
    coreGroup.add(outerWire)

    // Orbital Rings
    const ringGeo1 = new THREE.TorusGeometry(3.5, 0.02, 16, 100)
    const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x00f0ff, transparent: true, opacity: 0.3 })
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1)
    ring1.rotation.x = Math.PI / 3
    scene.add(ring1)

    const ringGeo2 = new THREE.TorusGeometry(4.2, 0.02, 16, 100)
    const ringMat2 = new THREE.MeshBasicMaterial({ color: 0x8b5cf6, transparent: true, opacity: 0.25 })
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2)
    ring2.rotation.y = Math.PI / 4
    ring2.rotation.x = -Math.PI / 6
    scene.add(ring2)

    // 4. Procedural Particle Nebula
    const particleCount = 700
    const particlePositions = new Float32Array(particleCount * 3)
    const particleColors = new Float32Array(particleCount * 3)
    const c1 = new THREE.Color(0x00f0ff)
    const c2 = new THREE.Color(0x8b5cf6)

    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(Math.random() * 2 - 1)
      const rad = 3.5 + Math.random() * 8.5

      particlePositions[i * 3] = rad * Math.sin(phi) * Math.cos(theta)
      particlePositions[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta)
      particlePositions[i * 3 + 2] = rad * Math.cos(phi)

      const mixed = Math.random() > 0.5 ? c1 : c2
      particleColors[i * 3] = mixed.r
      particleColors[i * 3 + 1] = mixed.g
      particleColors[i * 3 + 2] = mixed.b
    }

    const particleGeo = new THREE.BufferGeometry()
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3))
    particleGeo.setAttribute('color', new THREE.BufferAttribute(particleColors, 3))

    const particleMat = new THREE.PointsMaterial({
      size: 0.08,
      vertexColors: true,
      transparent: true,
      opacity: 0.7,
      blending: THREE.AdditiveBlending,
    })
    const particleSystem = new THREE.Points(particleGeo, particleMat)
    scene.add(particleSystem)

    // 5. Orbiting Skill Nodes & Animated Line Connectors
    const nodesGroup = new THREE.Group()
    scene.add(nodesGroup)

    interface NodeMeshItem {
      mesh: THREE.Mesh
      data: SkillNodeData
      line: THREE.Line
    }

    const nodeMeshes: NodeMeshItem[] = SKILL_NODES.map((node) => {
      const nodeGeo = new THREE.SphereGeometry(0.28, 16, 16)
      const nodeMat = new THREE.MeshStandardMaterial({
        color: node.color,
        emissive: node.color,
        emissiveIntensity: 0.8,
        roughness: 0.2,
      })
      const mesh = new THREE.Mesh(nodeGeo, nodeMat)
      nodesGroup.add(mesh)

      // Dynamic connector line from core to node
      const lineMat = new THREE.LineBasicMaterial({
        color: node.color,
        transparent: true,
        opacity: 0.35,
      })
      const lineGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(0, 0, 0),
      ])
      const line = new THREE.Line(lineGeo, lineMat)
      scene.add(line)

      return { mesh, data: node, line }
    })

    // 6. Interactive Mouse Tracking & Parallax
    let targetMouseX = 0
    let targetMouseY = 0
    let currentMouseX = 0
    let currentMouseY = 0

    const handleMouseMove = (event: MouseEvent) => {
      const rect = container.getBoundingClientRect()
      const x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      const y = -(((event.clientY - rect.top) / rect.height) * 2 - 1)
      targetMouseX = x * 1.5
      targetMouseY = y * 1.5
    }

    window.addEventListener('mousemove', handleMouseMove)

    // 7. Resize Handler
    const handleResize = () => {
      if (!container) return
      const newW = container.clientWidth
      const newH = container.clientHeight
      camera.aspect = newW / newH
      camera.updateProjectionMatrix()
      renderer.setSize(newW, newH)
    }

    window.addEventListener('resize', handleResize)

    // 8. Animation Loop
    let animationFrameId: number
    const clock = new THREE.Clock()

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate)
      const elapsedTime = clock.getElapsedTime()

      // Smooth mouse damping
      currentMouseX += (targetMouseX - currentMouseX) * 0.05
      currentMouseY += (targetMouseY - currentMouseY) * 0.05

      // Camera parallax
      camera.position.x = currentMouseX * 1.8
      camera.position.y = currentMouseY * 1.8
      camera.lookAt(0, 0, 0)

      // Rotate core elements
      coreGroup.rotation.y = elapsedTime * 0.25
      coreGroup.rotation.x = Math.sin(elapsedTime * 0.2) * 0.15

      midPoly.rotation.x = -elapsedTime * 0.3
      midPoly.rotation.z = elapsedTime * 0.15

      outerWire.rotation.y = -elapsedTime * 0.15
      outerWire.rotation.z = Math.cos(elapsedTime * 0.25) * 0.2

      // Core pulse
      const pulseScale = 1.0 + Math.sin(elapsedTime * 2.2) * 0.06
      innerNucleus.scale.set(pulseScale, pulseScale, pulseScale)

      // Orbital rings rotation
      ring1.rotation.z = elapsedTime * 0.12
      ring2.rotation.z = -elapsedTime * 0.1

      // Particle system gentle drift
      particleSystem.rotation.y = elapsedTime * 0.04
      particleSystem.rotation.x = Math.sin(elapsedTime * 0.03) * 0.05

      // Orbiting Skill Nodes positioning
      nodeMeshes.forEach(({ mesh, data, line }) => {
        const angle = elapsedTime * data.speed + data.phase
        const x = Math.cos(angle) * data.radius
        const z = Math.sin(angle) * data.radius
        const y = data.elevation + Math.sin(elapsedTime * 1.2 + data.phase) * 0.35

        mesh.position.set(x, y, z)

        // Update dynamic connector line vertices
        const linePositions = new Float32Array([0, 0, 0, x, y, z])
        line.geometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3))
        line.geometry.attributes.position.needsUpdate = true
      })

      renderer.render(scene, camera)
    }

    animate()

    // 9. Cleanup on Unmount
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('resize', handleResize)

      // Dispose Geometries & Materials
      innerNucleusGeo.dispose()
      innerNucleusMat.dispose()
      midGeo.dispose()
      midMat.dispose()
      outerGeo.dispose()
      wireMat.dispose()
      ringGeo1.dispose()
      ringMat1.dispose()
      ringGeo2.dispose()
      ringMat2.dispose()
      particleGeo.dispose()
      particleMat.dispose()

      nodeMeshes.forEach(({ mesh, line }) => {
        mesh.geometry.dispose()
        ;(mesh.material as THREE.Material).dispose()
        line.geometry.dispose()
        ;(line.material as THREE.Material).dispose()
      })

      renderer.dispose()
      if (container && renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [])

  if (!webGlSupported) {
    return (
      <div className="relative w-full h-[520px] flex items-center justify-center">
        <div className="absolute inset-0 bg-radial-gradient from-cyan-500/20 via-violet-600/10 to-transparent blur-2xl" />
        <div className="relative z-10 text-center p-8 border border-white/10 rounded-2xl bg-black/40 backdrop-blur-xl">
          <div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-tr from-cyan-400 to-violet-500 animate-pulse-slow flex items-center justify-center">
            <span className="text-3xl font-black text-black">AI</span>
          </div>
          <h3 className="text-xl font-bold text-white mt-4">Enterprise AI Neural Core</h3>
          <p className="text-sm text-slate-400 mt-2 max-w-xs">Adaptive stateful intelligence engine linking vector embeddings to multi-turn conversational telemetry.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="relative w-full h-[540px] flex items-center justify-center select-none overflow-visible">
      {/* Three.js Canvas Container */}
      <div ref={mountRef} className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Floating Status Badges & Skill Indicators */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-wrap gap-2 pointer-events-none max-w-sm">
        {SKILL_NODES.map((node) => (
          <span
            key={node.name}
            className="px-2.5 py-1 rounded-full text-[11px] font-mono font-medium tracking-wide bg-black/60 border border-white/10 text-slate-300 backdrop-blur-md flex items-center gap-1.5"
          >
            <span
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: `#${node.color.toString(16).padStart(6, '0')}` }}
            />
            {node.name}
          </span>
        ))}
      </div>

      <div className="absolute top-4 right-4 z-10 pointer-events-none">
        <div className="px-3 py-1.5 rounded-lg bg-black/60 border border-cyan-500/30 text-cyan-300 font-mono text-[11px] backdrop-blur-md flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
          LANGGRAPH 0.2 STATE MACHINE
        </div>
      </div>
    </div>
  )
}
