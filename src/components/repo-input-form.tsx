
'use client';

import type * as React from 'react';
import { useState } from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Github, Loader2 } from 'lucide-react';

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

// Basic URL validation, can be refined for specific Git hosting providers
const GITHUB_REGEX =
  /^(?:https?:\/\/)?(?:www\.)?github\.com\/[a-zA-Z0-9-]+\/[a-zA-Z0-9_.-]+(?:\.git)?$/;

const formSchema = z.object({
  repoUrl: z
    .string()
    .min(1, { message: 'Repository URL is required.' })
    .regex(GITHUB_REGEX, {
      message: 'Please enter a valid GitHub repository URL (e.g., https://github.com/user/repo).',
    }),
});

// Removed RepoInputFormProps type as onDocumentationStart is no longer needed
// type RepoInputFormProps = {
//   onDocumentationStart?: (repoUrl: string) => Promise<void>;
// };

export function RepoInputForm(/* Removed props: { onDocumentationStart } */) {
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
      console.log('Submitting repo URL:', values.repoUrl);

      // Call the server action directly
      await startDocumentationProcess(values.repoUrl);

      toast({
        title: 'Documentation Started',
        description: `Processing documentation for ${values.repoUrl}. Check history for updates.`,
      });
      form.reset(); // Reset form on successful submission
    } catch (error) {
      console.error('Error starting documentation:', error);
      const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred.';
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to start documentation process: ${errorMessage}`,
      });
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="w-full max-w-lg shadow-md">
       <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Github className="h-6 w-6 text-primary" />
          Document Repository
        </CardTitle>
         <CardDescription>
           Enter a GitHub repository URL to start the automated documentation process.
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
                  <FormLabel htmlFor="repoUrl">GitHub Repository URL</FormLabel>
                  <FormControl>
                    <Input
                      id="repoUrl"
                      placeholder="https://github.com/username/repository-name"
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
                  Starting...
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
