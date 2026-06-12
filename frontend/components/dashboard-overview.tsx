import { AppBuilder } from "./app-builder";

export function DashboardOverview() {
  return (
    <div className="stack">
      <section className="hero">
        <span className="badge">MVP Workspace</span>
        <h1>AI BizOps Orchestrator</h1>
        <p>
          このプロダクトは、社内業務の流れを自然文から読み取り、非効率な作業や連携不足を見つけて、
          改善案と業務接続設計図、実装イメージまで見える化するための分析ワークスペースです。
        </p>
      </section>

      <AppBuilder />
    </div>
  );
}
