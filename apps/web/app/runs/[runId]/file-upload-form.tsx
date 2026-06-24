"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createArtifact, uploadFile } from "@/lib/api";

type FileUploadFormProps = {
  runId: string;
};

export function FileUploadForm({ runId }: FileUploadFormProps) {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a .txt or .md file.");
      return;
    }

    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (extension !== ".txt" && extension !== ".md") {
      setError("Only .txt and .md files are supported.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const uploadedFile = await uploadFile(file);
      await createArtifact(runId, uploadedFile.id, name.trim() || file.name);
      setFile(null);
      setName("");
      router.refresh();
    } catch {
      setError("Could not upload the file.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="run-form" onSubmit={handleSubmit}>
      <label className="field-label" htmlFor="artifact-file">
        Text file
      </label>
      <input
        id="artifact-file"
        accept=".txt,.md"
        className="file-input"
        onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        type="file"
      />
      <label className="field-label" htmlFor="artifact-name">
        Artifact name
      </label>
      <input
        id="artifact-name"
        className="text-input"
        onChange={(event) => setName(event.target.value)}
        placeholder="Optional display name"
        type="text"
        value={name}
      />
      <div className="form-row">
        <button className="button" disabled={isSubmitting} type="submit">
          {isSubmitting ? "Uploading..." : "Upload artifact"}
        </button>
        {error ? <p className="form-error">{error}</p> : null}
      </div>
    </form>
  );
}
