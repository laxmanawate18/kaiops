import { useEffect, useRef } from 'react'
import * as THREE from 'three'

function ThreeBackground({ theme = 'dark' }) {
  const canvasRef = useRef(null)
  const rendererRef = useRef(null)
  const sceneRef = useRef(null)
  const cameraRef = useRef(null)
  const animationFrameIdRef = useRef(null)
  const particleRef = useRef(null)
  const waveRef = useRef(null)
  const glowSpheresRef = useRef([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const scene = new THREE.Scene()
    scene.background = null

    const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.1, 80)
    camera.position.set(0, 2, 18)

    const renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      powerPreference: 'high-performance'
    })
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

    sceneRef.current = scene
    cameraRef.current = camera
    rendererRef.current = renderer

    const ambient = new THREE.AmbientLight(0x5be1ff, 0.25)
    const softLight = new THREE.PointLight(0x7d4dff, 1, 60)
    softLight.position.set(4, 10, 12)
    scene.add(ambient, softLight)

    const particleCount = 400
    const particleGeometry = new THREE.BufferGeometry()
    const positions = new Float32Array(particleCount * 3)
    for (let i = 0; i < particleCount; i++) {
      const radius = 6 + Math.random() * 10
      const angle = Math.random() * Math.PI * 2
      const height = (Math.random() - 0.5) * 6
      positions[i * 3] = Math.cos(angle) * radius
      positions[i * 3 + 1] = height
      positions[i * 3 + 2] = Math.sin(angle) * radius
    }
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))

    const particleMaterial = new THREE.PointsMaterial({
      color: theme === 'dark' ? 0x6fdfff : 0x2761ff,
      size: 0.15,
      transparent: true,
      opacity: 0.5,
      depthWrite: false
    })

    const particles = new THREE.Points(particleGeometry, particleMaterial)
    scene.add(particles)
    particleRef.current = particles

    const waveGeometry = new THREE.PlaneGeometry(60, 40, 80, 60)
    const waveMaterial = new THREE.MeshBasicMaterial({
      color: 0x07122b,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    })
    const wave = new THREE.Mesh(waveGeometry, waveMaterial)
    wave.rotation.x = -Math.PI / 2.3
    wave.position.y = -8
    scene.add(wave)
    waveRef.current = wave

    const glowColors = [0x00f0ff, 0x6f7dff, 0x4b2bff]
    glowSpheresRef.current = []
    glowColors.forEach((color, idx) => {
      const glowGeometry = new THREE.SphereGeometry(2.2 + idx * 0.4, 32, 32)
      const glowMaterial = new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.08 })
      const glowSphere = new THREE.Mesh(glowGeometry, glowMaterial)
      glowSphere.position.set(-6 + idx * 6, 0, -10 - idx * 2)
      scene.add(glowSphere)
      glowSpheresRef.current.push(glowSphere)
    })

    let mouseX = 0
    const onMouseMove = (event) => {
      mouseX = (event.clientX / window.innerWidth) * 2 - 1
    }
    window.addEventListener('mousemove', onMouseMove)

    const onWindowResize = () => {
      if (cameraRef.current && rendererRef.current) {
        cameraRef.current.aspect = window.innerWidth / window.innerHeight
        cameraRef.current.updateProjectionMatrix()
        rendererRef.current.setSize(window.innerWidth, window.innerHeight)
      }
    }
    window.addEventListener('resize', onWindowResize)

    const animate = () => {
      animationFrameIdRef.current = requestAnimationFrame(animate)

      if (cameraRef.current) {
        cameraRef.current.position.x += (mouseX * 1.5 - cameraRef.current.position.x) * 0.02
        cameraRef.current.lookAt(0, 0, -10)
      }

      if (particleRef.current) {
        particleRef.current.rotation.y += 0.0004
      }

      if (waveRef.current) {
        const time = Date.now() * 0.0004
        const positions = waveRef.current.geometry.attributes.position
        for (let i = 0; i < positions.count; i++) {
          const x = positions.getX(i)
          const z = positions.getZ(i)
          const y = Math.sin(x * 0.1 + time) * 0.2 + Math.cos(z * 0.15 + time) * 0.2
          positions.setY(i, y)
        }
        positions.needsUpdate = true
      }

      glowSpheresRef.current.forEach((sphere, idx) => {
        sphere.material.opacity = 0.05 + Math.sin(Date.now() * 0.0003 + idx) * 0.015
        sphere.position.y = Math.sin(Date.now() * 0.0002 + idx) * 1.5 - 2
      })

      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current)
      }
    }

    animate()

    return () => {
      if (animationFrameIdRef.current) {
        cancelAnimationFrame(animationFrameIdRef.current)
      }
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('resize', onWindowResize)
      if (rendererRef.current) {
        rendererRef.current.dispose()
      }
      if (sceneRef.current) {
        sceneRef.current.traverse((child) => {
          if (child.isMesh || child.isPoints) {
            if (child.geometry) child.geometry.dispose()
            if (child.material) child.material.dispose()
          }
        })
      }
    }
  }, [theme])

  return <canvas ref={canvasRef} className="three-canvas" />
}

export default ThreeBackground
