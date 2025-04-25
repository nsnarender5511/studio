
import { RepoInputForm } from '@/components/repo-input-form';
import { ExecutionHistory } from '@/components/execution-history';

// startDocumentationProcess function removed, it will be handled by a server action.

export default function Home() {
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

        {/* Repository Input Form - Removed onDocumentationStart prop */}
        <RepoInputForm />

        {/* Execution History Table */}
        <ExecutionHistory />

      </div>
       <footer className="mt-16 text-center text-muted-foreground text-sm">
          Powered by Google ADK & Next.js
        </footer>
    </main>
  );
}
