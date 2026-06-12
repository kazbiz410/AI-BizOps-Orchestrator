"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { API_BASE_URL } from "../lib/api";
import { MermaidPreview } from "./mermaid-preview";

type Organization = {
  id: string;
  name: string;
  industry?: string | null;
  employee_count?: number | null;
};

type Department = {
  id: string;
  organization_id: string;
  name: string;
  lead_name?: string | null;
};

type Tool = {
  id: string;
  organization_id: string;
  name: string;
  category: string;
  monthly_cost: string;
  ai_enabled: boolean;
  vendor?: string | null;
};

type ProcessRecord = {
  id: string;
  organization_id: string;
  department_id?: string | null;
  name: string;
  process_type?: string | null;
  raw_input_text: string;
  kpi_summary?: string | null;
  challenge_summary?: string | null;
};

type ProcessStep = {
  id: string;
  process_id: string;
  step_order: number;
  step_name: string;
  manual_work: boolean;
  approval_required: boolean;
  ai_candidate: boolean;
  automation_candidate: boolean;
  human_approval_candidate: boolean;
  issue_tags: string[];
  meeting_related: boolean;
};

type ProcessDecomposeResponse = {
  process: ProcessRecord;
  steps: ProcessStep[];
};

type Dashboard = {
  organizations_count: number;
  departments_count: number;
  tools_count: number;
  business_processes_count: number;
};

type Finding = {
  id: string;
  title: string;
  finding_type: string;
  severity: string;
  summary?: string | null;
};

type Recommendation = {
  id: string;
  type: string;
  title: string;
  description: string;
  priority_score: number;
  roi_score: number;
};

type DiagnosisResult = {
  organization_id: string;
  findings: Finding[];
  recommendations: Recommendation[];
};

type GeneratedRecommendationContent = {
  summary: string;
  strengths: string[];
  issues: string[];
  proposal: string;
  roi_hypothesis: string;
  generated_by: string;
};

type BlueprintItem = {
  blueprint_type: string;
  title: string;
  content: string;
};

type ImplementationTaskItem = {
  title: string;
  description: string;
  priority: string;
};

type BlueprintGenerationResult = {
  organization_id: string;
  blueprints: BlueprintItem[];
  implementation_tasks: ImplementationTaskItem[];
  generated_by: string;
};

type N8nDraftResult = {
  organization_id: string;
  title: string;
  draft_json: string;
  generated_by: string;
};

type InterviewQuestion = {
  id: string;
  organization_id: string;
  assignee?: string | null;
  process_id?: string | null;
  question: string;
  reason?: string | null;
  slack_message?: string | null;
  status: string;
};

type InterviewAnswer = {
  id: string;
  question_id: string;
  answer_text: string;
  answered_by?: string | null;
};

type InterviewQuestionResult = {
  organization_id: string;
  interview_questions: InterviewQuestion[];
  generated_by: string;
};

type OutputSnapshotResult = {
  organization_id: string;
  recommendation_content: GeneratedRecommendationContent | null;
  blueprints: BlueprintItem[];
  implementation_tasks: ImplementationTaskItem[];
  n8n_draft: N8nDraftResult | null;
  interview_questions: InterviewQuestion[];
  interview_answers: InterviewAnswer[];
};

type AgentState = {
  key: string;
  label: string;
  status: "waiting" | "active" | "done";
  detail: string;
};

function isMermaidBlueprint(blueprint: BlueprintItem): boolean {
  return (
    blueprint.blueprint_type.includes("mermaid") ||
    blueprint.content.trim().startsWith("flowchart")
  );
}

