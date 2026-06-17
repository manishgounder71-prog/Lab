import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";
import React from "react";

// ── Polyfill requestAnimationFrame/cancelAnimationFrame ──────────────────────
globalThis.requestAnimationFrame = ((callback: FrameRequestCallback) => {
  return setTimeout(callback, 0) as unknown as number;
}) as typeof globalThis.requestAnimationFrame;

globalThis.cancelAnimationFrame = ((id: number) => {
  clearTimeout(id);
}) as typeof globalThis.cancelAnimationFrame;

// ── ResizeObserver polyfill ─────────────────────────────────────────────────
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;

// ── IntersectionObserver polyfill ───────────────────────────────────────────
class MockIntersectionObserver {
  readonly root: Element | null = null;
  readonly rootMargin: string = "";
  readonly thresholds: ReadonlyArray<number> = [];
  constructor() {}
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}
globalThis.IntersectionObserver =
  MockIntersectionObserver as unknown as typeof IntersectionObserver;

// ── WebSocket polyfill ──────────────────────────────────────────────────────
class MockWebSocket {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;

  readonly CONNECTING = 0;
  readonly OPEN = 1;
  readonly CLOSING = 2;
  readonly CLOSED = 3;

  readyState: number = MockWebSocket.CLOSED;
  send = vi.fn();
  close = vi.fn();
  addEventListener = vi.fn();
  removeEventListener = vi.fn();
  dispatchEvent = vi.fn<(event: Event) => boolean>(() => true);
  onopen: ((this: WebSocket, ev: Event) => unknown) | null = null;
  onclose: ((this: WebSocket, ev: CloseEvent) => unknown) | null = null;
  onmessage: ((this: WebSocket, ev: MessageEvent) => unknown) | null = null;
  onerror: ((this: WebSocket, ev: Event) => unknown) | null = null;
  url: string = "";
  protocol: string = "";
  extensions: string = "";
  bufferedAmount: number = 0;
  binaryType: BinaryType = "blob";

  constructor(url: string | URL) {
    this.url = String(url);
  }
}
globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;

// ── Canvas 2D Context mock ──────────────────────────────────────────────────
let _fillStyle = "";
const mockCanvasContext: Partial<CanvasRenderingContext2D> = {
  fillRect: vi.fn(),
  clearRect: vi.fn(),
  get fillStyle() {
    return _fillStyle;
  },
  set fillStyle(v: string) {
    _fillStyle = v;
  },
  strokeStyle: "",
  lineWidth: 1,
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  stroke: vi.fn(),
  arc: vi.fn(),
  fill: vi.fn(),
  setTransform: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
  scale: vi.fn(),
  rotate: vi.fn(),
  translate: vi.fn(),
  closePath: vi.fn(),
};

// Override getContext to return the mock
HTMLCanvasElement.prototype.getContext = vi.fn(
  () => mockCanvasContext as unknown as CanvasRenderingContext2D
) as unknown as typeof HTMLCanvasElement.prototype.getContext;

// ── Global framer-motion mock ───────────────────────────────────────────────
// This prevents 'whileHover' and other animation props from leaking to the DOM
// The unused variables in destructuring are intentional — we strip motion props
vi.mock("framer-motion", () => {
  const Div = ({ children, ...props }: { children?: React.ReactNode; [key: string]: unknown }) => {
    // Strip framer-motion specific props
    const {
      initial: _initial,
      animate: _animate,
      exit: _exit,
      whileHover: _whileHover,
      whileTap: _whileTap,
      whileInView: _whileInView,
      whileFocus: _whileFocus,
      whileDrag: _whileDrag,
      viewport: _viewport,
      transition: _transition,
      variants: _variants,
      drag: _drag,
      layout: _layout,
      layoutId: _layoutId,
      onAnimationStart: _onAnimationStart,
      onAnimationComplete: _onAnimationComplete,
      style,
      ...rest
    } = props;
    return React.createElement("div", { ...rest, style }, children);
  };

  return {
    motion: {
      div: Div,
      span: (props: Record<string, unknown>) => {
        const { initial: _i, animate: _a, exit: _e, whileHover: _wh, whileTap: _wt, whileInView: _wiv, whileFocus: _wf, whileDrag: _wd, viewport: _vp, transition: _tr, variants: _va, ...rest } = props;
        return React.createElement("span", rest);
      },
      button: (props: Record<string, unknown>) => {
        const { initial: _i, animate: _a, exit: _e, whileHover: _wh, whileTap: _wt, whileInView: _wiv, whileFocus: _wf, whileDrag: _wd, viewport: _vp, transition: _tr, variants: _va, ...rest } = props;
        return React.createElement("button", rest);
      },
    },
    AnimatePresence: ({ children }: { children: React.ReactNode }) =>
      React.createElement(React.Fragment, null, children),
  };
});

// ── Three.js mock ───────────────────────────────────────────────────────────
vi.mock("three", () => {
  const mockVector3 = { set: vi.fn(), x: 0, y: 0, z: 0 };
  const mockEuler = { y: 0, x: 0, set: vi.fn() };
  const mockScale = { set: vi.fn(), x: 1, y: 1, z: 1 };

  const mockObject3D = {
    position: mockVector3,
    rotation: mockEuler,
    scale: mockScale,
    add: vi.fn(),
    remove: vi.fn(),
    visible: true,
  };

  const mockMesh = {
    ...mockObject3D,
    geometry: { dispose: vi.fn() },
    material: { dispose: vi.fn() },
  };

  const mockRenderer = {
    setSize: vi.fn(),
    setPixelRatio: vi.fn(),
    render: vi.fn(),
    dispose: vi.fn(),
    domElement: document.createElement("canvas"),
  };

  return {
    Scene: vi.fn(() => ({ ...mockObject3D })),
    PerspectiveCamera: vi.fn(() => ({
      position: { z: 0, set: vi.fn() },
      aspect: 1,
      updateProjectionMatrix: vi.fn(),
    })),
    WebGLRenderer: vi.fn(() => mockRenderer),
    MeshPhongMaterial: vi.fn(() => ({ dispose: vi.fn(), color: 0, emissive: 0, shininess: 0, transparent: false, opacity: 0, wireframe: false })),
    MeshBasicMaterial: vi.fn(() => ({ dispose: vi.fn(), color: 0 })),
    IcosahedronGeometry: vi.fn(() => ({ dispose: vi.fn() })),
    SphereGeometry: vi.fn(() => ({ dispose: vi.fn() })),
    Mesh: vi.fn(() => mockMesh),
    PointLight: vi.fn(() => ({ position: { set: vi.fn() } })),
    AmbientLight: vi.fn(() => ({})),
    Timer: vi.fn(() => ({ getElapsed: vi.fn(() => 0), update: vi.fn() })),
  };
});
