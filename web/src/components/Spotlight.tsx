import { useEffect } from "react";
import { gsap } from "gsap";
import "./Spotlight.css";

/**
 * Cursor spotlight + per-card border glow, extracted from React Bits'
 * MagicBento.
 *
 * Only the ambient half of that component is used here. MagicBento also ships
 * tilt, magnetism, particles and a click ripple — all of which move or decorate
 * the card under the pointer. On a console whose panels hold tables, transcripts
 * and money figures, content that shifts while you read it is a defect, not a
 * flourish. The spotlight and border glow add depth without displacing a single
 * pixel of content, so those are the two that earn their place.
 *
 * Any element tagged `.glow-card` participates. One document-level listener
 * serves all of them rather than one per card.
 */
const SPOTLIGHT_RADIUS = 340;
const GLOW = "201, 162, 39"; // brass, matching the console accent

export function Spotlight({ radius = SPOTLIGHT_RADIUS }: { radius?: number }) {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    // Coarse pointers have no hover, so a cursor-following light is dead weight.
    if (!window.matchMedia("(hover: hover) and (pointer: fine)").matches) return;

    const light = document.createElement("div");
    light.className = "cursor-spotlight";
    light.style.background = `radial-gradient(circle,
      rgba(${GLOW}, 0.10) 0%,
      rgba(${GLOW}, 0.06) 18%,
      rgba(${GLOW}, 0.03) 32%,
      transparent 68%)`;
    document.body.appendChild(light);

    const proximity = radius * 0.5;
    const fade = radius * 0.75;
    let frame = 0;
    let pending: { x: number; y: number } | null = null;

    // Coalesce to one update per frame by storing the latest position rather
    // than dropping events while a frame is in flight. Early-returning on a
    // pending flag deadlocks the whole effect if a frame callback is ever
    // throttled or dropped, since the flag is only cleared inside it.
    const flush = () => {
      frame = 0;
      const point = pending;
      pending = null;
      if (!point) return;
      {
        const e = point;
        const cards = document.querySelectorAll<HTMLElement>(".glow-card");
        let nearest = Infinity;

        cards.forEach((card) => {
          const r = card.getBoundingClientRect();
          const cx = r.left + r.width / 2;
          const cy = r.top + r.height / 2;
          const dist = Math.max(
            0,
            Math.hypot(e.x - cx, e.y - cy) - Math.max(r.width, r.height) / 2,
          );
          nearest = Math.min(nearest, dist);

          let intensity = 0;
          if (dist <= proximity) intensity = 1;
          else if (dist <= fade) intensity = (fade - dist) / (fade - proximity);

          card.style.setProperty("--glow-x", `${((e.x - r.left) / r.width) * 100}%`);
          card.style.setProperty("--glow-y", `${((e.y - r.top) / r.height) * 100}%`);
          card.style.setProperty("--glow-intensity", String(intensity));
          card.style.setProperty("--glow-radius", `${radius}px`);
        });

        gsap.to(light, { left: e.x, top: e.y, duration: 0.12, ease: "power2.out" });
        const target =
          nearest <= proximity ? 1 : nearest <= fade ? (fade - nearest) / (fade - proximity) : 0;
        gsap.to(light, { opacity: target, duration: target > 0 ? 0.2 : 0.45, ease: "power2.out" });
      }
    };

    const onMove = (ev: MouseEvent) => {
      pending = { x: ev.clientX, y: ev.clientY };
      if (!frame) frame = requestAnimationFrame(flush);
    };

    const onLeave = () => {
      document
        .querySelectorAll<HTMLElement>(".glow-card")
        .forEach((c) => c.style.setProperty("--glow-intensity", "0"));
      gsap.to(light, { opacity: 0, duration: 0.3 });
    };

    document.addEventListener("mousemove", onMove, { passive: true });
    document.addEventListener("mouseleave", onLeave);

    return () => {
      if (frame) cancelAnimationFrame(frame);
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseleave", onLeave);
      light.remove();
    };
  }, [radius]);

  return null;
}
