
'use client';

import type * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { Clock, CheckCircle, XCircle, Loader2, AlertTriangle } from 'lucide-react'; // Use AlertTriangle for errors
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
import { Button } from '@/components/ui/button'; // For refresh button
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'; // For tooltips
import { formatDistanceToNow, parseISO } from 'date-fns'; // parseISO for string dates

// Import server actions and types
import { fetchExecutionHistory, fetchJobStatus, type ExecutionHistoryItem, type ExecutionStatus } from '@/app/actions';
import { useToast } from '@/hooks/use-toast';


// Helper to format duration (handles string dates from backend)
function formatDuration(startStr: string, endStr?: string): string {
  try {
    const start = parseISO(startStr);
    if (!endStr) {
        // Calculate duration from start to now if still running or pending
        const now = new Date();
        const durationSeconds = Math.round((now.getTime() - start.getTime()) / 1000);
        if (durationSeconds < 0) return '-'; // Avoid negative duration if clocks are slightly off
        if (durationSeconds < 60) return `${durationSeconds}s`;
        const durationMinutes = Math.floor(durationSeconds / 60);
        if (durationMinutes < 60) return `${durationMinutes}m ${durationSeconds % 60}s`;
        const durationHours = Math.floor(durationMinutes / 60);
        return `${durationHours}h ${durationMinutes % 60}m`;
    }
    const end = parseISO(endStr);
    const durationSeconds = Math.round((end.getTime() - start.getTime()) / 1000);
    if (durationSeconds < 0) return '-';
    if (durationSeconds < 60) return `${durationSeconds}s`;
    const durationMinutes = Math.floor(durationSeconds / 60);
    if (durationMinutes < 60) return `${durationMinutes}m ${durationSeconds % 60}s`;
    const durationHours = Math.floor(durationMinutes / 60);
    return `${durationHours}h ${durationMinutes % 60}m`;
  } catch (e) {
    console.error("Error parsing date for duration:", e);
    return '-';
  }
}

// Format start time string nicely
function formatStartTime(startStr: string): string {
    try {
        const start = parseISO(startStr);
        // Check if the date is recent (e.g., within last 7 days) for relative time
        if (new Date().getTime() - start.getTime() < 7 * 24 * 60 * 60 * 1000) {
            return formatDistanceToNow(start, { addSuffix: true });
        }
        // Otherwise, show absolute date/time
        return start.toLocaleString();
    } catch(e) {
        console.error("Error parsing start time:", e);
        return startStr; // Return original string if parsing fails
    }
}


// Map status to Badge variant and Icon
const statusMap: Record<
  ExecutionStatus,
  { variant: 'default' | 'secondary' | 'destructive' | 'outline'; Icon: React.ElementType }
> = {
  pending: { variant: 'outline', Icon: Clock },
  running: { variant: 'secondary', Icon: Loader2 },
  completed: { variant: 'default', Icon: CheckCircle }, // Using default (primary/teal) for completed
  failed: { variant: 'destructive', Icon: XCircle },
};

const POLLING_INTERVAL_MS = 5000; // Poll every 5 seconds

