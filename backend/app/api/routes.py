from fastapi import APIRouter

from app.repositories.storage import get_repository
from app.schemas.department import DepartmentCreate, DepartmentRead
from app.schemas.dashboard import DashboardResponse
from app.schemas.diagnosis import DiagnoseRequest, DiagnosisResponse
from app.schemas.finding import FindingRead
from app.schemas.generation import (
    BlueprintGenerationResponse,
    GeneratedRecommendationContent,
    N8nDraftResponse,
    OrganizationScopedRequest,
    OutputSnapshotResponse,
)
from app.schemas.interview import (
    InterviewAnswerAnalysisResponse,
    InterviewAnswerCreate,
    InterviewAnswerRead,
    InterviewQuestionGenerationResponse,
    InterviewQuestionRead,
)
from app.schemas.organization import OrganizationCreate, OrganizationRead
from app.schemas.process import ProcessCreate, ProcessRead
from app.schemas.process_step import ProcessDecomposeResponse, ProcessStepRead
from app.schemas.recommendation import RecommendationRead
from app.schemas.tool import ToolCreate, ToolRead
from app.services.crud_service import CrudService
from app.services.decomposition_service import DecompositionService
from app.services.diagnosis_service import DiagnosisService
from app.services.generation_service import GenerationService
from app.services.interview_service import InterviewService

router = APIRouter()


def get_crud_service() -> CrudService:
    return CrudService(get_repository())


def get_decomposition_service() -> DecompositionService:
    return DecompositionService(get_repository())


def get_diagnosis_service() -> DiagnosisService:
    return DiagnosisService(get_repository())


def get_generation_service() -> GenerationService:
    return GenerationService(get_repository())


def get_interview_service() -> InterviewService:
    return InterviewService(get_repository())


@router.get("/", tags=["meta"])
def root() -> dict[str, str]:
    return {"message": "AI BizOps Orchestrator API"}


@router.get("/dashboard", response_model=DashboardResponse, tags=["dashboard"])
def get_dashboard() -> DashboardResponse:
    service = get_crud_service()
    organizations = service.list_organizations()
    departments = service.list_departments()
    tools = service.list_tools()
    processes = service.list_processes()
    findings = []
    recommendations = []
    for organization in organizations:
        findings.extend(get_repository().list_findings(organization["id"]))
        recommendations.extend(get_repository().list_recommendations(organization["id"]))

    return DashboardResponse(
        organizations_count=len(organizations),
        departments_count=len(departments),
        tools_count=len(tools),
        business_processes_count=len(processes),
        latest_findings=[
            {"id": item["id"], "title": item["title"], "type": item["finding_type"]}
            for item in findings[:5]
        ],
        latest_recommendations=[
            {"id": item["id"], "title": item["title"], "type": item["type"]}
            for item in recommendations[:5]
        ],
    )


@router.get("/organizations", response_model=list[OrganizationRead], tags=["organizations"])
def list_organizations() -> list[OrganizationRead]:
    service = get_crud_service()
    return [OrganizationRead.model_validate(item) for item in service.list_organizations()]


@router.post("/organizations", response_model=OrganizationRead, tags=["organizations"])
def create_organization(payload: OrganizationCreate) -> OrganizationRead:
    service = get_crud_service()
    return OrganizationRead.model_validate(service.create_organization(payload))


@router.get("/departments", response_model=list[DepartmentRead], tags=["departments"])
def list_departments() -> list[DepartmentRead]:
    service = get_crud_service()
    return [DepartmentRead.model_validate(item) for item in service.list_departments()]


@router.post("/departments", response_model=DepartmentRead, tags=["departments"])
def create_department(payload: DepartmentCreate) -> DepartmentRead:
    service = get_crud_service()
    return DepartmentRead.model_validate(service.create_department(payload))


@router.get("/tools", response_model=list[ToolRead], tags=["tools"])
def list_tools() -> list[ToolRead]:
    service = get_crud_service()
    return [ToolRead.model_validate(item) for item in service.list_tools()]


@router.post("/tools", response_model=ToolRead, tags=["tools"])
def create_tool(payload: ToolCreate) -> ToolRead:
    service = get_crud_service()
    return ToolRead.model_validate(service.create_tool(payload))


@router.get("/processes", response_model=list[ProcessRead], tags=["processes"])
def list_processes() -> list[ProcessRead]:
    service = get_crud_service()
    return [ProcessRead.model_validate(item) for item in service.list_processes()]


@router.post("/processes", response_model=ProcessRead, tags=["processes"])
def create_process(payload: ProcessCreate) -> ProcessRead:
    service = get_crud_service()
    return ProcessRead.model_validate(service.create_process(payload))


@router.post(
    "/processes/{process_id}/decompose",
    response_model=ProcessDecomposeResponse,
    tags=["processes"],
)
def decompose_process(process_id: str) -> ProcessDecomposeResponse:
    service = get_decomposition_service()
    process, steps = service.decompose_process(process_id)
    return ProcessDecomposeResponse(
        process=process,
        steps=[ProcessStepRead.model_validate(step) for step in steps],
    )


@router.get(
    "/processes/{process_id}/steps",
    response_model=list[ProcessStepRead],
    tags=["processes"],
)
def get_process_steps(process_id: str) -> list[ProcessStepRead]:
    repository = get_repository()
    return [ProcessStepRead.model_validate(step) for step in repository.list_process_steps(process_id)]


