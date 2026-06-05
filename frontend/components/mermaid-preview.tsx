"use client";

import { useEffect, useId, useState } from "react";

type MermaidPreviewProps = {
  chart: string;
};

export function MermaidPreview({ chart }: MermaidPreviewProps) {
  const [svg, setSvg] = useState<string>("");
  const [error, setError] = useState<string>("");
  const uniqueId = useId().replace(/:/g, "-");

  useEffect(() => {
    let active = true;

    async function renderChart() {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({
          startOnLoad: false,
          securityLevel: "loose",
          theme: "default",
        });
        const result = await mermaid.render(`mermaid-${uniqueId}`, chart);
        if (!active) {
          return;
        }
        setSvg(result.svg);
        setError("");
      } catch (renderError) {
        if (!active) {
          return;
        }
        setError(
          renderError instanceof Error
            ? renderError.message
            : "Mermaid chart rendering failed.",
        );
      }
    }

    void renderChart();

    return () => {
      active = false;
    };
  }, [chart, uniqueId]);

  if (error) {
    return (
      <div className="mermaid-fallback">
        <p className="helper-text">図の描画に失敗したため、コード表示に切り替えています。</p>
        <pre className="code-block">{chart}</pre>
      </div>
    );
  }

  if (!svg) {
    return <p className="helper-text">図を描画しています...</p>;
  }

  return (
    <div
      className="mermaid-diagram"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