export function ExecutionHistory() {
  const [history, setHistory] = useState<ExecutionHistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const loadHistory = useCallback(async (showLoading = true) => {
    if (showLoading) setIsLoading(true);
    setError(null);
    const result = await fetchExecutionHistory();
    if ('error' in result) {
      setError(result.error);
      toast({
        variant: 'destructive',
        title: 'Failed to Load History',
        description: result.error,
      });
    } else {
      setHistory(result); // Assuming backend returns sorted data
    }
    if (showLoading) setIsLoading(false);
  }, [toast]); // Added toast dependency

  // Initial load
  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

   // Polling mechanism for running jobs
  useEffect(() => {
    const runningJobIds = history.filter(job => job.status === 'running').map(job => job.job_id);

    if (runningJobIds.length === 0) {
      return; // No need to poll if no jobs are running
    }

    const intervalId = setInterval(async () => {
        console.log("Polling for status updates...", runningJobIds);
        let historyUpdated = false;
        for (const jobId of runningJobIds) {
            const statusResult = await fetchJobStatus(jobId);
            if (!('error' in statusResult)) {
                 // Update the specific job in the history state
                 setHistory(prevHistory => {
                     const updated = prevHistory.map(job =>
                         job.job_id === jobId ? statusResult : job
                     );
                     // Check if the status actually changed to avoid unnecessary re-renders if polling is fast
                     const oldJob = prevHistory.find(j => j.job_id === jobId);
                     if (oldJob?.status !== statusResult.status) {
                         historyUpdated = true;
                         if (statusResult.status === 'completed' || statusResult.status === 'failed') {
                             toast({
                                 title: `Job ${statusResult.status.toUpperCase()}`,
                                 description: `Job for ${statusResult.repo_url.split('/').slice(-2).join('/')} finished.`,
                             });
                         }
                     }
                     return updated;
                 });
            } else {
                // Handle error fetching status for a specific job (e.g., log it)
                console.warn(`Polling failed for job ${jobId}: ${statusResult.error}`);
            }
        }
         // Optional: If any job finished, trigger a full history reload
        // if (historyUpdated && history.some(job => job.job_id && runningJobIds.includes(job.job_id) && (job.status === 'completed' || job.status === 'failed'))) {
        //    loadHistory(false); // Reload full history without showing loading indicator
        // }

    }, POLLING_INTERVAL_MS);

    // Cleanup function to clear the interval when the component unmounts
    // or when the list of running jobs changes
    return () => clearInterval(intervalId);
  }, [history, toast]); // Rerun effect if history changes (e.g., job status updates)

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
       <CardHeader className="flex flex-row items-center justify-between">
         <div>
             <CardTitle className="flex items-center gap-2">
               <Clock className="h-6 w-6 text-primary" />
               Execution History
             </CardTitle>
             <CardDescription>
               Track the progress and status of your documentation jobs. Running jobs update automatically.
             </CardDescription>
         </div>
         <Button variant="outline" size="sm" onClick={() => loadHistory(true)} disabled={isLoading}>
             <Loader2 className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : 'hidden'}`} />
            Refresh
          </Button>
      </CardHeader>
      <CardContent>
         {error && (
             <div className="flex items-center justify-center p-4 text-destructive bg-destructive/10 rounded-md border border-destructive/30">
                 <AlertTriangle className="h-5 w-5 mr-2" />
                 <span>Error loading history: {error}</span>
            </div>
         )}
        <ScrollArea className={`h-[400px] w-full rounded-md border ${error ? 'mt-4' : ''}`}>
         <TooltipProvider>
          <Table>
             {(isLoading && history.length === 0) && (
                <TableCaption>Loading history...</TableCaption>
             )}
             {(!isLoading && !error && history.length === 0) && (
                <TableCaption>No documentation history yet. Submit a repository above.</TableCaption>
             )}
            <TableHeader>
              <TableRow>
                <TableHead>Repository / Path</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading && history.length === 0 ? renderSkeleton() : (
                history.map((item) => {
                  const { Icon, variant } = statusMap[item.status] || statusMap.pending; // Default to pending if status unknown
                  const repoName = item.repo_url.includes('/')
                        ? item.repo_url.split('/').slice(-2).join('/') // Extract user/repo for URL
                        : item.repo_url; // Show full path if local

                  return (
                    <TableRow key={item.job_id}>
                       <TableCell className="font-medium truncate max-w-xs">
                         <Tooltip>
                           <TooltipTrigger asChild>
                             <span>{repoName}</span>
                           </TooltipTrigger>
                           <TooltipContent>
                             <p>{item.repo_url}</p>
                           </TooltipContent>
                         </Tooltip>
                       </TableCell>
                       <TableCell>
                         <Tooltip>
                           <TooltipTrigger asChild>
                               <span>{formatStartTime(item.start_time)}</span>
                            </TooltipTrigger>
                           <TooltipContent>
                             <p>{new Date(item.start_time).toLocaleString()}</p>
                           </TooltipContent>
                         </Tooltip>
                        </TableCell>
                      <TableCell>{formatDuration(item.start_time, item.end_time)}</TableCell>
                      <TableCell>
                        <Badge variant={variant} className="flex items-center gap-1 capitalize">
                          <Icon className={`h-3 w-3 ${item.status === 'running' ? 'animate-spin' : ''}`} />
                          {item.status}
                        </Badge>
                      </TableCell>
                       <TableCell className="text-sm text-muted-foreground truncate max-w-md">
                         <Tooltip>
                             <TooltipTrigger asChild>
                                 <span>{item.details || '-'}</span>
                             </TooltipTrigger>
                            {item.details && ( // Only show tooltip if there are details
                                 <TooltipContent>
                                     <p className="max-w-xs whitespace-normal">{item.details}</p>
                                 </TooltipContent>
                             )}
                         </Tooltip>
                        </TableCell>
                    </TableRow>
                  );
                })
              )}
               {/* Show skeleton rows below existing data when refreshing */}
               {isLoading && history.length > 0 && renderSkeleton()}
            </TableBody>
          </Table>
          </TooltipProvider>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
