"use client";

import React, { useEffect, useRef } from "react";
import { useTheme } from "next-themes";
import * as THREE from "three";

interface NodeItem {
  id: string;
  name: string;
  pos: [number, number, number];
  color: string;
  pulse?: boolean;
}

const NODES: NodeItem[] = [
  { id: "supplier", name: "Supplier", pos: [-3, 0.8, 0], color: "#EF4444", pulse: true },
  { id: "inventory", name: "Inventory", pos: [-1.5, -0.6, 0.5], color: "#F59E0B" },
  { id: "orders", name: "Orders", pos: [0, 0.9, -0.5], color: "#3B82F6" },
  { id: "cash", name: "Cash Flow", pos: [1.5, -0.5, 0.5], color: "#8B5CF6" },
  { id: "payments", name: "Payments", pos: [3, 0.7, 0], color: "#22C55E" },
];

export default function Hero3D() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { theme, resolvedTheme } = useTheme();
  const currentTheme = theme === "system" ? resolvedTheme : theme;
  const isDark = currentTheme === "dark";

  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 500;
    const height = container.clientHeight || 400;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 1000);
    camera.position.set(0, 0, 7.5);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
    container.appendChild(renderer.domElement);

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, isDark ? 0.9 : 1.4);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x8b5cf6, 1.5);
    dirLight.position.set(10, 10, 5);
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0x3b82f6, 1.2);
    pointLight.position.set(-10, -10, -10);
    scene.add(pointLight);

    // 3. Supply Chain Node Spheres
    const nodeMeshes: THREE.Mesh[] = [];
    const pulseRings: THREE.Mesh[] = [];

    NODES.forEach((node) => {
      const geom = new THREE.SphereGeometry(0.35, 32, 32);
      const mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(node.color),
        roughness: 0.2,
        metalness: 0.8,
        emissive: new THREE.Color(node.color),
        emissiveIntensity: node.pulse ? 0.7 : 0.3,
      });
      const mesh = new THREE.Mesh(geom, mat);
      mesh.position.set(...node.pos);
      scene.add(mesh);
      nodeMeshes.push(mesh);

      if (node.pulse) {
        const ringGeom = new THREE.RingGeometry(0.45, 0.52, 32);
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0xef4444,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.7,
        });
        const ring = new THREE.Mesh(ringGeom, ringMat);
        ring.position.set(...node.pos);
        scene.add(ring);
        pulseRings.push(ring);
      }
    });

    // 4. Connecting Line Segments
    const linePoints: number[] = [];
    for (let i = 0; i < NODES.length - 1; i++) {
      linePoints.push(...NODES[i].pos, ...NODES[i + 1].pos);
    }
    const lineGeom = new THREE.BufferGeometry();
    lineGeom.setAttribute("position", new THREE.Float32BufferAttribute(linePoints, 3));
    const lineMat = new THREE.LineBasicMaterial({
      color: isDark ? 0x8b5cf6 : 0x4f46e5,
      transparent: true,
      opacity: isDark ? 0.6 : 0.4,
    });
    const lineSegments = new THREE.LineSegments(lineGeom, lineMat);
    scene.add(lineSegments);

    // 5. Particle Sparkles
    const particleCount = 60;
    const particleGeom = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i++) {
      particlePositions[i] = (Math.random() - 0.5) * 8;
    }
    particleGeom.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 0.08,
      color: isDark ? 0xa78bfa : 0x6366f1,
      transparent: true,
      opacity: 0.7,
    });
    const particles = new THREE.Points(particleGeom, particleMat);
    scene.add(particles);

    // Mouse parallax tracking
    let mouseX = 0;
    let mouseY = 0;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 0.5;
      mouseY = ((e.clientY - rect.top) / rect.height - 0.5) * 0.5;
    };
    window.addEventListener("mousemove", handleMouseMove);

    // Window resize tracking
    const handleResize = () => {
      if (!containerRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // 6. Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const elapsed = clock.getElapsedTime();

      // Slow Scene Rotation & Parallax Drift
      scene.rotation.y = elapsed * 0.15 + mouseX;
      scene.rotation.x = Math.sin(elapsed * 0.2) * 0.05 + mouseY;

      // Pulse ring animation
      pulseRings.forEach((ring) => {
        const s = 1 + Math.sin(elapsed * 4) * 0.1;
        ring.scale.set(s, s, 1);
      });

      // Floating Bobbing Effect on Nodes
      nodeMeshes.forEach((mesh, idx) => {
        mesh.position.y = NODES[idx].pos[1] + Math.sin(elapsed * 2 + idx) * 0.08;
      });

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("resize", handleResize);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [isDark]);

  return (
    <div
      ref={containerRef}
      className="w-full h-[400px] sm:h-[480px] relative flex items-center justify-center rounded-3xl overflow-hidden"
    />
  );
}
