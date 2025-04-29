/**
 * Type declarations for MSW
 * This file provides type definitions for MSW to avoid TypeScript errors
 */

declare module 'msw' {
  export interface ResponseResolver {
    (req: any, res: any, ctx: any): any;
  }

  export const rest: {
    get: (url: string, resolver: ResponseResolver) => any;
    post: (url: string, resolver: ResponseResolver) => any;
    put: (url: string, resolver: ResponseResolver) => any;
    delete: (url: string, resolver: ResponseResolver) => any;
    patch: (url: string, resolver: ResponseResolver) => any;
    options: (url: string, resolver: ResponseResolver) => any;
  };

  export const setupWorker: (...handlers: any[]) => {
    start: (options?: any) => Promise<any>;
    stop: () => Promise<any>;
    resetHandlers: (...handlers: any[]) => void;
    use: (...handlers: any[]) => void;
  };
}

declare module 'msw/node' {
  export const setupServer: (...handlers: any[]) => {
    listen: (callback?: () => void) => void;
    close: () => void;
    resetHandlers: (...handlers: any[]) => void;
    use: (...handlers: any[]) => void;
  };
}

declare module '@testing-library/react-hooks' {
  export function renderHook<P, R>(
    callback: (props: P) => R,
    options?: {
      initialProps?: P;
      wrapper?: React.ComponentType<any>;
    }
  ): {
    result: { current: R };
    waitForNextUpdate: () => Promise<void>;
    rerender: (props?: P) => void;
    unmount: () => void;
  };
}
