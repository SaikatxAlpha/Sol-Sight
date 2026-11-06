"""
SolSight runs without accounts: everything lives in one shared workspace.

Panels and inspections still carry an `owner_email`, so per-user accounts
can be brought back later by swapping this dependency for a real auth check
without touching the stored data or the routers.
"""

WORKSPACE_OWNER = {"name": "SolSight", "email": "workspace@solsight.local"}


async def get_owner() -> dict:
    return WORKSPACE_OWNER
