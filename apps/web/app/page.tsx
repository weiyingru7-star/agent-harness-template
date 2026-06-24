import { getHealth } from "@/lib/api";

export default async function Home() {
  const health = await getHealth();
  const isHealthy = health?.status === "ok";

  return (
    <main>
      <div className="shell">
        <section className="header">
          <div>
            <h1 className="title">Agent Harness Template</h1>
            <p className="subtitle">
              A business-agnostic foundation for building reusable agent
              applications. Stage 1 only verifies the app skeleton and service
              health.
            </p>
          </div>
          <div className="status">
            <p className="status-label">API health</p>
            <p className="status-value">{isHealthy ? "ok" : "unavailable"}</p>
          </div>
        </section>

        <section className="grid">
          <article className="panel">
            <h2>Frontend</h2>
            <p>Next.js app shell with a minimal homepage.</p>
          </article>
          <article className="panel">
            <h2>Backend</h2>
            <p>FastAPI service with a single health endpoint.</p>
          </article>
          <article className="panel">
            <h2>Infrastructure</h2>
            <p>PostgreSQL and Redis are available through Docker Compose.</p>
          </article>
        </section>
      </div>
    </main>
  );
}
