from __future__ import annotations

from src.config import Settings
from src.dynamics.auth import DataverseAuth
from src.dynamics.client import DataverseClient
from src.hubspot.client import HubSpotClient
from src.hubspot.contacts import HubSpotContacts
from src.mapping.loader import MappingConfig

from .contacts import ContactSync
from .opportunities import OpportunitySync
from .workflow import SyncWorkflow


def build_sync_workflow(settings: Settings) -> SyncWorkflow:
    settings.validate()

    hubspot = HubSpotContacts(HubSpotClient(settings.hubspot_access_token))

    auth = DataverseAuth(
        tenant_id=settings.dynamics_tenant_id,
        client_id=settings.dynamics_client_id,
        client_secret=settings.dynamics_client_secret,
        base_url=settings.dynamics_base_url,
    )
    dataverse = DataverseClient(
        auth,
        api_version=settings.dynamics_api_version,
    )

    mapping = MappingConfig.load(settings.mapping_file)

    return SyncWorkflow(
        hubspot=hubspot,
        contacts=ContactSync(dataverse),
        opportunities=OpportunitySync(dataverse, mapping.entity("opportunity")),
    )
