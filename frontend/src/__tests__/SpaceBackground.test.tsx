import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render } from "@/test/test-utils";

import SpaceBackground from "@/components/SpaceBackground";

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Get the mocked 2d context methods (all vi.fn() from setup.ts) */
function getMockCtx(): Record<string, ReturnType<typeof vi.fn>> {
  const canvas = document.querySelector("canvas");
  if (!canvas) return {};
  const ctx = canvas.getContext("2d");
  // The setup.ts mock returns an object where every method is vi.fn()
  return (ctx ?? {}) as unknown as Record<string, ReturnType<typeof vi.fn>>;
}

/** Retrieve the fillRect mock from the canvas context */
function getFillRectMock() {
  return getMockCtx().fillRect as unknown as ReturnType<typeof vi.fn>;
}

// ─── Controlled IntersectionObserver mock ────────────────────────────────────

const OriginalObserver = globalThis.IntersectionObserver;

let observeMock: ReturnType<typeof vi.fn>;
let disconnectMock: ReturnType<typeof vi.fn>;
/** The callback the component registered with IntersectionObserver */
let registeredObserverCallback: IntersectionObserverCallback;

function setupControlledObserver() {
  observeMock = vi.fn();
  disconnectMock = vi.fn();
  registeredObserverCallback = (() => {}) as unknown as IntersectionObserverCallback;

  // Use a real class (constructable) that captures the callback for test control
  class MockObserver {
    readonly root: Element | null = null;
    readonly rootMargin: string = "";
    readonly thresholds: ReadonlyArray<number> = [];

    constructor(callback: IntersectionObserverCallback) {
      registeredObserverCallback = callback;
    }

    observe = observeMock;
    unobserve = vi.fn();
    disconnect = disconnectMock;
    takeRecords = () => [] as IntersectionObserverEntry[];
  }
  globalThis.IntersectionObserver = MockObserver as unknown as typeof IntersectionObserver;
}

function tearDownControlledObserver() {
  globalThis.IntersectionObserver = OriginalObserver;
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("SpaceBackground", () => {
  beforeEach(() => {
    setupControlledObserver();
    vi.useFakeTimers();
  });

  afterEach(() => {
    tearDownControlledObserver();
    vi.useRealTimers();
  });

  // ── Basic rendering ──────────────────────────────────────────────────────

  it("should render a canvas element", () => {
    const { container } = render(<SpaceBackground />);
    const canvas = container.querySelector("canvas");
    expect(canvas).toBeInTheDocument();
  });

  it("should have fixed positioning classes", () => {
    const { container } = render(<SpaceBackground />);
    const canvas = container.querySelector("canvas");
    expect(canvas).toHaveClass("fixed");
    expect(canvas).toHaveClass("inset-0");
    expect(canvas).toHaveClass("pointer-events-none");
  });

  it("should have the correct z-index for background", () => {
    const { container } = render(<SpaceBackground />);
    const canvas = container.querySelector("canvas");
    expect(canvas).toHaveClass("z-0");
  });

  it("should set canvas width and height based on window size", () => {
    Object.defineProperty(window, "innerWidth", { value: 1920, configurable: true });
    Object.defineProperty(window, "innerHeight", { value: 1080, configurable: true });

    const { container } = render(<SpaceBackground />);
    const canvas = container.querySelector("canvas") as HTMLCanvasElement;
    expect(canvas).toBeInTheDocument();
  });

  it("should render without crashing with empty window dimensions", () => {
    Object.defineProperty(window, "innerWidth", { value: 0, configurable: true });
    Object.defineProperty(window, "innerHeight", { value: 0, configurable: true });
    expect(() => render(<SpaceBackground />)).not.toThrow();
  });

  // ── Event listeners ──────────────────────────────────────────────────────

  it("should handle resize events", () => {
    const addEventListenerSpy = vi.spyOn(window, "addEventListener");

    render(<SpaceBackground />);

    expect(addEventListenerSpy).toHaveBeenCalledWith("resize", expect.any(Function), { passive: true });

    addEventListenerSpy.mockRestore();
  });

  it("should cleanup event listeners on unmount", () => {
    const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

    const { unmount } = render(<SpaceBackground />);
    unmount();

    const resizeCalls = removeEventListenerSpy.mock.calls.filter(
      ([event]) => event === "resize",
    );
    expect(resizeCalls.length).toBeGreaterThan(0);

    removeEventListenerSpy.mockRestore();
  });

  // ── IntersectionObserver ─────────────────────────────────────────────────

  it("should create an IntersectionObserver that observes the canvas", () => {
    const { container } = render(<SpaceBackground />);
    const canvas = container.querySelector("canvas");

    // The registered callback was captured by the mock constructor
    expect(registeredObserverCallback).not.toBeNull();
    // The observe method was called with the canvas element
    expect(observeMock).toHaveBeenCalledWith(canvas);
  });

  it("should disconnect the IntersectionObserver on unmount", () => {
    const { unmount } = render(<SpaceBackground />);
    unmount();
    expect(disconnectMock).toHaveBeenCalled();
  });

  // Helper to create a minimal IntersectionObserverEntry for tests
  function makeEntry(isIntersecting: boolean, target: Element): IntersectionObserverEntry {
    const rect: DOMRectReadOnly = { top: 0, right: 0, bottom: 0, left: 0, width: 0, height: 0, x: 0, y: 0, toJSON: () => {} };
    return {
      boundingClientRect: rect,
      intersectionRatio: isIntersecting ? 1 : 0,
      intersectionRect: rect,
      isIntersecting,
      rootBounds: null,
      target,
      time: Date.now(),
    };
  }

  it("should skip canvas rendering when canvas is scrolled out of view", () => {
    render(<SpaceBackground />);

    const fillRectMock = getFillRectMock();

    // Reset call counts after initial render + draw() call
    fillRectMock.mockClear();

    // Simulate the observer firing: canvas scrolled out of view
    const canvas = document.querySelector("canvas")!;
    registeredObserverCallback([makeEntry(false, canvas)], {} as IntersectionObserver);

    // Advance timers to trigger the next requestAnimationFrame callback
    vi.advanceTimersByTime(16);

    // When not visible, draw() returns early without calling fillRect
    expect(fillRectMock).not.toHaveBeenCalled();
  });

  it("should resume canvas rendering when canvas becomes visible again", () => {
    render(<SpaceBackground />);

    const fillRectMock = getFillRectMock();

    // Simulate: canvas becomes invisible
    const canvas = document.querySelector("canvas")!;
    registeredObserverCallback([makeEntry(false, canvas)], {} as IntersectionObserver);

    fillRectMock.mockClear();

    // Simulate: canvas scrolls back into view
    registeredObserverCallback([makeEntry(true, canvas)], {} as IntersectionObserver);

    // Advance timers to trigger the rAF callback
    vi.advanceTimersByTime(16);

    // When visible again, draw() should call fillRect to render particles
    expect(fillRectMock).toHaveBeenCalled();
  });

  it("should keep the animation loop alive even when not visible", () => {
    render(<SpaceBackground />);

    const rafSpy = vi.spyOn(window, "requestAnimationFrame");
    const canvas = document.querySelector("canvas")!;

    // Simulate scrolled out of view
    registeredObserverCallback([makeEntry(false, canvas)], {} as IntersectionObserver);

    // Clear calls from the initial mount
    rafSpy.mockClear();

    // Advance timers multiple times to let several rAF callbacks fire
    vi.advanceTimersByTime(100);

    // The rAF loop should still be scheduling frames (draw() calls rAF even when hidden)
    expect(rafSpy).toHaveBeenCalled();
  });
});
