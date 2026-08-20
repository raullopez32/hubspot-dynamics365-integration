import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    hubspot_access_token: str | None
    hubspot_list_id: str | None
    dynamics_tenant_id: str | None
    dynamics_client_id: str | None
    dynamics_client_secret: str | None
    dynamics_base_url: str | None
    dynamics_api_version: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            hubspot_access_token=os.getenv("HUBSPOT_ACCESS_TOKEN"),
            hubspot_list_id=os.getenv("HUBSPOT_LIST_ID"),
            dynamics_tenant_id=os.getenv("DYNAMICS_TENANT_ID"),
            dynamics_client_id=os.getenv("DYNAMICS_CLIENT_ID"),
            dynamics_client_secret=os.getenv("DYNAMICS_CLIENT_SECRET"),
            dynamics_base_url=os.getenv("DYNAMICS_BASE_URL"),
            dynamics_api_version=os.getenv("DYNAMICS_API_VERSION", "v9.2"),
        )
