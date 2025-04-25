
'use client';

import type * as React from 'react';
import { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TableCaption,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDistanceToNow } from 'date-fns'; // For relative time

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ExecutionHistoryItem {
  id: string;
  repoUrl: string;
  startTime: Date;
  endTime?: Date;
  status: ExecutionStatus;
  details?: string; // e.g., error message or summary
}

// Mock data for demonstration
const MOCK_HISTORY: ExecutionHistoryItem[] = [
  {
    id: 'exec-1',
    repoUrl: 'https://github.com/example/repo1',
    startTime: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
    status: 'running',
  },
  {
    id: 'exec-2',
    repoUrl: 'https://github.com/test/another-repo',
    startTime: new Date(Date.now() - 30 * 60 * 1000), // 30 minutes ago
    endTime: new Date(Date.now() - 25 * 60 * 1000), // 5 minutes later
    status: 'completed',
    details: 'Documentation generated successfully. 5 files processed.',
  },
  {
    id: 'exec-3',
    repoUrl: 'https://github.com/org/project-alpha',
    startTime: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
    endTime: new Date(Date.now() - 1 * 60 * 60 * 1000 - 50 * 60 * 1000), // 10 mins later
    status: 'failed',
    details: 'Error: Could not clone repository. Check permissions.',
  },
    {
    id: 'exec-4',
    repoUrl: 'https://github.com/user/new-feature',
    startTime: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), // 5 days ago
    endTime: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000 + 15 * 60 * 1000), // 15 mins later
    status: 'completed',
    details: 'Documentation generated successfully. 12 files processed.',
  },
];

// Helper to format duration
function formatDuration(start: Date, end?: Date): string {
  if (!end) return '-';
  const durationSeconds = Math.round((end.getTime() - start.getTime()) / 1000);
  if (durationSeconds < 60) return `${durationSeconds}s`;
  const durationMinutes = Math.round(durationSeconds / 60);
   if (durationMinutes < 60) return `${durationMinutes}m`;
   const durationHours = Math.round(durationMinutes / 60);
   return `${durationHours}h ${durationMinutes % 60}m`;
}

// Map status to Badge variant and Icon
const statusMap: Record<
  ExecutionStatus,
  { variant: 'default' | 'secondary' | 'destructive' | 'outline'; Icon: React.ElementType }
> = {
  pending: { variant: 'outline', Icon: Clock },
  running: { variant: 'secondary', Icon: Loader2 },
  completed: { variant: 'default', Icon: CheckCircle }, // Using default (primary) for completed
  failed: { variant: 'destructive', Icon: XCircle },
};

export function ExecutionHistory() {
  const [history, setHistory] = useState<ExecutionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching data
    setIsLoading(true);
    const timer = setTimeout(() => {
       // In a real app, you'd fetch from an API here
       // Sort by start time, newest first
      setHistory(MOCK_HISTORY.sort((a, b) => b.startTime.getTime() - a.startTime.getTime()));
      setIsLoading(false);
    }, 1000); // Simulate network delay

    return () => clearTimeout(timer);
  }, []); // Run once on mount

   // Function to periodically refresh running tasks (optional)
   useEffect(() => {
    const interval = setInterval(() => {
      // In a real app, fetch updated status for 'running' tasks
      // For demo, just force a re-render to update relative times
      setHistory(prev => [...prev]);
    }, 60 * 1000); // Refresh every minute

    return () => clearInterval(interval);
   }, []);

  const renderSkeleton = () => (
    <>
      {[...Array(3)].map((_, i) => (
        <TableRow key={`skel-${i}`}>
          <TableCell><Skeleton className="h-4 w-3/4" /></TableCell>
          <TableCell><Skeleton className="h-4 w-1/2" /></TableCell>
          <TableCell><Skeleton className="h-4 w-1/4" /></TableCell>
          <TableCell><Skeleton className="h-4 w-1/4" /></TableCell>
          <TableCell><Skeleton className="h-4 w-full" /></TableCell>
        </TableRow>
      ))}
    </>
  );

  return (
    <Card className="w-full mt-8 shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
           <Clock className="h-6 w-6 text-primary" />
           Execution History
        </CardTitle>
         <CardDescription>
           Track the progress and status of your documentation jobs.
         </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] w-full rounded-md border">
          <Table>
             {!isLoading && history.length === 0 && (
                <TableCaption>No documentation history yet. Submit a repository above to get started.</TableCaption>
             )}
             {isLoading && (
                <TableCaption>Loading history...</TableCaption>
             )}
            <TableHeader>
              <TableRow>
                <TableHead>Repository</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? renderSkeleton() : (
                history.map((item) => {
                  const { Icon, variant } = statusMap[item.status];
                  const repoName = item.repoUrl.split('/').slice(-2).join('/'); // Extract user/repo
                  return (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium truncate max-w-xs" title={item.repoUrl}>
                        {repoName}
                      </TableCell>
                      <TableCell title={item.startTime.toLocaleString()}>
                        {formatDistanceToNow(item.startTime, { addSuffix: true })}
                      </TableCell>
                      <TableCell>{formatDuration(item.startTime, item.endTime)}</TableCell>
                      <TableCell>
                        <Badge variant={variant} className="flex items-center gap-1 capitalize">
                          <Icon className={`h-3 w-3 ${item.status === 'running' ? 'animate-spin' : ''}`} />
                          {item.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-sm text-muted-foreground truncate max-w-md" title={item.details}>
                        {item.details || '-'}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
