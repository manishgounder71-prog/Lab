'use client';

import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

interface SeverityOrbProps {
  severity: 'ALPHA' | 'OMEGA' | 'OPTIMAL' | 'P1';
  riskScore: number; // 0 to 100
}

export default function SeverityOrb({ severity, riskScore }: SeverityOrbProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const configRef = useRef({ severity, riskScore });

  // Update properties ref in real-time without triggering effect runs
  useEffect(() => {
    configRef.current = { severity, riskScore };
  }, [severity, riskScore]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 300;
    const height = container.clientHeight || 300;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Initial colors based on first render severity
    const initialConfig = configRef.current;
    let primaryColor = 0xff0000;
    let emissiveColor = 0x330000;
    let coreColor = 0xff3300;

    if (initialConfig.severity === 'OPTIMAL') {
      primaryColor = 0x00ffcc;
      emissiveColor = 0x003322;
      coreColor = 0x00ff88;
    } else if (initialConfig.severity === 'ALPHA') {
      primaryColor = 0xff6600;
      emissiveColor = 0x331100;
      coreColor = 0xff9900;
    } else if (initialConfig.severity === 'OMEGA') {
      primaryColor = 0xff0055;
      emissiveColor = 0x440011;
      coreColor = 0xff3366;
    }

    // Severity Orb (Outer wireframe icosahedron)
    const geometry = new THREE.IcosahedronGeometry(1.2, 3);
    const material = new THREE.MeshPhongMaterial({
      color: primaryColor,
      emissive: emissiveColor,
      shininess: 120,
      transparent: true,
      opacity: 0.7,
      wireframe: true,
    });

    const orb = new THREE.Mesh(geometry, material);
    scene.add(orb);

    // Inner Core (solid glowing sphere)
    const coreGeom = new THREE.SphereGeometry(0.55, 32, 32);
    const coreMat = new THREE.MeshBasicMaterial({ color: coreColor });
    const core = new THREE.Mesh(coreGeom, coreMat);
    scene.add(core);

    // Light setups
    const light = new THREE.PointLight(primaryColor, 3, 10);
    light.position.set(2, 2, 2);
    scene.add(light);

    const ambientLight = new THREE.AmbientLight(0x222222);
    scene.add(ambientLight);

    camera.position.z = 3.2;

    let animationFrameId: number;
    const timer = new THREE.Timer();

    function animate() {
      timer.update();
      const elapsedTime = timer.getElapsed();
      const currentConfig = configRef.current;

      // Color definitions updated dynamically in the frame loop (no context recreations)
      let targetColor = 0xff0000;
      let targetEmissive = 0x330000;
      let targetCore = 0xff3300;

      if (currentConfig.severity === 'OPTIMAL') {
        targetColor = 0x00ffcc;
        targetEmissive = 0x003322;
        targetCore = 0x00ff88;
      } else if (currentConfig.severity === 'ALPHA') {
        targetColor = 0xff6600;
        targetEmissive = 0x331100;
        targetCore = 0xff9900;
      } else if (currentConfig.severity === 'OMEGA') {
        targetColor = 0xff0055;
        targetEmissive = 0x440011;
        targetCore = 0xff3366;
      }

      // Smooth color transitions in-place
      material.color.setHex(targetColor);
      material.emissive.setHex(targetEmissive);
      coreMat.color.setHex(targetCore);
      light.color.setHex(targetColor);

      // Rotation speeds change based on riskScore
      const rotSpeed = 0.4 + (currentConfig.riskScore / 100) * 0.8;
      orb.rotation.y = elapsedTime * 0.3 * rotSpeed;
      orb.rotation.x = elapsedTime * 0.15 * rotSpeed;

      // Pulse scaling based on severity
      const baseScale = 1.0;
      const pulseAmplitude = 0.08 + (currentConfig.riskScore / 100) * 0.12;
      const pulseFreq = 3.5 + (currentConfig.riskScore / 100) * 5.0;

      const scale = baseScale + Math.sin(elapsedTime * pulseFreq) * pulseAmplitude;
      orb.scale.set(scale, scale, scale);

      // Core scales in opposition
      const coreScale = 1.0 - (scale - 1.0) * 0.8;
      core.scale.set(coreScale, coreScale, coreScale);

      renderer.render(scene, camera);
      animationFrameId = requestAnimationFrame(animate);
    }

    animate();

    // Debounced resize to avoid layout thrashing
    let resizeTimeout: ReturnType<typeof setTimeout> | null = null;
    const handleResize = () => {
      if (resizeTimeout) return;
      resizeTimeout = setTimeout(() => {
        resizeTimeout = null;
        if (!container || !renderer || !camera) return;
        const w = container.clientWidth;
        const h = container.clientHeight;
        if (w === 0 || h === 0) return;
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
      }, 150);
    };

    window.addEventListener('resize', handleResize, { passive: true });

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (resizeTimeout) clearTimeout(resizeTimeout);
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
      // Dispose all GPU resources
      geometry.dispose();
      material.dispose();
      coreGeom.dispose();
      coreMat.dispose();
      renderer.dispose();
      scene.remove(orb, core, light, ambientLight);
    };
  }, []); // Run only once on mount

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div ref={containerRef} className="w-full h-full max-w-[340px] max-h-[340px]" />
    </div>
  );
}
