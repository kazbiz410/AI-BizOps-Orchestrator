from app.repositories.storage import StorageRepository
from app.schemas.department import DepartmentCreate
from app.schemas.organization import OrganizationCreate
from app.schemas.process import ProcessCreate
from app.schemas.tool import ToolCreate


class CrudService:
    def __init__(self, repository: StorageRepository) -> None:
        self.repository = repository

    def create_organization(self, payload: OrganizationCreate) -> dict:
        return self.repository.create_organization(payload.model_dump())

    def list_organizations(self) -> list[dict]:
        return self.repository.list_organizations()

    def create_department(self, payload: DepartmentCreate) -> dict:
        return self.repository.create_department(payload.model_dump())

    def list_departments(self) -> list[dict]:
        return self.repository.list_departments()

    def create_tool(self, payload: ToolCreate) -> dict:
        return self.repository.create_tool(payload.model_dump())

    def list_tools(self) -> list[dict]:
        return self.repository.list_tools()

    def create_process(self, payload: ProcessCreate) -> dict:
        return self.repository.create_process(payload.model_dump())

    def list_processes(self) -> list[dict]:
        return self.repository.list_processes()

