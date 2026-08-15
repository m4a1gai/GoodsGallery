import { useEffect, useRef, useState } from "react";

interface Props {
  src: string;
  onClose: () => void;
  /** If provided, a "Crop" toggle appears in the controls bar. Confirming a
   * crop selection calls this with the cropped region as a data: URI, then
   * closes the lightbox. */
  onCrop?: (dataUrl: string) => void;
}

const MIN_SCALE = 0.5;
const MAX_SCALE = 6;

/**
 * Fullscreen image viewer: scroll/buttons to zoom, drag to pan when zoomed
 * away from 1x, double-click to toggle 1x/2x — and, when `onCrop` is passed,
 * an in-place crop tool. Cropping from here (rather than a separate flat
 * modal) means you can zoom in first for precision before drawing the
 * selection. The selection rectangle is tracked in screen/client
 * coordinates; at confirm time `img.getBoundingClientRect()` gives the
 * image's actual on-screen rect *after* the pan/zoom transform, so mapping
 * screen coordinates back to natural image pixels doesn't need to re-derive
 * the transform math by hand.
 */
export default function Lightbox({ src, onClose, onCrop }: Props) {
  const imgRef = useRef<HTMLImageElement>(null);

  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef<{ x: number; y: number } | null>(null);
  const posStart = useRef({ x: 0, y: 0 });

  const [cropMode, setCropMode] = useState(false);
  const [cropRect, setCropRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [selecting, setSelecting] = useState(false);
  const selectStart = useRef<{ x: number; y: number } | null>(null);

  const [error, setError] = useState<string | null>(null);

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

  function toggleCropMode() {
    setCropMode((v) => !v);
    setCropRect(null);
  }

  function onMouseDown(e: React.MouseEvent) {
    if (cropMode) {
      const start = { x: e.clientX, y: e.clientY };
      selectStart.current = start;
      setSelecting(true);
      setCropRect({ x: start.x, y: start.y, w: 0, h: 0 });
      return;
    }
    if (scale === 1) return;
    e.preventDefault();
    setDragging(true);
    dragStart.current = { x: e.clientX, y: e.clientY };
    posStart.current = pos;
  }

  function onMouseMove(e: React.MouseEvent) {
    if (cropMode) {
      if (!selecting || !selectStart.current) return;
      const start = selectStart.current;
      setCropRect({
        x: Math.min(start.x, e.clientX),
        y: Math.min(start.y, e.clientY),
        w: Math.abs(e.clientX - start.x),
        h: Math.abs(e.clientY - start.y),
      });
      return;
    }
    if (!dragging || !dragStart.current) return;
    setPos({
      x: posStart.current.x + (e.clientX - dragStart.current.x),
      y: posStart.current.y + (e.clientY - dragStart.current.y),
    });
  }

  function onMouseUp() {
    setSelecting(false);
    setDragging(false);
  }

  function onDoubleClick() {
    if (cropMode) return;
    if (scale > 1) {
      reset();
    } else {
      setScale(2);
    }
  }

  function confirmCrop() {
    const img = imgRef.current;
    if (!img || !cropRect || cropRect.w < 4 || cropRect.h < 4 || !onCrop) return;

    const rect = img.getBoundingClientRect();
    const scaleX = img.naturalWidth / rect.width;
    const scaleY = img.naturalHeight / rect.height;

    const sx = Math.max(0, (cropRect.x - rect.left) * scaleX);
    const sy = Math.max(0, (cropRect.y - rect.top) * scaleY);
    const sw = Math.min(img.naturalWidth - sx, cropRect.w * scaleX);
    const sh = Math.min(img.naturalHeight - sy, cropRect.h * scaleY);
    if (sw <= 1 || sh <= 1) return;

    const canvas = document.createElement("canvas");
    canvas.width = Math.round(sw);
    canvas.height = Math.round(sh);
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    try {
      const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
      onCrop(dataUrl);
      onClose();
    } catch {
      setError("裁剪失败——这张图片所在的站点可能不允许跨域读取像素数据（CORS），暂时没法在浏览器里裁剪它。");
    }
  }

  const cursor = cropMode
    ? "crosshair"
    : scale === 1
      ? "zoom-in"
      : dragging
        ? "grabbing"
        : "grab";

  return (
    <div className="lightbox-backdrop" onClick={cropMode ? undefined : onClose} onWheel={onWheel}>
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
        {onCrop && (
          <button className={`btn ${cropMode ? "primary" : ""}`} onClick={toggleCropMode}>
            {cropMode ? "Cancel crop" : "Crop"}
          </button>
        )}
        {cropMode && cropRect && cropRect.w > 4 && (
          <button className="btn primary" onClick={confirmCrop}>
            Use selection
          </button>
        )}
      </div>

      {cropMode && (
        <p className="lightbox-hint" onClick={(e) => e.stopPropagation()}>
          在图上拖一个矩形框；缩放/平移调整好视角后再框选，精度更高
        </p>
      )}

      <img
        ref={imgRef}
        src={src}
        alt=""
        crossOrigin="anonymous"
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
          cursor,
          transition: dragging ? "none" : "transform 0.08s ease-out",
        }}
      />

      {cropMode && cropRect && (
        <div
          className="crop-drag-rect"
          style={{ position: "fixed", left: cropRect.x, top: cropRect.y, width: cropRect.w, height: cropRect.h }}
        />
      )}

      {error && (
        <p className="lightbox-error" onClick={(e) => e.stopPropagation()}>
          {error}
        </p>
      )}
    </div>
  );
}
