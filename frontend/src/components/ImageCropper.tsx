import { useRef, useState } from "react";

interface Props {
  src: string;
  onClose: () => void;
  onConfirm: (dataUrl: string) => void;
}

const DISPLAY_WIDTH = 480;

/**
 * Crops a region out of an image entirely client-side (canvas) and hands the
 * caller back a data: URI — nothing is uploaded anywhere. Exists because box/
 * pack product photos often show several items at once (e.g. a trading badge
 * pack) and we don't want the whole box shot as a single character's head
 * image. Drag a rectangle over the part you want.
 */
export default function ImageCropper({ src, onClose, onConfirm }: Props) {
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [dragOrigin, setDragOrigin] = useState<{ x: number; y: number } | null>(null);
  const [dragRect, setDragRect] = useState<{ x: number; y: number; w: number; h: number } | null>(null);

  const [naturalSize, setNaturalSize] = useState<{ w: number; h: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const displayHeight = naturalSize ? (DISPLAY_WIDTH * naturalSize.h) / naturalSize.w : DISPLAY_WIDTH;

  function handleImgLoad() {
    const img = imgRef.current;
    if (img) setNaturalSize({ w: img.naturalWidth, h: img.naturalHeight });
  }

  function cropToDataUrl(sx: number, sy: number, sw: number, sh: number): string | null {
    const img = imgRef.current;
    if (!img || sw <= 1 || sh <= 1) return null;
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(sw);
    canvas.height = Math.round(sh);
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height);
    try {
      return canvas.toDataURL("image/jpeg", 0.92);
    } catch {
      return null;
    }
  }

  function finish(dataUrl: string | null) {
    if (!dataUrl) {
      setError("裁剪失败——这张图片所在的站点可能不允许跨域读取像素数据（CORS），暂时没法在浏览器里裁剪它。");
      return;
    }
    onConfirm(dataUrl);
  }

  function confirmSelection() {
    if (!dragRect || !naturalSize) return;
    const scaleX = naturalSize.w / DISPLAY_WIDTH;
    const scaleY = naturalSize.h / displayHeight;
    finish(cropToDataUrl(dragRect.x * scaleX, dragRect.y * scaleY, dragRect.w * scaleX, dragRect.h * scaleY));
  }

  function pointerPos(e: React.MouseEvent): { x: number; y: number } {
    const rect = containerRef.current!.getBoundingClientRect();
    const x = Math.min(Math.max(e.clientX - rect.left, 0), DISPLAY_WIDTH);
    const y = Math.min(Math.max(e.clientY - rect.top, 0), displayHeight);
    return { x, y };
  }

  function onMouseDown(e: React.MouseEvent) {
    const pos = pointerPos(e);
    setIsDragging(true);
    setDragOrigin(pos);
    setDragRect({ x: pos.x, y: pos.y, w: 0, h: 0 });
  }

  function onMouseMove(e: React.MouseEvent) {
    if (!isDragging || !dragOrigin) return;
    const pos = pointerPos(e);
    setDragRect({
      x: Math.min(dragOrigin.x, pos.x),
      y: Math.min(dragOrigin.y, pos.y),
      w: Math.abs(pos.x - dragOrigin.x),
      h: Math.abs(pos.y - dragOrigin.y),
    });
  }

  function onMouseUp() {
    setIsDragging(false);
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-panel" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <strong>Crop image</strong>
          <button className="btn" onClick={onClose}>
            Close
          </button>
        </div>

        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", margin: "0 0 0.6rem" }}>
          在图上拖一个矩形框
        </p>

        <div
          ref={containerRef}
          className="crop-canvas-wrap"
          style={{ width: DISPLAY_WIDTH, height: displayHeight }}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
        >
          <img
            ref={imgRef}
            src={src}
            alt=""
            crossOrigin="anonymous"
            onLoad={handleImgLoad}
            style={{ width: DISPLAY_WIDTH, height: displayHeight, display: "block", userSelect: "none" }}
            draggable={false}
          />

          {dragRect && (
            <div
              className="crop-drag-rect"
              style={{ left: dragRect.x, top: dragRect.y, width: dragRect.w, height: dragRect.h }}
            />
          )}
        </div>

        {error && <p style={{ color: "#e07a7a", fontSize: "0.85rem" }}>{error}</p>}

        <div className="review-actions" style={{ marginTop: "0.8rem" }}>
          <button className="btn primary" disabled={!dragRect || dragRect.w < 4} onClick={confirmSelection}>
            Use selection
          </button>
        </div>
      </div>
    </div>
  );
}