function isActionRunning(activeAction: string | null, prefix: string): boolean {
  return activeAction === prefix || activeAction?.startsWith(prefix) || false;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const responseText = await response.text();
    throw new Error(responseText || `API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function summarizeAgentStates(input: {
  organizations: Organization[];
  tools: Tool[];
  processes: ProcessRecord[];
  decompositions: Record<string, ProcessStep[]>;
  diagnoses: Record<string, DiagnosisResult>;
  generatedRecommendations: Record<string, GeneratedRecommendationContent>;
  generatedBlueprints: Record<string, BlueprintGenerationResult>;
  generatedQuestions: Record<string, InterviewQuestionResult>;
  generatedN8nDrafts: Record<string, N8nDraftResult>;
}): AgentState[] {
  const decompositionCount = Object.values(input.decompositions).reduce(
    (count, steps) => count + steps.length,
    0,
  );
  const diagnosisCount = Object.values(input.diagnoses).reduce(
    (count, diagnosis) => count + diagnosis.findings.length,
    0,
  );
  const recommendationCount = Object.values(input.generatedRecommendations).length;
  const blueprintCount = Object.values(input.generatedBlueprints).length;
  const questionCount = Object.values(input.generatedQuestions).reduce(
    (count, result) => count + result.interview_questions.length,
    0,
  );
  const n8nCount = Object.values(input.generatedN8nDrafts).length;

  return [
    {
      key: "discovery",
      label: "Discovery Agent",
      status: input.organizations.length || input.tools.length || input.processes.length ? "done" : "active",
      detail:
        input.organizations.length || input.tools.length || input.processes.length
          ? `組織 ${input.organizations.length} 件、ツール ${input.tools.length} 件、業務 ${input.processes.length} 件を把握済み`
          : "組織・ツール・業務の材料を集める段階",
    },
    {
      key: "decomposition",
      label: "Decomposition Agent",
      status: decompositionCount ? "done" : input.processes.length ? "active" : "waiting",
      detail: decompositionCount
        ? `業務ステップ ${decompositionCount} 件に分解済み`
        : input.processes.length
          ? "自然文業務をまだ分解していません"
          : "業務登録後に分解できます",
    },
    {
      key: "diagnosis",
      label: "Diagnosis Agent",
      status: diagnosisCount ? "done" : decompositionCount ? "active" : "waiting",
      detail: diagnosisCount
        ? `Findings ${diagnosisCount} 件を抽出済み`
        : decompositionCount
          ? "分解済み業務を診断できます"
          : "分解結果ができると診断へ進めます",
    },
    {
      key: "recommendation",
      label: "Recommendation Agent",
      status: recommendationCount ? "done" : diagnosisCount ? "active" : "waiting",
      detail: recommendationCount
        ? `提案文 ${recommendationCount} 件を生成済み`
        : diagnosisCount
          ? "診断結果から改善提案を生成できます"
          : "診断完了後に提案をまとめます",
    },
    {
      key: "interview",
      label: "Interview Agent",
      status: questionCount ? "done" : diagnosisCount ? "active" : "waiting",
      detail: questionCount
        ? `追加質問 ${questionCount} 件を生成済み`
        : diagnosisCount
          ? "不足情報を埋める質問を作れます"
          : "診断後に不足情報を見つけます",
    },
    {
      key: "blueprint",
      label: "Blueprint Agent",
      status: blueprintCount || n8nCount ? "done" : diagnosisCount ? "active" : "waiting",
      detail:
        blueprintCount || n8nCount
          ? `Blueprint ${blueprintCount} 件、n8n draft ${n8nCount} 件を生成済み`
          : diagnosisCount
            ? "図、実装タスク、n8n draft を生成できます"
            : "診断後に設計アウトプットを組み立てます",
    },
  ];
}

export function AppBuilder() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [processes, setProcesses] = useState<ProcessRecord[]>([]);
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [decompositions, setDecompositions] = useState<Record<string, ProcessStep[]>>({});
  const [diagnoses, setDiagnoses] = useState<Record<string, DiagnosisResult>>({});
  const [generatedRecommendations, setGeneratedRecommendations] = useState<
    Record<string, GeneratedRecommendationContent>
  >({});
  const [generatedBlueprints, setGeneratedBlueprints] = useState<
    Record<string, BlueprintGenerationResult>
  >({});
  const [generatedN8nDrafts, setGeneratedN8nDrafts] = useState<Record<string, N8nDraftResult>>({});
  const [generatedQuestions, setGeneratedQuestions] = useState<
    Record<string, InterviewQuestionResult>
  >({});
  const [savedInterviewAnswers, setSavedInterviewAnswers] = useState<Record<string, InterviewAnswer[]>>({});
  const [status, setStatus] = useState("読み込み中です。");
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [selectedOrganizationId, setSelectedOrganizationId] = useState<string>("");
  const [selectedOutputTab, setSelectedOutputTab] = useState<
    "diagnosis" | "recommendation" | "blueprint" | "automation"
  >("diagnosis");

  const [organizationForm, setOrganizationForm] = useState({
    name: "",
    industry: "",
    employeeCount: "",
  });
  const [departmentForm, setDepartmentForm] = useState({
    organizationId: "",
    name: "",
    leadName: "",
  });
  const [toolForm, setToolForm] = useState({
    organizationId: "",
    name: "",
    category: "",
    monthlyCost: "0",
    aiEnabled: false,
    vendor: "",
  });
  const [processForm, setProcessForm] = useState({
    organizationId: "",
    departmentId: "",
    name: "",
    processType: "",
    rawInputText: "",
    kpiSummary: "",
    challengeSummary: "",
  });
  const [answerDrafts, setAnswerDrafts] = useState<
    Record<string, { answerText: string; answeredBy: string }>
  >({});

  const orgOptions = useMemo(
    () => organizations.map((organization) => ({ label: organization.name, value: organization.id })),
    [organizations],
  );

  const selectedOrganizationIdSafe = selectedOrganizationId || organizations[0]?.id || "";
  const selectedOrganization = organizations.find(
    (organization) => organization.id === selectedOrganizationIdSafe,
  );
  const selectedDiagnosis = selectedOrganization ? diagnoses[selectedOrganization.id] : null;
  const selectedRecommendation = selectedOrganization
    ? generatedRecommendations[selectedOrganization.id]
    : null;
  const selectedBlueprint = selectedOrganization ? generatedBlueprints[selectedOrganization.id] : null;
  const selectedN8nDraft = selectedOrganization ? generatedN8nDrafts[selectedOrganization.id] : null;
  const selectedQuestions = selectedOrganization ? generatedQuestions[selectedOrganization.id] : null;
  const selectedInterviewAnswers = selectedOrganization
    ? savedInterviewAnswers[selectedOrganization.id] || []
    : [];
  const hasSavedRecommendation = Boolean(selectedRecommendation);
  const hasSavedBlueprint = Boolean(selectedBlueprint?.blueprints.length);
  const hasSavedN8nDraft = Boolean(selectedN8nDraft);
  const hasSavedQuestions = Boolean(selectedQuestions?.interview_questions.length);
  const nonRenderableBlueprintCount = selectedBlueprint
    ? selectedBlueprint.blueprints.filter((blueprint) => !isMermaidBlueprint(blueprint)).length
    : 0;

  const selectedDepartments = useMemo(
    () =>
      departments.filter(
        (department) => department.organization_id === selectedOrganizationIdSafe,
      ),
    [departments, selectedOrganizationIdSafe],
  );

  const selectedTools = useMemo(
    () => tools.filter((tool) => tool.organization_id === selectedOrganizationIdSafe),
    [tools, selectedOrganizationIdSafe],
  );

  const selectedProcesses = useMemo(
    () => processes.filter((process) => process.organization_id === selectedOrganizationIdSafe),
    [processes, selectedOrganizationIdSafe],
  );

  const processDepartmentOptions = useMemo(
    () =>
      departments.filter(
        (department) => department.organization_id === processForm.organizationId,
      ),
    [departments, processForm.organizationId],
  );

  const agentStates = useMemo(
    () =>
      summarizeAgentStates({
        organizations,
        tools,
        processes,
        decompositions,
        diagnoses,
        generatedRecommendations,
        generatedBlueprints,
        generatedQuestions,
        generatedN8nDrafts,
      }),
    [
      organizations,
      tools,
      processes,
      decompositions,
      diagnoses,
      generatedRecommendations,
      generatedBlueprints,
      generatedQuestions,
      generatedN8nDrafts,
    ],
  );

  const isReloading = isActionRunning(activeAction, "reload");
  const isDiagnosing = isActionRunning(activeAction, "diagnose");
  const isGeneratingRecommendation = isActionRunning(activeAction, "recommend");
  const isGeneratingBlueprint = isActionRunning(activeAction, "blueprint");
  const isGeneratingN8n = isActionRunning(activeAction, "n8n");
  const isGeneratingQuestion = isActionRunning(activeAction, "question");
  const isSavingAnswer = isActionRunning(activeAction, "answer");
  const isRefreshingDiagnosis = isActionRunning(activeAction, "refresh-diagnosis");

  async function runAction(actionKey: string, action: () => Promise<void>) {
    setActiveAction(actionKey);
    try {
      await action();
    } finally {
      setActiveAction((current) => (current === actionKey ? null : current));
    }
  }

  async function loadData() {
    await runAction("reload", async () => {
      try {
      const [organizationsData, departmentsData, toolsData, processesData, dashboardData] =
        await Promise.all([
          fetchJson<Organization[]>("/organizations"),
          fetchJson<Department[]>("/departments"),
          fetchJson<Tool[]>("/tools"),
          fetchJson<ProcessRecord[]>("/processes"),
          fetchJson<Dashboard>("/dashboard"),
        ]);

      setOrganizations(organizationsData);
      setDepartments(departmentsData);
      setTools(toolsData);
      setProcesses(processesData);
      setDashboard(dashboardData);
      const nextSelectedOrganizationId = selectedOrganizationId || organizationsData[0]?.id || "";
      setSelectedOrganizationId(nextSelectedOrganizationId);
      if (nextSelectedOrganizationId) {
        await loadSavedWorkspace(
          nextSelectedOrganizationId,
          processesData.filter((process) => process.organization_id === nextSelectedOrganizationId),
        );
      }
      setStatus("APIと接続できています。登録、分析、生成の一連の流れを試せます。");
      } catch (error) {
        setStatus(
          error instanceof Error
            ? `一覧取得に失敗しました: ${error.message}`
            : "一覧取得に失敗しました。バックエンド起動後に再読み込みしてください。",
        );
      }
    });
  }

  useEffect(() => {
    void loadData();
  }, []);

  useEffect(() => {
    if (!selectedOrganizationIdSafe || !processes.length) {
      return;
    }
    const organizationProcesses = processes.filter(
      (process) => process.organization_id === selectedOrganizationIdSafe,
    );
    void loadSavedWorkspace(selectedOrganizationIdSafe, organizationProcesses);
  }, [selectedOrganizationIdSafe, processes]);

  async function loadSavedWorkspace(
    organizationId: string,
    organizationProcesses: ProcessRecord[],
  ) {
    try {
      const [diagnosisSnapshot, outputSnapshot, savedStepsList] = await Promise.all([
        fetchJson<DiagnosisResult>(`/diagnosis/${organizationId}`),
        fetchJson<OutputSnapshotResult>(`/outputs/${organizationId}`),
        Promise.all(
          organizationProcesses.map(async (process) => ({
            processId: process.id,
            steps: await fetchJson<ProcessStep[]>(`/processes/${process.id}/steps`),
          })),
        ),
      ]);

      if (diagnosisSnapshot.findings.length || diagnosisSnapshot.recommendations.length) {
        setDiagnoses((current) => ({
          ...current,
          [organizationId]: diagnosisSnapshot,
        }));
      }

      if (outputSnapshot.recommendation_content) {
        setGeneratedRecommendations((current) => ({
          ...current,
          [organizationId]: outputSnapshot.recommendation_content!,
        }));
      }

      setGeneratedBlueprints((current) => ({
        ...current,
        [organizationId]: {
          organization_id: organizationId,
          blueprints: outputSnapshot.blueprints,
          implementation_tasks: outputSnapshot.implementation_tasks,
          generated_by: "saved",
        },
      }));

      if (outputSnapshot.n8n_draft) {
        setGeneratedN8nDrafts((current) => ({
          ...current,
          [organizationId]: outputSnapshot.n8n_draft!,
        }));
      }

      setGeneratedQuestions((current) => ({
        ...current,
        [organizationId]: {
          organization_id: organizationId,
          interview_questions: outputSnapshot.interview_questions,
          generated_by: "saved",
        },
      }));

      setSavedInterviewAnswers((current) => ({
        ...current,
        [organizationId]: outputSnapshot.interview_answers,
      }));

      setDecompositions((current) => {
        const next = { ...current };
        for (const savedSteps of savedStepsList) {
          if (savedSteps.steps.length) {
            next[savedSteps.processId] = savedSteps.steps;
          }
        }
        return next;
      });
    } catch (error) {
      // Keep the existing live state and avoid overriding the main status banner.
    }
  }

  async function handleCreateOrganization(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("create-organization", async () => {
      try {
        await fetchJson<Organization>("/organizations", {
          method: "POST",
          body: JSON.stringify({
            name: organizationForm.name,
            industry: organizationForm.industry || null,
            employee_count: organizationForm.employeeCount
              ? Number(organizationForm.employeeCount)
              : null,
          }),
        });
        setOrganizationForm({ name: "", industry: "", employeeCount: "" });
        setStatus("組織を保存しました。次に部署、ツール、業務を追加できます。");
        await loadData();
      } catch (error) {
        setStatus(
          error instanceof Error
            ? `組織保存に失敗しました: ${error.message}`
            : "組織保存に失敗しました。",
        );
      }
    });
  }

  async function handleCreateDepartment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("create-department", async () => {
      try {
        await fetchJson<Department>("/departments", {
          method: "POST",
          body: JSON.stringify({
            organization_id: departmentForm.organizationId,
            name: departmentForm.name,
            lead_name: departmentForm.leadName || null,
          }),
        });
        setDepartmentForm({ organizationId: "", name: "", leadName: "" });
        setStatus("部署を保存しました。業務とつなげる準備ができました。");
        await loadData();
      } catch (error) {
        setStatus(
          error instanceof Error ? `部署保存に失敗しました: ${error.message}` : "部署保存に失敗しました。",
        );
      }
    });
  }

  async function handleCreateTool(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("create-tool", async () => {
      try {
        await fetchJson<Tool>("/tools", {
          method: "POST",
          body: JSON.stringify({
            organization_id: toolForm.organizationId,
            name: toolForm.name,
            category: toolForm.category,
            monthly_cost: Number(toolForm.monthlyCost),
            ai_enabled: toolForm.aiEnabled,
            vendor: toolForm.vendor || null,
          }),
        });
        setToolForm({
          organizationId: "",
          name: "",
          category: "",
          monthlyCost: "0",
          aiEnabled: false,
          vendor: "",
        });
        setStatus("ツールを保存しました。重複や未接続の診断材料が増えました。");
        await loadData();
      } catch (error) {
        setStatus(
          error instanceof Error ? `ツール保存に失敗しました: ${error.message}` : "ツール保存に失敗しました。",
        );
      }
    });
  }

  async function handleCreateProcess(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runAction("create-process", async () => {
      try {
        await fetchJson<ProcessRecord>("/processes", {
          method: "POST",
          body: JSON.stringify({
            organization_id: processForm.organizationId,
            department_id: processForm.departmentId || null,
            name: processForm.name,
            process_type: processForm.processType || null,
            raw_input_text: processForm.rawInputText,
            kpi_summary: processForm.kpiSummary || null,
            challenge_summary: processForm.challengeSummary || null,
          }),
        });
        setProcessForm({
          organizationId: "",
          departmentId: "",
          name: "",
          processType: "",
          rawInputText: "",
          kpiSummary: "",
          challengeSummary: "",
        });
        setStatus("業務を保存しました。次は業務分解と診断を実行できます。");
        await loadData();
      } catch (error) {
        setStatus(
          error instanceof Error ? `業務保存に失敗しました: ${error.message}` : "業務保存に失敗しました。",
        );
      }
    });
  }

  async function handleDecompose(processId: string) {
    await runAction(`decompose-${processId}`, async () => {
      try {
        const response = await fetchJson<ProcessDecomposeResponse>(
          `/processes/${processId}/decompose`,
          { method: "POST" },
        );
        setDecompositions((current) => ({
          ...current,
          [processId]: response.steps,
        }));
        setStatus("Decomposition Agent が自然文業務をステップ単位に分解しました。");
      } catch (error) {
        setStatus(
          error instanceof Error ? `業務分解に失敗しました: ${error.message}` : "業務分解に失敗しました。",
        );
      }
    });
  }

  async function handleDiagnose(organizationId: string) {
    await runAction(`diagnose-${organizationId}`, async () => {
      try {
        const response = await fetchJson<DiagnosisResult>("/diagnose", {
          method: "POST",
          body: JSON.stringify({ organization_id: organizationId }),
        });
        setDiagnoses((current) => ({
          ...current,
          [organizationId]: response,
        }));
        setStatus("Diagnosis Agent がボトルネックと改善候補を整理しました。");
      } catch (error) {
        setStatus(
          error instanceof Error ? `診断に失敗しました: ${error.message}` : "診断に失敗しました。",
        );
      }
    });
  }

  async function handleGenerateRecommendations(organizationId: string, forceRefresh = false) {
    await runAction(`recommend-${organizationId}`, async () => {
      try {
        const response = await fetchJson<GeneratedRecommendationContent>("/generate-recommendations", {
          method: "POST",
          body: JSON.stringify({ organization_id: organizationId, force_refresh: forceRefresh }),
        });
        setGeneratedRecommendations((current) => ({ ...current, [organizationId]: response }));
        setStatus(
          forceRefresh
            ? "Recommendation Agent が提案文とROI仮説を再生成しました。"
            : "Recommendation Agent の提案文とROI仮説を表示しました。",
        );
      } catch (error) {
        setStatus(
          error instanceof Error ? `提案文生成に失敗しました: ${error.message}` : "提案文生成に失敗しました。",
        );
      }
    });
  }

  async function handleGenerateBlueprints(organizationId: string, forceRefresh = false) {
    await runAction(`blueprint-${organizationId}`, async () => {
      try {
        const response = await fetchJson<BlueprintGenerationResult>("/generate-blueprints", {
          method: "POST",
          body: JSON.stringify({ organization_id: organizationId, force_refresh: forceRefresh }),
        });
        setGeneratedBlueprints((current) => ({ ...current, [organizationId]: response }));
        setStatus(
          forceRefresh
            ? "Blueprint Agent が図と実装タスクを再生成しました。"
            : "Blueprint Agent の図と実装タスクを表示しました。",
        );
      } catch (error) {
        setStatus(
          error instanceof Error ? `ブループリント生成に失敗しました: ${error.message}` : "ブループリント生成に失敗しました。",
        );
      }
    });
  }

  async function handleGenerateN8nDraft(organizationId: string, forceRefresh = false) {
    await runAction(`n8n-${organizationId}`, async () => {
      try {
        const response = await fetchJson<N8nDraftResult>("/generate-n8n-draft", {
          method: "POST",
          body: JSON.stringify({ organization_id: organizationId, force_refresh: forceRefresh }),
        });
        setGeneratedN8nDrafts((current) => ({ ...current, [organizationId]: response }));
        setStatus(
          forceRefresh
            ? "Blueprint Agent が n8n draft を再生成しました。"
            : "Blueprint Agent の n8n draft を表示しました。",
        );
      } catch (error) {
        setStatus(
          error instanceof Error ? `n8nドラフト生成に失敗しました: ${error.message}` : "n8nドラフト生成に失敗しました。",
        );
      }
    });
  }

  async function handleGenerateQuestions(organizationId: string, forceRefresh = false) {
    await runAction(`question-${organizationId}`, async () => {
      try {
        const response = await fetchJson<InterviewQuestionResult>("/generate-questions", {
          method: "POST",
          body: JSON.stringify({ organization_id: organizationId, force_refresh: forceRefresh }),
        });
        setGeneratedQuestions((current) => ({ ...current, [organizationId]: response }));
        setStatus(
          forceRefresh
            ? "Interview Agent が不足情報の質問文を再生成しました。"
            : "Interview Agent の質問文を表示しました。",
        );
      } catch (error) {
        setStatus(
          error instanceof Error ? `質問文生成に失敗しました: ${error.message}` : "質問文生成に失敗しました。",
        );
      }
    });
  }

  async function handleSubmitInterviewAnswer(organizationId: string, question: InterviewQuestion) {
    const draft = answerDrafts[question.id];
    if (!draft?.answerText.trim()) {
      setStatus("回答内容を入力してから保存してください。");
      return;
    }

    await runAction(`answer-${question.id}`, async () => {
      try {
        const answerResponse = await fetchJson<{
          organization_id: string;
          saved_answers: InterviewAnswer[];
          note: string;
        }>(`/analyze-answers?organization_id=${organizationId}`, {
          method: "POST",
          body: JSON.stringify([
            {
              question_id: question.id,
              answer_text: draft.answerText.trim(),
              answered_by: draft.answeredBy.trim() || null,
            },
          ]),
        });

        setSavedInterviewAnswers((current) => ({
          ...current,
          [organizationId]: [
            ...(current[organizationId] || []).filter(
              (item) => !answerResponse.saved_answers.some((saved) => saved.id === item.id),
            ),
            ...answerResponse.saved_answers,
          ],
        }));
        setGeneratedQuestions((current) => {
          const existing = current[organizationId];
          if (!existing) {
            return current;
          }
          return {
            ...current,
            [organizationId]: {
              ...existing,
              interview_questions: existing.interview_questions.map((item) =>
                item.id === question.id ? { ...item, status: "answered" } : item,
              ),
            },
          };
        });
        setAnswerDrafts((current) => ({
          ...current,
          [question.id]: { answerText: "", answeredBy: "" },
        }));
        setStatus("回答を保存しました。必要に応じて再診断してください。");
      } catch (error) {
        setStatus(
          error instanceof Error ? `回答保存に失敗しました: ${error.message}` : "回答保存に失敗しました。",
        );
      }
    });
  }

  async function handleRefreshDiagnosis(organizationId: string) {
    await runAction(`refresh-diagnosis-${organizationId}`, async () => {
      try {
        const diagnosisResponse = await fetchJson<DiagnosisResult>("/diagnose", {
          method: "POST",
          body: JSON.stringify({ organization_id: organizationId }),
        });
        setDiagnoses((current) => ({
          ...current,
          [organizationId]: diagnosisResponse,
        }));
        setStatus("Diagnosis Agent が保存済み回答を反映して再診断しました。");
      } catch (error) {
        setStatus(
          error instanceof Error ? `再診断に失敗しました: ${error.message}` : "再診断に失敗しました。",
        );
      }
    });
  }

  return (
    <div className="dashboard-shell">
      <div className="dashboard-main">
        <section className="workspace-top-stack" id="overview">
          <header className="workspace-header">
            <div>
              <p className="eyebrow">Workspace</p>
              <h2>AI BizOps Workspace</h2>
              <p className="helper-text">
                {selectedOrganization
                  ? `${selectedOrganization.name} を対象に、登録から診断、業務接続設計図の確認までを一つの画面で進められます。`
                  : "対象組織を選ぶと、登録、分析、保存済み結果をこの画面で追えます。"}
              </p>
            </div>
            <div className="header-actions">
              <label className="workspace-selector">
                <span>対象組織</span>
                <select
                  value={selectedOrganizationIdSafe}
                  onChange={(event) => setSelectedOrganizationId(event.target.value)}
                >
                  {orgOptions.length ? null : <option value="">組織を登録してください</option>}
                  {orgOptions.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className="button-secondary"
                onClick={() => void loadData()}
                disabled={Boolean(activeAction)}
              >
                {isReloading ? "再読み込み中..." : "再読み込み"}
              </button>
              {selectedOrganization ? (
                <button
                  type="button"
                  onClick={() => void handleDiagnose(selectedOrganization.id)}
                  disabled={Boolean(activeAction)}
                >
                  {isDiagnosing ? "診断中..." : "診断を実行"}
                </button>
              ) : null}
            </div>
          </header>

          <div className="grid compact-stat-grid">
            <div className="panel compact-panel">
              <p className="eyebrow">Status</p>
              <p className="status-text">{status}</p>
              {activeAction ? <p className="status-subtle">処理中: {activeAction}</p> : null}
            </div>
            {dashboard ? (
              <>
                <div className="panel stat-mini"><span>組織</span><strong>{dashboard.organizations_count}</strong></div>
                <div className="panel stat-mini"><span>部署</span><strong>{dashboard.departments_count}</strong></div>
                <div className="panel stat-mini"><span>ツール</span><strong>{dashboard.tools_count}</strong></div>
                <div className="panel stat-mini"><span>業務</span><strong>{dashboard.business_processes_count}</strong></div>
              </>
            ) : null}
          </div>

          <section className="workspace-section panel" id="pipeline">
            <div className="section-title-row">
              <div>
                <p className="eyebrow">Agent Pipeline</p>
                <h2>内部責務の進行状況</h2>
              </div>
              <p className="helper-text">どの段階まで進んでいるかを短いカードでまとめます。</p>
            </div>
            <div className="agent-rail">
              {agentStates.map((agent) => (
                <div key={agent.key} className={`agent-card compact-agent agent-${agent.status}`}>
                  <div className="agent-header">
                    <strong>{agent.label}</strong>
                    <span className={`agent-chip chip-${agent.status}`}>
                      {agent.status === "done" ? "完了" : agent.status === "active" ? "進行対象" : "待機"}
                    </span>
                  </div>
                  <p className="helper-text">{agent.detail}</p>
                </div>
              ))}
            </div>
          </section>
        </section>

        <section className="workspace-two-column">
          <section className="workspace-section workspace-column panel compact-panel" id="input">
            <div className="section-title-row">
              <div>
                <p className="eyebrow">Data Input</p>
                <h2>登録フロー</h2>
              </div>
              <p className="helper-text">登録作業を左側でまとめて進められるよう、フォーム密度を上げています。</p>
            </div>
            <div className="form-card-grid">
          <form className="panel stack form-panel" onSubmit={(event) => void handleCreateOrganization(event)}>
            <h3>1. 組織登録</h3>
            <label>
              組織名
              <input
                value={organizationForm.name}
                onChange={(event) =>
                  setOrganizationForm((current) => ({ ...current, name: event.target.value }))
                }
                required
              />
            </label>
            <label>
              業種
              <input
                value={organizationForm.industry}
                onChange={(event) =>
                  setOrganizationForm((current) => ({ ...current, industry: event.target.value }))
                }
              />
            </label>
            <label>
              社員数
              <input
                type="number"
                min="1"
                value={organizationForm.employeeCount}
                onChange={(event) =>
                  setOrganizationForm((current) => ({
                    ...current,
                    employeeCount: event.target.value,
                  }))
                }
              />
            </label>
            <button type="submit" disabled={Boolean(activeAction)}>
              {isActionRunning(activeAction, "create-organization") ? "保存中..." : "組織を保存"}
            </button>
          </form>

          <form className="panel stack form-panel" onSubmit={(event) => void handleCreateDepartment(event)}>
            <h3>2. 部署登録</h3>
            <label>
              組織
              <select
                value={departmentForm.organizationId}
                onChange={(event) =>
                  setDepartmentForm((current) => ({
                    ...current,
                    organizationId: event.target.value,
                  }))
                }
                required
              >
                <option value="">選択してください</option>
                {orgOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              部署名
              <input
                value={departmentForm.name}
                onChange={(event) =>
                  setDepartmentForm((current) => ({ ...current, name: event.target.value }))
                }
                required
              />
            </label>
            <label>
              担当責任者
              <input
                value={departmentForm.leadName}
                onChange={(event) =>
                  setDepartmentForm((current) => ({ ...current, leadName: event.target.value }))
                }
              />
            </label>
            <button type="submit" disabled={Boolean(activeAction)}>
              {isActionRunning(activeAction, "create-department") ? "保存中..." : "部署を保存"}
            </button>
          </form>

          <form className="panel stack form-panel" onSubmit={(event) => void handleCreateTool(event)}>
            <h3>3. ツール登録</h3>
            <label>
              組織
              <select
                value={toolForm.organizationId}
                onChange={(event) =>
                  setToolForm((current) => ({
                    ...current,
                    organizationId: event.target.value,
                  }))
                }
                required
              >
                <option value="">選択してください</option>
                {orgOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              ツール名
              <input
                value={toolForm.name}
                onChange={(event) =>
                  setToolForm((current) => ({ ...current, name: event.target.value }))
                }
                required
              />
            </label>
            <label>
              カテゴリ
              <input
                value={toolForm.category}
                onChange={(event) =>
                  setToolForm((current) => ({ ...current, category: event.target.value }))
                }
                required
              />
            </label>
            <label>
              月額コスト
              <input
                type="number"
                min="0"
                step="0.01"
                value={toolForm.monthlyCost}
                onChange={(event) =>
                  setToolForm((current) => ({
                    ...current,
                    monthlyCost: event.target.value,
                  }))
                }
              />
            </label>
            <label>
              ベンダー
              <input
                value={toolForm.vendor}
                onChange={(event) =>
                  setToolForm((current) => ({ ...current, vendor: event.target.value }))
                }
              />
            </label>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={toolForm.aiEnabled}
                onChange={(event) =>
                  setToolForm((current) => ({
                    ...current,
                    aiEnabled: event.target.checked,
                  }))
                }
              />
              AI利用あり
            </label>
            <button type="submit" disabled={Boolean(activeAction)}>
              {isActionRunning(activeAction, "create-tool") ? "保存中..." : "ツールを保存"}
            </button>
          </form>

          <form className="panel stack form-panel" onSubmit={(event) => void handleCreateProcess(event)}>
            <h3>4. 業務登録</h3>
            <label>
              組織
              <select
                value={processForm.organizationId}
                onChange={(event) =>
                  setProcessForm((current) => ({
                    ...current,
                    organizationId: event.target.value,
                    departmentId: "",
                  }))
                }
                required
              >
                <option value="">選択してください</option>
                {orgOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              部署
              <select
                value={processForm.departmentId}
                onChange={(event) =>
                  setProcessForm((current) => ({
                    ...current,
                    departmentId: event.target.value,
                  }))
                }
              >
                <option value="">未選択でも可</option>
                {processDepartmentOptions.map((department) => (
                  <option key={department.id} value={department.id}>
                    {department.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              業務名
              <input
                value={processForm.name}
                onChange={(event) =>
                  setProcessForm((current) => ({ ...current, name: event.target.value }))
                }
                required
              />
            </label>
            <label>
              業務タイプ
              <input
                value={processForm.processType}
                onChange={(event) =>
                  setProcessForm((current) => ({
                    ...current,
                    processType: event.target.value,
                  }))
                }
              />
            </label>
            <label>
              自然文業務入力
              <textarea
                rows={4}
                value={processForm.rawInputText}
                onChange={(event) =>
                  setProcessForm((current) => ({
                    ...current,
                    rawInputText: event.target.value,
                  }))
                }
                required
              />
            </label>
            <label>
              KPI
              <input
                value={processForm.kpiSummary}
                onChange={(event) =>
                  setProcessForm((current) => ({
                    ...current,
                    kpiSummary: event.target.value,
                  }))
                }
              />
            </label>
            <label>
              課題
              <input
                value={processForm.challengeSummary}
                onChange={(event) =>
                  setProcessForm((current) => ({
                    ...current,
                    challengeSummary: event.target.value,
                  }))
                }
              />
            </label>
            <button type="submit" disabled={Boolean(activeAction)}>
              {isActionRunning(activeAction, "create-process") ? "保存中..." : "業務を保存"}
            </button>
          </form>
            </div>
          </section>

          <section className="workspace-section workspace-column panel compact-panel" id="analysis">
            <div className="section-title-row">
              <div>
                <p className="eyebrow">Analysis</p>
                <h2>分析ワークスペース</h2>
              </div>
              <p className="helper-text">
                {selectedOrganization
                  ? `${selectedOrganization.name} の業務を分解し、診断や生成をこのエリアで進めます。`
                  : "対象組織を選ぶと分析を進められます。"}
              </p>
            </div>
            <div className="analysis-surface">
          <div className="panel analysis-panel">
            <h3>保存済み業務</h3>
            <ul className="plain-list">
              {selectedProcesses.length ? (
                selectedProcesses.map((process) => (
                  <li key={process.id} className="result-card">
                    <div className="section-title-row">
                      <div>
                        <strong>{process.name}</strong>
                        <p className="helper-text">{process.raw_input_text}</p>
                      </div>
                      <button
                        type="button"
                        onClick={() => void handleDecompose(process.id)}
                        disabled={Boolean(activeAction)}
                      >
                        {isActionRunning(activeAction, `decompose-${process.id}`) ? "分解中..." : "業務を分解する"}
                      </button>
                    </div>
                    {decompositions[process.id] ? (
                      <ol className="step-list">
                        {decompositions[process.id].map((step) => (
                          <li key={step.id}>
                            <strong>{step.step_name}</strong>
                            <div className="inline-meta">
                              <span>手作業: {step.manual_work ? "はい" : "いいえ"}</span>
                              <span>AI候補: {step.ai_candidate ? "はい" : "いいえ"}</span>
                              <span>会議関連: {step.meeting_related ? "はい" : "いいえ"}</span>
                            </div>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="helper-text">まだ分解していません。</p>
                    )}
                  </li>
                ))
              ) : (
                <li className="helper-text">この組織の業務はまだ登録されていません。</li>
              )}
            </ul>
          </div>

          <div className="panel stack analysis-panel">
            <h3>診断と生成アクション</h3>
            {selectedOrganization ? (
              <>
                <button
                  type="button"
                  onClick={() => void handleDiagnose(selectedOrganization.id)}
                  disabled={Boolean(activeAction)}
                >
                  {isDiagnosing ? "診断中..." : "組織を診断する"}
                </button>
                <div className="action-row">
                  <button
                    type="button"
                    onClick={() => void handleGenerateRecommendations(selectedOrganization.id)}
                    disabled={Boolean(activeAction)}
                  >
                    {isGeneratingRecommendation
                      ? "処理中..."
                      : hasSavedRecommendation
                        ? "保存済み提案文を表示"
                        : "提案文を生成する"}
                  </button>
                  {hasSavedRecommendation ? (
                    <button
                      type="button"
                      className="button-secondary"
                      onClick={() => void handleGenerateRecommendations(selectedOrganization.id, true)}
                      disabled={Boolean(activeAction)}
                    >
                      再生成する
                    </button>
                  ) : null}
                </div>
                <div className="action-row">
                  <button
                    type="button"
                    onClick={() => void handleGenerateBlueprints(selectedOrganization.id)}
                    disabled={Boolean(activeAction)}
                  >
                    {isGeneratingBlueprint
                      ? "処理中..."
                      : hasSavedBlueprint
                        ? "保存済みの図とタスクを表示"
                        : "図と実装タスクを生成する"}
                  </button>
                  {hasSavedBlueprint ? (
                    <button
                      type="button"
                      className="button-secondary"
                      onClick={() => void handleGenerateBlueprints(selectedOrganization.id, true)}
                      disabled={Boolean(activeAction)}
                    >
                      再生成する
                    </button>
                  ) : null}
                </div>
                <div className="action-row">
                  <button
                    type="button"
                    onClick={() => void handleGenerateN8nDraft(selectedOrganization.id)}
                    disabled={Boolean(activeAction)}
                  >
                    {isGeneratingN8n
                      ? "処理中..."
                      : hasSavedN8nDraft
                        ? "保存済みn8nドラフトを表示"
                        : "n8nドラフトを生成する"}
                  </button>
                  {hasSavedN8nDraft ? (
                    <button
                      type="button"
                      className="button-secondary"
                      onClick={() => void handleGenerateN8nDraft(selectedOrganization.id, true)}
                      disabled={Boolean(activeAction)}
                    >
                      再生成する
                    </button>
                  ) : null}
                </div>
                <div className="action-row">
                  <button
                    type="button"
                    onClick={() => void handleGenerateQuestions(selectedOrganization.id)}
                    disabled={Boolean(activeAction)}
                  >
                    {isGeneratingQuestion
                      ? "処理中..."
                      : hasSavedQuestions
                        ? "保存済み質問案を表示"
                        : "Slack質問を生成する"}
                  </button>
                  {hasSavedQuestions ? (
                    <button
                      type="button"
                      className="button-secondary"
                      onClick={() => void handleGenerateQuestions(selectedOrganization.id, true)}
                      disabled={Boolean(activeAction)}
                    >
                      再生成する
                    </button>
                  ) : null}
                </div>
              </>
            ) : (
              <p className="helper-text">先に対象組織を選択してください。</p>
            )}
          </div>
            </div>
          </section>
        </section>

        <section className="workspace-section" id="outputs">
          <div className="section-title-row">
            <div>
              <p className="eyebrow">Outputs</p>
              <h2>保存済み結果</h2>
            </div>
            <div className="output-tabs">
              <button
                type="button"
                className={selectedOutputTab === "diagnosis" ? "tab-active" : "tab-button"}
                onClick={() => setSelectedOutputTab("diagnosis")}
              >
                Diagnosis
              </button>
              <button
                type="button"
                className={selectedOutputTab === "recommendation" ? "tab-active" : "tab-button"}
                onClick={() => setSelectedOutputTab("recommendation")}
              >
                Proposal
              </button>
              <button
                type="button"
                className={selectedOutputTab === "blueprint" ? "tab-active" : "tab-button"}
                onClick={() => setSelectedOutputTab("blueprint")}
              >
                Blueprint
              </button>
              <button
                type="button"
                className={selectedOutputTab === "automation" ? "tab-active" : "tab-button"}
                onClick={() => setSelectedOutputTab("automation")}
              >
                Automation
              </button>
            </div>
          </div>

          {selectedOutputTab === "diagnosis" ? (
            <div className="grid result-grid">
              <div className="panel">
                <h3>診断結果</h3>
                {isDiagnosing ? <div className="loading-panel"><span className="spinner" />診断結果を更新しています...</div> : null}
                {selectedDiagnosis ? (
              <div className="stack">
                <div className="result-card">
                  <h4>Findings</h4>
                  <ul className="plain-list">
                    {selectedDiagnosis.findings.map((finding) => (
                      <li key={finding.id}>
                        <strong>{finding.title}</strong>
                        <div className="inline-meta">
                          <span>{finding.finding_type}</span>
                          <span>重要度 {finding.severity}</span>
                        </div>
                        <p className="helper-text">{finding.summary}</p>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="result-card">
                  <h4>Recommendations</h4>
                  <ul className="plain-list">
                    {selectedDiagnosis.recommendations.map((recommendation) => (
                      <li key={recommendation.id}>
                        <strong>{recommendation.title}</strong>
                        <div className="inline-meta">
                          <span>{recommendation.type}</span>
                          <span>優先度 {recommendation.priority_score}</span>
                          <span>ROI {recommendation.roi_score}</span>
                        </div>
                        <p className="helper-text">{recommendation.description}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
                ) : (
                  <p className="helper-text">診断結果はまだ生成されていません。</p>
                )}
              </div>
              <div className="panel">
                <h3>登録済み部署</h3>
                <ul className="plain-list">
                  {selectedDepartments.length ? (
                    selectedDepartments.map((department) => (
                      <li key={department.id}>
                        <strong>{department.name}</strong>
                        <p className="helper-text">{department.lead_name || "責任者未設定"}</p>
                      </li>
                    ))
                  ) : (
                    <li className="helper-text">部署はまだ登録されていません。</li>
                  )}
                </ul>
              </div>
            </div>
          ) : null}

          {selectedOutputTab === "recommendation" ? (
            <div className="grid result-grid">
              <div className="panel stack">
                <h3>提案文とROI仮説</h3>
                {isGeneratingRecommendation ? <div className="loading-panel"><span className="spinner" />提案文を生成しています...</div> : null}
                {selectedRecommendation ? (
              <div className="result-card">
                <p>{selectedRecommendation.summary}</p>
                <h4>良い点</h4>
                <ul className="plain-list">
                  {selectedRecommendation.strengths.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
                <h4>問題点</h4>
                <ul className="plain-list">
                  {selectedRecommendation.issues.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
                <h4>改善提案</h4>
                <p>{selectedRecommendation.proposal}</p>
                <h4>ROI仮説</h4>
                <p>{selectedRecommendation.roi_hypothesis}</p>
              </div>
            ) : (
              <p className="helper-text">提案文はまだ生成されていません。</p>
            )}
              </div>
              <div className="panel">
                <h3>登録済みツール</h3>
                <ul className="plain-list">
                  {selectedTools.length ? (
                    selectedTools.map((tool) => (
                      <li key={tool.id}>
                        <strong>{tool.name}</strong>
                        <div className="inline-meta">
                          <span>{tool.category}</span>
                          <span>AI {tool.ai_enabled ? "あり" : "なし"}</span>
                          <span>月額 {tool.monthly_cost}</span>
                        </div>
                      </li>
                    ))
                  ) : (
                    <li className="helper-text">ツールはまだ登録されていません。</li>
                  )}
                </ul>
              </div>
            </div>
          ) : null}

          {selectedOutputTab === "blueprint" ? (
            <div className="grid result-grid">
              <div className="panel stack">
                <h3>Blueprint と実装タスク</h3>
                {isGeneratingBlueprint ? <div className="loading-panel"><span className="spinner" />図と実装タスクを生成しています...</div> : null}
                {selectedBlueprint ? (
              <>
                {nonRenderableBlueprintCount ? (
                  <div className="notice-card">
                    <strong>前回保存分はまだ図用データではありません。</strong>
                    <p className="helper-text">
                      以前の保存データは文章形式の Blueprint でした。もう一度
                      「図と実装タスクを生成する」を押すと、Mermaid 記法で保存し直され、図として表示されます。
                    </p>
                  </div>
                ) : null}
                <div className="result-card">
                  <h4>Mermaid / Blueprint</h4>
                  <ul className="plain-list">
                    {selectedBlueprint.blueprints.map((blueprint) => (
                      <li key={blueprint.title}>
                        <strong>{blueprint.title}</strong>
                        {isMermaidBlueprint(blueprint) ? (
                          <MermaidPreview chart={blueprint.content} />
                        ) : (
                          <pre className="code-block">{blueprint.content}</pre>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="result-card">
                  <h4>実装タスク</h4>
                  <ul className="plain-list">
                    {selectedBlueprint.implementation_tasks.map((task) => (
                      <li key={task.title}>
                        <strong>{task.title}</strong>
                        <div className="inline-meta">
                          <span>優先度 {task.priority}</span>
                        </div>
                        <p className="helper-text">{task.description}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <p className="helper-text">Blueprint はまだ生成されていません。</p>
            )}
              </div>
            </div>
          ) : null}

          {selectedOutputTab === "automation" ? (
            <div className="grid result-grid">
              <div className="panel stack">
                <h3>n8n draft / Slack質問</h3>
                {isGeneratingN8n || isGeneratingQuestion ? (
                  <div className="loading-panel">
                    <span className="spinner" />
                    {isGeneratingN8n ? "n8n draft を生成しています..." : "質問案を生成しています..."}
                  </div>
                ) : null}
                {isSavingAnswer ? (
                  <div className="loading-panel">
                    <span className="spinner" />
                    回答を保存しています...
                  </div>
                ) : null}
                {isRefreshingDiagnosis ? (
                  <div className="loading-panel">
                    <span className="spinner" />
                    保存済み回答を反映して再診断しています...
                  </div>
                ) : null}
                {selectedN8nDraft ? (
              <div className="result-card">
                <h4>n8n draft</h4>
                <pre className="code-block">{selectedN8nDraft.draft_json}</pre>
              </div>
            ) : (
              <p className="helper-text">n8n draft はまだ生成されていません。</p>
            )}
                {selectedQuestions ? (
              <div className="result-card">
                <h4>Slack質問案</h4>
                <ul className="plain-list">
                  {selectedQuestions.interview_questions.map((question) => (
                    <li key={question.id}>
                      <div className="agent-header">
                        <strong>{question.assignee || "未設定"}</strong>
                        <span className={question.status === "answered" ? "badge badge-success" : "badge badge-muted"}>
                          {question.status === "answered" ? "回答済" : "回答待ち"}
                        </span>
                      </div>
                      <p>{question.question}</p>
                      <p className="helper-text">{question.reason}</p>
                      <pre className="code-block">{question.slack_message}</pre>
                      <label>
                        回答
                        <textarea
                          rows={3}
                          value={answerDrafts[question.id]?.answerText || ""}
                          onChange={(event) =>
                            setAnswerDrafts((current) => ({
                              ...current,
                              [question.id]: {
                                answerText: event.target.value,
                                answeredBy: current[question.id]?.answeredBy || "",
                              },
                            }))
                          }
                          placeholder="例: 毎回45分かかっています。HubspotとGmailは未連携で、担当マネージャーが最終確認しています。"
                        />
                      </label>
                      <label>
                        回答者
                        <input
                          value={answerDrafts[question.id]?.answeredBy || ""}
                          onChange={(event) =>
                            setAnswerDrafts((current) => ({
                              ...current,
                              [question.id]: {
                                answerText: current[question.id]?.answerText || "",
                                answeredBy: event.target.value,
                              },
                            }))
                          }
                          placeholder="例: 現場担当者"
                        />
                      </label>
                      <button
                        type="button"
                        disabled={Boolean(activeAction)}
                        onClick={() => void handleSubmitInterviewAnswer(selectedOrganizationIdSafe, question)}
                      >
                        {isActionRunning(activeAction, `answer-${question.id}`) ? "保存中..." : "回答を保存"}
                      </button>
                      <button
                        type="button"
                        className="button-secondary"
                        disabled={Boolean(activeAction)}
                        onClick={() => void handleRefreshDiagnosis(selectedOrganizationIdSafe)}
                      >
                        {isActionRunning(activeAction, `refresh-diagnosis-${selectedOrganizationIdSafe}`) ? "再診断中..." : "保存済み回答で再診断"}
                      </button>
                      {selectedInterviewAnswers
                        .filter((answer) => answer.question_id === question.id)
                        .map((answer) => (
                          <div key={answer.id} className="notice-card">
                            <strong>保存済み回答</strong>
                            <p>{answer.answer_text}</p>
                            <p className="helper-text">{answer.answered_by || "回答者未設定"}</p>
                          </div>
                        ))}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="helper-text">Slack質問案はまだ生成されていません。</p>
            )}
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </div>
  );
}
