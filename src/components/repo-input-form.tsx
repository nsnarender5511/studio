
'use client';

import type * as React from 'react';
import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Github, Loader2, FolderGit2 } from 'lucide-react'; // Added FolderGit2

import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { startDocumentationProcess } from '@/app/actions'; // Import the server action

// Allow local paths for demonstration, adjust validation as needed
// Basic check for something that looks like a path or a git URL
// WARNING: This is very basic and doesn't guarantee a valid repo/path.
// More robust validation (e.g., checking for `.git` suffix for URLs) might be needed.
const formSchema = z.object({
  repoUrl: z
    .string()
    .min(1, { message: 'Repository URL or local path is required.' })
    // Example: Allows common Git URLs and basic paths (absolute or relative)
    // This regex is permissive and mainly checks for non-empty string.
    .refine(value => value.trim().length > 0, {
        message: "Repository URL or local path cannot be empty."
    }),
    // .regex(/^(?:https?:\/\/|git@)?(?:[\w.-]+@)?[\w.-]+\/[\w.-]+\/?(?:\.git)?$|^[\\\/a-zA-Z0-9_\-.]+$/, {
    //   message: 'Please enter a valid Git repository URL or a local path.',
    // }),
});


export function RepoInputForm() {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      repoUrl: '',
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true);
    try {
      const repoInput = values.repoUrl;
      console.log('Submitting repo input:', repoInput);

      // Call the server action directly
      const result = await startDocumentationProcess(repoInput);

      if ('error' in result) {
          throw new Error(result.error); // Throw error to be caught below
      }

      // Handle success
      toast({
        title: 'Documentation Job Submitted',
        description: `Processing started for ${repoInput}. Job ID: ${result.job_id}. Check history below for updates.`,
        duration: 5000, // Show for 5 seconds
      });
      form.reset(); // Reset form on successful submission

      // TODO: Trigger a refresh of the history table (e.g., via a shared state or context)
      // This requires lifting state up or using a state management library.
      // For now, the user needs to manually wait or refresh.

    } catch (error) {
      console.error('Error submitting documentation job:', error);
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.';
      toast({
        variant: 'destructive',
        title: 'Submission Failed',
        description: `${errorMessage}`,
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-lg shadow-md">
       <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {/* Use appropriate icon based on input? Maybe too complex. Stick with generic repo icon */}
          <FolderGit2 className="h-6 w-6 text-primary" />
          Document Repository
        </CardTitle>
         <CardDescription>
           Enter a GitHub repository URL or a local path to start the automated documentation process.
         </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="repoUrl"
              render={({ field }) => (
                <FormItem>
                  <FormLabel htmlFor="repoUrl">Repository URL or Local Path</FormLabel>
                  <FormControl>
                    <Input
                      id="repoUrl"
                      placeholder="https://github.com/user/repo or /path/to/local/repo"
                      {...field}
                      aria-describedby="repoUrl-message"
                      disabled={isLoading}
                    />
                  </FormControl>
                  <FormMessage id="repoUrl-message" />
                </FormItem>
              )}
            />
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                'Generate Documentation'
              )}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
