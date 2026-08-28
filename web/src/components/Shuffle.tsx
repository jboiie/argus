import React, { useEffect, useMemo, useRef, useState } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { SplitText as GSAPSplitText } from "gsap/SplitText";
import { useGSAP } from "@gsap/react";
import "./Shuffle.css";

gsap.registerPlugin(ScrollTrigger, GSAPSplitText, useGSAP);

/* React Bits' Shuffle, ported to TypeScript. Two deliberate changes:
 *  - the CSS no longer forces a font family or 4rem size, so it inherits from
 *    wherever it is used rather than fighting the type system;
 *  - a ready-guard, see READY_FALLBACK_MS below. */

type ShuffleDirection = "left" | "right" | "up" | "down";

export interface ShuffleProps {
  text: string;
  className?: string;
  style?: React.CSSProperties;
  shuffleDirection?: ShuffleDirection;
  duration?: number;
  maxDelay?: number;
  ease?: string | ((t: number) => number);
  threshold?: number;
  rootMargin?: string;
  tag?: "h1" | "h2" | "h3" | "h4" | "h5" | "h6" | "p" | "span";
  textAlign?: React.CSSProperties["textAlign"];
  onShuffleComplete?: () => void;
  shuffleTimes?: number;
  animationMode?: "evenodd" | "random";
  loop?: boolean;
  loopDelay?: number;
  stagger?: number;
  scrambleCharset?: string;
  colorFrom?: string;
  colorTo?: string;
  triggerOnce?: boolean;
  respectReducedMotion?: boolean;
  triggerOnHover?: boolean;
}

/** The component hides itself until the animation has been built, to avoid a
 *  flash of un-split text. That is fine when it fails soft, but here it is the
 *  brand mark: if ScrollTrigger never fires (element never crosses the start,
 *  an offscreen tab, a refresh race) the word would stay invisible forever.
 *  A brief flash of static text is a far better failure than a missing logo. */
const READY_FALLBACK_MS = 600;

