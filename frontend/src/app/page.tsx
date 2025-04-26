
'use client'; // Make the page a client component to manage state

import { useState, useCallback } from 'react';
import { RepoInputForm } from '@/components/repo-input-form';
import { ExecutionHistory } from '@/components/execution-history';

export default function Home() {
  // State to trigger refresh in ExecutionHistory
  const [refreshKey, setRefreshKey] = useState(0);

  // Callback function to trigger refresh
  const triggerRefresh = useCallback(() => {
    console.log('Triggering history refresh from page...');
    setRefreshKey(prevKey => prevKey + 1);
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-8 md:p-16 lg:p-24 bg-background">
      <div className="w-full max-w-6xl flex flex-col items-center space-y-12">
        <header className="text-center">
           <h1 className="text-4xl font-bold text-primary tracking-tight mb-2">
             GitDocu
           </h1>
           <p className="text-xl text-foreground/80">
             AI-Powered Git Repository Documentation
           </p>
        </header>

        {/* Pass the triggerRefresh callback to the form */}
        <RepoInputForm onJobSubmitted={triggerRefresh} />

        {/* Pass the refreshKey to ExecutionHistory to trigger re-fetching */}
        <ExecutionHistory refreshKey={refreshKey} />

      </div>
       <footer className="mt-16 text-center text-muted-foreground text-sm">
          Powered by Google ADK & Next.js
        </footer>
    </main>
  );
}
