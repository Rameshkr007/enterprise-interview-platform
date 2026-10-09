'use client'

import React, { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function HolographicBrain() {
  const mountRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = mountRef.current
    if (!container) return

    const width = container.clientWidth || 320
    const height = container.clientHeight || 240

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0, 7.5)

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance',
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)

    const purpleLight = new THREE.PointLight(0xa855f7, 5, 20)
    purpleLight.position.set(5, 5, 5)
    scene.add(purpleLight)

    const cyanLight = new THREE.PointLight(0x06b6d4, 4, 20)
    cyanLight.position.set(-5, -5, 5)
    scene.add(cyanLight)

    // Brain / Neural Network Hemisphere Structure
    const brainGroup = new THREE.Group()
    scene.add(brainGroup)

    // Generate neural nodes in a brain/dual-hemisphere volume
    const nodeCount = 140
    const nodes: THREE.Vector3[] = []
    const nodeColors: number[] = []

    for (let i = 0; i < nodeCount; i++) {
      // Create two ellipsoidal lobes
      const lobe = Math.random() > 0.5 ? 1 : -1
      const u = Math.random()
      const v = Math.random()
      const theta = u * 2.0 * Math.PI
      const phi = Math.acos(2.0 * v - 1.0)
      const r = Math.cbrt(Math.random()) * 1.8

      const x = r * Math.sin(phi) * Math.cos(theta) * 1.1 + (lobe * 0.45)
      const y = r * Math.sin(phi) * Math.sin(theta) * 0.95 + 0.1
      const z = r * Math.cos(phi) * 1.25

      nodes.push(new THREE.Vector3(x, y, z))
      nodeColors.push(lobe === 1 ? 0x8b5cf6 : 0x06b6d4)
    }

    // Node Meshes
    const nodeGeo = new THREE.SphereGeometry(0.065, 8, 8)
    const nodeGroup = new THREE.Group()

    nodes.forEach((pos, idx) => {
      const col = nodeColors[idx]
      const mat = new THREE.MeshBasicMaterial({
        color: col,
        transparent: true,
        opacity: 0.9,
      })
      const mesh = new THREE.Mesh(nodeGeo, mat)
      mesh.position.copy(pos)
      nodeGroup.add(mesh)
    })
    brainGroup.add(nodeGroup)

    // Synaptic Connection Lines between nearby nodes
    const lineMat = new THREE.LineBasicMaterial({
      color: 0x818cf8,
      transparent: true,
      opacity: 0.28,
      blending: THREE.AdditiveBlending,
    })

    const linePositions: number[] = []
    const maxDistance = 0.95

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dist = nodes[i].distanceTo(nodes[j])
        if (dist < maxDistance) {
          linePositions.push(nodes[i].x, nodes[i].y, nodes[i].z)
          linePositions.push(nodes[j].x, nodes[j].y, nodes[j].z)
        }
      }
    }

    const lineGeo = new THREE.BufferGeometry()
    lineGeo.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3))
    const lineMesh = new THREE.LineSegments(lineGeo, lineMat)
    brainGroup.add(lineMesh)

    // Holographic Pedestal / Base Rings
    const ringGeo = new THREE.RingGeometry(1.6, 1.8, 32)
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xa855f7,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.4,
    })
    const baseRing = new THREE.Mesh(ringGeo, ringMat)
    baseRing.rotation.x = Math.PI / 2
    baseRing.position.y = -2.2
    brainGroup.add(baseRing)

    const innerRingGeo = new THREE.RingGeometry(0.8, 0.95, 32)
    const innerRingMat = new THREE.MeshBasicMaterial({
      color: 0x06b6d4,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5,
    })
    const innerRing = new THREE.Mesh(innerRingGeo, innerRingMat)
    innerRing.rotation.x = Math.PI / 2
    innerRing.position.y = -2.2
    brainGroup.add(innerRing)

    // Animation Loop
    let animId: number
    const clock = new THREE.Clock()

    const animate = () => {
      animId = requestAnimationFrame(animate)
      const elapsed = clock.getElapsedTime()

      brainGroup.rotation.y = elapsed * 0.4
      brainGroup.position.y = Math.sin(elapsed * 1.5) * 0.12

      baseRing.rotation.z = -elapsed * 0.5
      innerRing.rotation.z = elapsed * 0.8

      renderer.render(scene, camera)
    }

    animate()

    const handleResize = () => {
      if (!container) return
      const w = container.clientWidth
      const h = container.clientHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }

    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('resize', handleResize)
      nodeGeo.dispose()
      lineGeo.dispose()
      ringGeo.dispose()
      innerRingGeo.dispose()
      renderer.dispose()
      if (container && renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [])

  return (
    <div className="relative w-full h-full min-h-[220px] flex items-center justify-center select-none pointer-events-none">
      <div className="absolute inset-0 bg-radial-gradient from-purple-600/20 via-blue-600/10 to-transparent blur-xl" />
      <div ref={mountRef} className="w-full h-full" />
    </div>
  )
}
