import { useEffect, useRef, useState } from "react";

interface Props {
  src: string;
  onClose: () => void;
}

const MIN_SCALE = 0.5;
const MAX_SCALE = 6;

/** Fullscreen image viewer: scroll/buttons to zoom, drag to pan when zoomed
 * in, double-click to toggle 1x/2x — the standard "click to view big image"
 * pattern. */
export default function Lightbox({ src, onClose }: Props) {
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef<{ x: number; y: number } | null>(null);
  const posStart = useRef({ x: 0, y: 0 });

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function clampScale(s: number) {
    return Math.min(Math.max(s, MIN_SCALE), MAX_SCALE);
  }

  function onWheel(e: React.WheelEvent) {
    e.preventDefault();
    const delta = -e.deltaY * 0.0015;
    setScale((s) => clampScale(s + s * delta));
  }

  function zoomIn() {
    setScale((s) => clampScale(s * 1.3));
  }
  function zoomOut() {
    setScale((s) => clampScale(s / 1.3));
  }
  function reset() {
    setScale(1);
    setPos({ x: 0, y: 0 });
  }

  function onMouseDown(e: React.MouseEvent) {
    if (scale <= 1) return;
    e.preventDefault();
    setDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    posStart.current = pos;
  }
  function onMouseMove(e: React.MouseEvent) {
    if (!dragging || !dragStart.current) return;
    setPos({
      x: posStart.current.x + (e.clientX - dragStart.current.x),
      y: posStart.current.y + (e.clientY - dragStart.current.y),
    });
  }
  function onMouseUp() {
    setDragging(false);
  }

  function onDoubleClick() {
    if (scale > 1) {
      reset();
    } else {
      setScale(2);
    }
  }

  return (
    <div className="lightbox-backdrop" onClick={onClose} onWheel={onWheel}>
      <button className="lightbox-close" onClick={onClose} title="Close (Esc)">
        ×
      </button>
      <div className="lightbox-controls" onClick={(e) => e.stopPropagation()}>
        <button className="btn" onClick={zoomOut}>
          −
        </button>
        <span>{Math.round(scale * 100)}%</span>
        <button className="btn" onClick={zoomIn}>
          +
        </button>
        <button className="btn" onClick={reset}>
          Reset
        </button>
      </div>
      <img
        src={src}
        alt=""
        draggable={false}
        onClick={(e) => e.stopPropagation()}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
        onDoubleClick={onDoubleClick}
        className="lightbox-image"
        style={{
          transform: `translate(${pos.x}px, ${pos.y}px) scale(${scale})`,
          cursor: scale > 1 ? (dragging ? "grabbing" : "grab") : "zoom-in",
          transition: dragging ? "none" : "transform 0.08s ease-out",
        }}
      />
    </div>
  );
}
