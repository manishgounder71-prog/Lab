import React, { type ReactElement } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { CommandCenterProvider } from "@/context/CommandCenterContext";

/**
 * Wrapper that provides CommandCenter context to tests
 */
function AllTheProviders({ children }: { children: React.ReactNode }) {
  return <CommandCenterProvider>{children}</CommandCenterProvider>;
}

/**
 * Custom render with providers
 */
function customRender(
  ui: ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) {
  return render(ui, { wrapper: AllTheProviders, ...options });
}

export * from "@testing-library/react";
export { customRender as render };
