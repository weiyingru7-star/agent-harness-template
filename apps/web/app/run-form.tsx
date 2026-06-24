"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createRun } from "@/lib/api";

export function RunForm() {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput) {
      setError("Enter a task before starting a run.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const run = await createRun(trimmedInput);
      router.push(`/runs/${run.id}`);
    } catch {
      setError("Could not create a run. Check that the API is available.");
      setIsSubmitting(false);
    }
  }

  return (
    <form className="run-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="task-input">
        Task
      </label>
      <textarea
        id="task-input"
        className="task-input"
        value={input}
        onChange={(event) => setInput(event.target.value)}
        placeholder="Describe a task for demo_agent"
        rows={5}
      />
      <div className="form-row">
        <button className="button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Starting..." : "Start run"}
        </button>
        {error ? <p className="form-error">{error}</p> : null}
      </div>
    </form>
  );
}
