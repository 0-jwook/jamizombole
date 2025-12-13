'use client';

import React from 'react';
import { useServerInsertedHTML } from 'next/navigation';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';

// This implementation is taken from the official emotion documentation for Next.js App Router.
// It ensures that emotion styles are correctly extracted and rendered on the server.
export default function StyledComponentsRegistry({ children }: { children: React.ReactNode }) {
  const cache = React.useMemo(() => {
    const cache = createCache({ key: 'css', prepend: true });
    cache.compat = true;
    return cache;
  }, []);

  useServerInsertedHTML(() => {
    return (
      <style
        data-emotion={`${cache.key} ${Object.keys(cache.inserted).join(' ')}`}
        dangerouslySetInnerHTML={{
          __html: Object.values(cache.inserted).join(' '),
        }}
      />
    );
  });

  return (
    <CacheProvider value={cache}>
      {children}
    </CacheProvider>
  );
}
