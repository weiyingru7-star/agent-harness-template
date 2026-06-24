type HealthResponse = {
  status: string;
  service: string;
};

export type Task = {
  id: string;
  input: string;
  created_at: string;
};

export type Step = {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  output: string | null;
  created_at: string;
  completed_at: string | null;
};

export type Run = {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  task: Task;
  steps: Step[];
  output: string | null;
  created_at: string;
  completed_at: string | null;
};

export type RunEvent = {
  type: string;
  message: string;
  created_at: string;
};

export type UploadedFile = {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  extension: string;
  storage_path: string;
  text: string;
  created_at: string;
};

export type Artifact = {
  id: string;
  run_id: string;
  file_id: string;
  name: string;
  kind: "text";
  text: string;
  created_at: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8005";

export async function getHealth(): Promise<HealthResponse | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/health`, {
      cache: "no-store",
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export async function createRun(input: string): Promise<Run> {
  const response = await fetch(`${apiBaseUrl}/api/runs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ input }),
  });

  if (!response.ok) {
    throw new Error("Failed to create run");
  }

  return response.json();
}

export async function getRun(runId: string): Promise<Run | null> {
  const response = await fetch(`${apiBaseUrl}/api/runs/${runId}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Failed to load run");
  }

  return response.json();
}

export async function getRunEvents(runId: string): Promise<RunEvent[]> {
  const response = await fetch(`${apiBaseUrl}/api/runs/${runId}/events`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}

export async function uploadFile(file: File): Promise<UploadedFile> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${apiBaseUrl}/api/files/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload file");
  }

  return response.json();
}

export async function createArtifact(
  runId: string,
  fileId: string,
  name: string,
): Promise<Artifact> {
  const response = await fetch(`${apiBaseUrl}/api/runs/${runId}/artifacts`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ file_id: fileId, name }),
  });

  if (!response.ok) {
    throw new Error("Failed to create artifact");
  }

  return response.json();
}

export async function getRunArtifacts(runId: string): Promise<Artifact[]> {
  const response = await fetch(`${apiBaseUrl}/api/runs/${runId}/artifacts`, {
    cache: "no-store",
  });

  if (!response.ok) {
    return [];
  }

  return response.json();
}
