import React, { useEffect, useRef } from 'react';

const ParticleBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = canvas.width = window.innerWidth;
    let height = canvas.height = window.innerHeight;

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Star particles
    const stars = Array.from({ length: 150 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 1.5,
      opacity: Math.random(),
      speed: Math.random() * 0.05 + 0.01,
    }));

    // Glow orbs
    const orbs = [
      { x: width * 0.2, y: height * 0.3, radius: 300, color: 'rgba(41, 98, 255, 0.07)', vx: 0.2, vy: 0.1 },
      { x: width * 0.8, y: height * 0.7, radius: 400, color: 'rgba(124, 77, 255, 0.07)', vx: -0.15, vy: -0.1 },
      { x: width * 0.5, y: height * 0.5, radius: 350, color: 'rgba(0, 176, 255, 0.05)', vx: 0.1, vy: -0.15 },
    ];

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Draw orbs
      orbs.forEach(orb => {
        orb.x += orb.vx;
        orb.y += orb.vy;

        if (orb.x < 0 || orb.x > width) orb.vx *= -1;
        if (orb.y < 0 || orb.y > height) orb.vy *= -1;

        const gradient = ctx.createRadialGradient(orb.x, orb.y, 0, orb.x, orb.y, orb.radius);
        gradient.addColorStop(0, orb.color);
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
      });

      // Draw stars
      ctx.fillStyle = '#fff';
      stars.forEach(star => {
        star.opacity += star.speed;
        if (star.opacity > 1 || star.opacity < 0) star.speed *= -1;
        
        ctx.globalAlpha = Math.max(0, star.opacity);
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1;

      animationFrameId = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1,
        background: '#050505',
        pointerEvents: 'none',
      }}
    />
  );
};

export default ParticleBackground;