const Shuffle: React.FC<ShuffleProps> = ({
  text,
  className = "",
  style = {},
  shuffleDirection = "right",
  duration = 0.35,
  maxDelay = 0,
  ease = "power3.out",
  threshold = 0.1,
  rootMargin = "-100px",
  tag = "p",
  textAlign = "center",
  onShuffleComplete,
  shuffleTimes = 1,
  animationMode = "evenodd",
  loop = false,
  loopDelay = 0,
  stagger = 0.03,
  scrambleCharset = "",
  colorFrom,
  colorTo,
  triggerOnce = true,
  respectReducedMotion = true,
  triggerOnHover = true,
}) => {
  const ref = useRef<HTMLElement>(null);
  const [fontsLoaded, setFontsLoaded] = useState(false);
  const [ready, setReady] = useState(false);

  const splitRef = useRef<GSAPSplitText | null>(null);
  const wrappersRef = useRef<HTMLElement[]>([]);
  const tlRef = useRef<gsap.core.Timeline | null>(null);
  const playingRef = useRef(false);
  const hoverHandlerRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    if ("fonts" in document) {
      if (document.fonts.status === "loaded") setFontsLoaded(true);
      else document.fonts.ready.then(() => setFontsLoaded(true));
    } else setFontsLoaded(true);
  }, []);

  // Never leave the mark invisible - see READY_FALLBACK_MS.
  useEffect(() => {
    const t = window.setTimeout(() => setReady(true), READY_FALLBACK_MS);
    return () => window.clearTimeout(t);
  }, []);

  const scrollTriggerStart = useMemo(() => {
    const startPct = (1 - threshold) * 100;
    const mm = /^(-?\d+(?:\.\d+)?)(px|em|rem|%)?$/.exec(rootMargin || "");
    const mv = mm ? parseFloat(mm[1]) : 0;
    const mu = mm ? mm[2] || "px" : "px";
    const sign = mv === 0 ? "" : mv < 0 ? `-=${Math.abs(mv)}${mu}` : `+=${mv}${mu}`;
    return `top ${startPct}%${sign}`;
  }, [threshold, rootMargin]);

  useGSAP(
    () => {
      if (!ref.current || !text || !fontsLoaded) return;
      if (
        respectReducedMotion &&
        window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      ) {
        setReady(true);
        onShuffleComplete?.();
        return;
      }

      const el = ref.current;
      const start = scrollTriggerStart;

      const removeHover = () => {
        if (hoverHandlerRef.current && ref.current) {
          ref.current.removeEventListener("mouseenter", hoverHandlerRef.current);
          hoverHandlerRef.current = null;
        }
      };

      const teardown = () => {
        if (tlRef.current) {
          tlRef.current.kill();
          tlRef.current = null;
        }
        if (wrappersRef.current.length) {
          wrappersRef.current.forEach((wrap) => {
            const inner = wrap.firstElementChild;
            const orig = inner?.querySelector('[data-orig="1"]');
            if (orig && wrap.parentNode) wrap.parentNode.replaceChild(orig, wrap);
          });
          wrappersRef.current = [];
        }
        try {
          splitRef.current?.revert();
        } catch {
          /* noop */
        }
        splitRef.current = null;
        playingRef.current = false;
      };

      const build = () => {
        teardown();

        splitRef.current = new GSAPSplitText(el, {
          type: "chars",
          charsClass: "shuffle-char",
          wordsClass: "shuffle-word",
          linesClass: "shuffle-line",
          smartWrap: true,
          reduceWhiteSpace: false,
        });

        const chars = splitRef.current.chars || [];
        wrappersRef.current = [];

        const rolls = Math.max(1, Math.floor(shuffleTimes));
        const rand = (set: string) => set.charAt(Math.floor(Math.random() * set.length)) || "";
        const vertical = shuffleDirection === "up" || shuffleDirection === "down";

        chars.forEach((ch) => {
          const el2 = ch as HTMLElement;
          const parent = el2.parentElement;
          if (!parent) return;

          const w = el2.getBoundingClientRect().width;
          const h = el2.getBoundingClientRect().height;
          if (!w) return;

          const wrap = document.createElement("span");
          Object.assign(wrap.style, {
            display: "inline-block",
            overflow: "hidden",
            width: w + "px",
            height: vertical ? h + "px" : "auto",
            verticalAlign: "bottom",
          });

          const inner = document.createElement("span");
          Object.assign(inner.style, {
            display: "inline-block",
            whiteSpace: vertical ? "normal" : "nowrap",
            willChange: "transform",
          });

          parent.insertBefore(wrap, el2);
          wrap.appendChild(inner);

          const firstOrig = el2.cloneNode(true) as HTMLElement;
          Object.assign(firstOrig.style, {
            display: vertical ? "block" : "inline-block",
            width: w + "px",
            textAlign: "center",
          });

          el2.setAttribute("data-orig", "1");
          Object.assign(el2.style, {
            display: vertical ? "block" : "inline-block",
            width: w + "px",
            textAlign: "center",
          });

          inner.appendChild(firstOrig);
          for (let k = 0; k < rolls; k++) {
            const c = el2.cloneNode(true) as HTMLElement;
            if (scrambleCharset) c.textContent = rand(scrambleCharset);
            Object.assign(c.style, {
              display: vertical ? "block" : "inline-block",
              width: w + "px",
              textAlign: "center",
            });
            inner.appendChild(c);
          }
          inner.appendChild(el2);

          const steps = rolls + 1;

          if (shuffleDirection === "right" || shuffleDirection === "down") {
            const firstCopy = inner.firstElementChild;
            const real = inner.lastElementChild;
            if (real) inner.insertBefore(real, inner.firstChild);
            if (firstCopy) inner.appendChild(firstCopy);
          }

          let startX = 0,
            finalX = 0,
            startY = 0,
            finalY = 0;

          if (shuffleDirection === "right") startX = -steps * w;
          else if (shuffleDirection === "left") finalX = -steps * w;
          else if (shuffleDirection === "down") startY = -steps * h;
          else if (shuffleDirection === "up") finalY = -steps * h;

          if (!vertical) {
            gsap.set(inner, { x: startX, y: 0, force3D: true });
            inner.setAttribute("data-start-x", String(startX));
            inner.setAttribute("data-final-x", String(finalX));
          } else {
            gsap.set(inner, { x: 0, y: startY, force3D: true });
            inner.setAttribute("data-start-y", String(startY));
            inner.setAttribute("data-final-y", String(finalY));
          }

          if (colorFrom) inner.style.color = colorFrom;
          wrappersRef.current.push(wrap);
        });
      };

      const inners = () =>
        wrappersRef.current.map((w) => w.firstElementChild as HTMLElement).filter(Boolean);

      const randomizeScrambles = () => {
        if (!scrambleCharset) return;
        wrappersRef.current.forEach((w) => {
          const strip = w.firstElementChild;
          if (!strip) return;
          const kids = Array.from(strip.children);
          for (let i = 1; i < kids.length - 1; i++) {
            kids[i].textContent = scrambleCharset.charAt(
              Math.floor(Math.random() * scrambleCharset.length),
            );
          }
        });
      };

      const cleanupToStill = () => {
        wrappersRef.current.forEach((w) => {
          const strip = w.firstElementChild as HTMLElement | null;
          if (!strip) return;
          const real = strip.querySelector('[data-orig="1"]');
          if (!real) return;
          strip.replaceChildren(real);
          strip.style.transform = "none";
          strip.style.willChange = "auto";
        });
      };

      const armHover = () => {
        if (!triggerOnHover || !ref.current) return;
        removeHover();
        const handler = () => {
          if (playingRef.current) return;
          build();
          if (scrambleCharset) randomizeScrambles();
          play();
        };
        hoverHandlerRef.current = handler;
        ref.current.addEventListener("mouseenter", handler);
      };

      const play = () => {
        const strips = inners();
        if (!strips.length) return;

        playingRef.current = true;
        const isVertical = shuffleDirection === "up" || shuffleDirection === "down";

        const tl = gsap.timeline({
          smoothChildTiming: true,
          repeat: loop ? -1 : 0,
          repeatDelay: loop ? loopDelay : 0,
          onRepeat: () => {
            if (scrambleCharset) randomizeScrambles();
            if (isVertical) {
              gsap.set(strips, {
                y: (_i, t) => parseFloat((t as HTMLElement).getAttribute("data-start-y") || "0"),
              });
            } else {
              gsap.set(strips, {
                x: (_i, t) => parseFloat((t as HTMLElement).getAttribute("data-start-x") || "0"),
              });
            }
            onShuffleComplete?.();
          },
          onComplete: () => {
            playingRef.current = false;
            if (!loop) {
              cleanupToStill();
              if (colorTo) gsap.set(strips, { color: colorTo });
              onShuffleComplete?.();
              armHover();
            }
          },
        });

        const addTween = (targets: HTMLElement[], at: number) => {
          const vars: gsap.TweenVars = {
            duration,
            ease,
            force3D: true,
            stagger: animationMode === "evenodd" ? stagger : 0,
          };
          if (isVertical) {
            vars.y = (_i: number, t: Element) =>
              parseFloat((t as HTMLElement).getAttribute("data-final-y") || "0");
          } else {
            vars.x = (_i: number, t: Element) =>
              parseFloat((t as HTMLElement).getAttribute("data-final-x") || "0");
          }
          tl.to(targets, vars, at);
          if (colorFrom && colorTo) tl.to(targets, { color: colorTo, duration, ease }, at);
        };

        if (animationMode === "evenodd") {
          const odd = strips.filter((_, i) => i % 2 === 1);
          const even = strips.filter((_, i) => i % 2 === 0);
          const oddTotal = duration + Math.max(0, odd.length - 1) * stagger;
          const evenStart = odd.length ? oddTotal * 0.7 : 0;
          if (odd.length) addTween(odd, 0);
          if (even.length) addTween(even, evenStart);
        } else {
          strips.forEach((strip) => {
            const d = Math.random() * maxDelay;
            const vars: gsap.TweenVars = { duration, ease, force3D: true };
            if (isVertical) vars.y = parseFloat(strip.getAttribute("data-final-y") || "0");
            else vars.x = parseFloat(strip.getAttribute("data-final-x") || "0");
            tl.to(strip, vars, d);
            if (colorFrom && colorTo)
              tl.fromTo(strip, { color: colorFrom }, { color: colorTo, duration, ease }, d);
          });
        }

        tlRef.current = tl;
      };

      const create = () => {
        build();
        if (scrambleCharset) randomizeScrambles();
        play();
        armHover();
        setReady(true);
      };

      const st = ScrollTrigger.create({ trigger: el, start, once: triggerOnce, onEnter: create });

      return () => {
        st.kill();
        removeHover();
        teardown();
      };
    },
    {
      dependencies: [
        text,
        duration,
        maxDelay,
        ease,
        scrollTriggerStart,
        fontsLoaded,
        shuffleDirection,
        shuffleTimes,
        animationMode,
        loop,
        loopDelay,
        stagger,
        scrambleCharset,
        colorFrom,
        colorTo,
        triggerOnce,
        respectReducedMotion,
        triggerOnHover,
        onShuffleComplete,
      ],
      scope: ref,
    },
  );

  const commonStyle = useMemo<React.CSSProperties>(
    () => ({ textAlign, ...style }),
    [textAlign, style],
  );
  const classes = `shuffle-parent ${ready ? "is-ready" : ""} ${className}`;

  return React.createElement(tag || "p", { ref, className: classes, style: commonStyle }, text);
};

export default Shuffle;
