import Link from "next/link";
import { notFound } from "next/navigation";

import { FileUploadForm } from "@/app/runs/[runId]/file-upload-form";
import { getRun, getRunArtifacts, getRunEvents } from "@/lib/api";

type RunPageProps = {
  params: {
    runId: string;
  };
};

export default async function RunPage({ params }: RunPageProps) {
  const run = await getRun(params.runId);
  if (!run) {
    notFound();
  }

  const events = await getRunEvents(params.runId);
  const artifacts = await getRunArtifacts(params.runId);

  return (
    <main>
      <div className="shell">
        <section className="header">
          <div>
            <Link className="text-link" href="/">
              Back to runs
            </Link>
            <h1 className="title">Run Detail</h1>
            <p className="subtitle">{run.id}</p>
          </div>
          <div className="status">
            <p className="status-label">Run status</p>
            <p className="status-value">{run.status}</p>
          </div>
        </section>

        <section className="section">
          <div className="section-heading">
            <h2>Task</h2>
          </div>
          <div className="detail-block">{run.task.input}</div>
        </section>

        <section className="section">
          <div className="section-heading">
            <h2>Steps</h2>
          </div>
          <div className="stack">
            {run.steps.map((step) => (
              <article className="panel compact" key={step.id}>
                <div className="split-row">
                  <h3>{step.name}</h3>
                  <span className="badge">{step.status}</span>
                </div>
                <p>{step.output ?? "No output yet."}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="section">
          <div className="section-heading">
            <h2>Output</h2>
          </div>
          <div className="detail-block">{run.output ?? "No output yet."}</div>
        </section>

        <section className="section">
          <div className="section-heading">
            <h2>Artifacts</h2>
            <p>Upload .txt or .md files as run artifacts.</p>
          </div>
          <FileUploadForm runId={run.id} />
          <div className="stack spaced">
            {artifacts.length === 0 ? (
              <div className="detail-block muted-block">No artifacts yet.</div>
            ) : (
              artifacts.map((artifact) => (
                <article className="panel compact" key={artifact.id}>
                  <div className="split-row">
                    <h3>{artifact.name}</h3>
                    <span className="badge">{artifact.kind}</span>
                  </div>
                  <p className="artifact-meta">File: {artifact.file_id}</p>
                  <p>{artifact.text}</p>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="section">
          <div className="section-heading">
            <h2>Events</h2>
          </div>
          <ol className="event-list">
            {events.map((event) => (
              <li key={`${event.type}-${event.created_at}`}>
                <span>{event.type}</span>
                <p>{event.message}</p>
              </li>
            ))}
          </ol>
        </section>
      </div>
    </main>
  );
}