@router.post("/diagnose", response_model=DiagnosisResponse, tags=["diagnosis"])
def diagnose(payload: DiagnoseRequest) -> DiagnosisResponse:
    service = get_diagnosis_service()
    findings, recommendations = service.diagnose_organization(payload.organization_id)
    return DiagnosisResponse(
        organization_id=payload.organization_id,
        findings=[FindingRead.model_validate(item) for item in findings],
        recommendations=[RecommendationRead.model_validate(item) for item in recommendations],
    )


@router.get("/diagnosis/{organization_id}", response_model=DiagnosisResponse, tags=["diagnosis"])
def get_diagnosis(organization_id: str) -> DiagnosisResponse:
    repository = get_repository()
    findings = repository.list_findings(organization_id)
    recommendations = repository.list_recommendations(organization_id)
    return DiagnosisResponse(
        organization_id=organization_id,
        findings=[FindingRead.model_validate(item) for item in findings],
        recommendations=[RecommendationRead.model_validate(item) for item in recommendations],
    )


@router.post(
    "/generate-recommendations",
    response_model=GeneratedRecommendationContent,
    tags=["generation"],
)
def generate_recommendation_content(
    payload: OrganizationScopedRequest,
) -> GeneratedRecommendationContent:
    service = get_generation_service()
    return GeneratedRecommendationContent.model_validate(
        service.generate_recommendation_content(
            payload.organization_id,
            force_refresh=payload.force_refresh,
        )
    )


@router.post(
    "/generate-blueprints",
    response_model=BlueprintGenerationResponse,
    tags=["generation"],
)
def generate_blueprints(payload: OrganizationScopedRequest) -> BlueprintGenerationResponse:
    service = get_generation_service()
    result = service.generate_blueprints(
        payload.organization_id,
        force_refresh=payload.force_refresh,
    )
    return BlueprintGenerationResponse.model_validate(
        {
            "organization_id": result["organization_id"],
            "blueprints": [
                {
                    "blueprint_type": item["blueprint_type"],
                    "title": item["title"],
                    "content": item["content"],
                }
                for item in result["blueprints"]
            ],
            "implementation_tasks": [
                {
                    "title": item["title"],
                    "description": item["description"],
                    "priority": item["priority"],
                }
                for item in result["implementation_tasks"]
            ],
            "generated_by": result["generated_by"],
        }
    )


@router.post("/generate-n8n-draft", response_model=N8nDraftResponse, tags=["generation"])
def generate_n8n_draft(payload: OrganizationScopedRequest) -> N8nDraftResponse:
    service = get_generation_service()
    return N8nDraftResponse.model_validate(
        service.generate_n8n_draft(
            payload.organization_id,
            force_refresh=payload.force_refresh,
        )
    )


@router.get("/outputs/{organization_id}", response_model=OutputSnapshotResponse, tags=["generation"])
def get_outputs(organization_id: str) -> OutputSnapshotResponse:
    repository = get_repository()
    recommendation_record = repository.get_generated_recommendation_content(organization_id)
    n8n_record = repository.get_generated_n8n_draft(organization_id)
    recommendation_content = recommendation_record.get("content") if recommendation_record else None
    n8n_content = n8n_record.get("content") if n8n_record else None

    return OutputSnapshotResponse(
        organization_id=organization_id,
        recommendation_content=(
            GeneratedRecommendationContent.model_validate(recommendation_content)
            if recommendation_content
            else None
        ),
        blueprints=[
            {
                "blueprint_type": item["blueprint_type"],
                "title": item["title"],
                "content": item["content"],
            }
            for item in repository.list_blueprints(organization_id)
        ],
        implementation_tasks=[
            {
                "title": item["title"],
                "description": item["description"],
                "priority": item["priority"],
            }
            for item in repository.list_implementation_tasks(organization_id)
        ],
        n8n_draft=(
            N8nDraftResponse.model_validate(
                {
                    "organization_id": organization_id,
                    "title": n8n_content["title"],
                    "draft_json": n8n_content["draft_json"],
                    "generated_by": n8n_content["generated_by"],
                }
            )
            if n8n_content
            else None
        ),
        interview_questions=[
            InterviewQuestionRead.model_validate(item)
            for item in repository.list_interview_questions(organization_id)
        ],
        interview_answers=[
            InterviewAnswerRead.model_validate(item)
            for item in repository.list_interview_answers(organization_id)
        ],
    )


@router.post(
    "/generate-questions",
    response_model=InterviewQuestionGenerationResponse,
    tags=["interview"],
)
def generate_questions(payload: OrganizationScopedRequest) -> InterviewQuestionGenerationResponse:
    service = get_interview_service()
    questions, send_status = service.generate_questions(
        payload.organization_id,
        force_refresh=payload.force_refresh,
    )
    return InterviewQuestionGenerationResponse(
        organization_id=payload.organization_id,
        interview_questions=[InterviewQuestionRead.model_validate(item) for item in questions],
        generated_by=send_status,
    )


@router.post(
    "/analyze-answers",
    response_model=InterviewAnswerAnalysisResponse,
    tags=["interview"],
)
def analyze_answers(
    payload: list[InterviewAnswerCreate],
    organization_id: str,
) -> InterviewAnswerAnalysisResponse:
    service = get_interview_service()
    saved_answers = service.analyze_answers([answer.model_dump() for answer in payload])
    return InterviewAnswerAnalysisResponse(
        organization_id=organization_id,
        saved_answers=[InterviewAnswerRead.model_validate(item) for item in saved_answers],
        note="回答を保存しました。次の分析や再診断に使えます。",
    )
