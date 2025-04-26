'use server';

const BACKEND_URL = process.env.BACKEND_API_URL || 'http://127.0.0.1:5001'; // Default backend URL

// This is the server action that will be called from the client component.
export async function startDocumentationProcess(repoUrl: string): Promise<{ job_id: string } | { error: string }> {
  console.log(`[Server Action] Triggering backend documentation for: ${repoUrl}`);

  try {
    const response = await fetch(`${BACKEND_URL}/document`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ repoUrl }), // Send repoUrl in the body
      cache: 'no-store', // Ensure fresh request
    });

    const result = await response.json();

    if (!response.ok) {
      // If response is not OK, throw an error with the message from the backend
      console.error(`Backend Error (${response.status}): ${result.error || 'Unknown error'}`);
      return { error: `Backend Error: ${result.error || response.statusText || 'Failed to start process'}` };
    }

    console.log('[Server Action] Backend responded:', result);
    // Assuming the backend returns { job_id: "...", status: "...", message: "..." } on success (202)
    if (result.job_id) {
       return { job_id: result.job_id };
    } else {
       console.error('Backend did not return a job_id');
       return { error: 'Backend did not return a job ID.' };
    }

  } catch (error) {
    console.error('[Server Action] Error calling backend:', error);
     const errorMessage = error instanceof Error ? error.message : 'Network error or backend unreachable.';
     // Check for fetch-specific errors like ECONNREFUSED
     if (errorMessage.includes('ECONNREFUSED') || errorMessage.includes('fetch failed')) {
        return { error: `Could not connect to the backend service at ${BACKEND_URL}. Is it running?` };
     }
     return { error: `Failed to communicate with backend: ${errorMessage}` };
  }
}


// --- New Server Actions for History/Status ---

export type ExecutionStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ExecutionHistoryItem {
  job_id: string; // Matches backend field name
  repo_url: string; // Matches backend field name
  start_time: string; // Keep as string for transfer
  end_time?: string; // Keep as string for transfer
  status: ExecutionStatus;
  details?: string;
  final_state_summary?: {
     documentation_plan?: any[]; // Adjust types as needed
     summary_status?: string;
  };
}


export async function fetchExecutionHistory(): Promise<ExecutionHistoryItem[] | { error: string }> {
  console.log('[Server Action] Fetching execution history from backend');
  try {
    const response = await fetch(`${BACKEND_URL}/history`, {
       method: 'GET',
       cache: 'no-store', // Ensure fresh data
    });
    const data = await response.json();

    if (!response.ok) {
       console.error(`Backend Error (${response.status}): ${data.error || 'Unknown error'}`);
       return { error: `Backend Error: ${data.error || response.statusText || 'Failed to fetch history'}` };
    }

    // Basic validation if needed
    if (!Array.isArray(data)) {
        console.error('Backend returned non-array for history:', data);
        return { error: 'Invalid history format received from backend.' };
    }

    // Convert snake_case from Python to camelCase for TypeScript if necessary
    // Or adjust the frontend component to expect snake_case
    // For simplicity, let's assume the component handles snake_case for now.
    return data as ExecutionHistoryItem[];

  } catch (error) {
    console.error('[Server Action] Error fetching history:', error);
    const errorMessage = error instanceof Error ? error.message : 'Network error or backend unreachable.';
    if (errorMessage.includes('ECONNREFUSED') || errorMessage.includes('fetch failed')) {
       return { error: `Could not connect to the backend service at ${BACKEND_URL}. Is it running?` };
    }
    return { error: `Failed to fetch history: ${errorMessage}` };
  }
}

export async function fetchJobStatus(jobId: string): Promise<ExecutionHistoryItem | { error: string }> {
  console.log(`[Server Action] Fetching status for job: ${jobId}`);
   if (!jobId) return { error: 'Job ID is required.'};

  try {
    const response = await fetch(`${BACKEND_URL}/status/${jobId}`, {
      method: 'GET',
      cache: 'no-store', // Ensure fresh data
    });
    const data = await response.json();

    if (!response.ok) {
       console.error(`Backend Error (${response.status}): ${data.error || 'Unknown error'}`);
       if (response.status === 404) {
           return { error: `Job with ID ${jobId} not found.` };
       }
       return { error: `Backend Error: ${data.error || response.statusText || 'Failed to fetch status'}` };
    }

     // Assume data matches ExecutionHistoryItem structure (with snake_case)
    return data as ExecutionHistoryItem;

  } catch (error) {
    console.error('[Server Action] Error fetching job status:', error);
    const errorMessage = error instanceof Error ? error.message : 'Network error or backend unreachable.';
     if (errorMessage.includes('ECONNREFUSED') || errorMessage.includes('fetch failed')) {
        return { error: `Could not connect to the backend service at ${BACKEND_URL}. Is it running?` };
     }
    return { error: `Failed to fetch status for job ${jobId}: ${errorMessage}` };
  }
}
