import { getHealth } from "@/lib/api";
import { RunForm } from "@/app/run-form";

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
              applications. Stage 2 adds a minimal mock run path for the
              demo_agent module.
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
            <p>Submit a task and inspect the resulting run.</p>
          </article>
          <article className="panel">
            <h2>Backend</h2>
            <p>FastAPI exposes health and minimal run endpoints.</p>
          </article>
          <article className="panel">
            <h2>Infrastructure</h2>
            <p>PostgreSQL and Redis are available through Docker Compose.</p>
          </article>
        </section>

        <section className="section">
          <div className="section-heading">
            <h2>Start A Run</h2>
            <p>demo_agent returns a mock response without calling an external model.</p>
          </div>
          <RunForm />
        </section>
      </div>
    </main>
  );
}
