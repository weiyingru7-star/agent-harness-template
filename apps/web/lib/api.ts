type HealthResponse = {
  status: string;
  service: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

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
