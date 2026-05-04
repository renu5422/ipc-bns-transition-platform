from pydantic import BaseModel
from typing import List


class SectionMapping(BaseModel):
    """
    IPC to BNS legal mapping schema.
    """

    id: str

    ipc_code: str
    ipc_title: str

    bns_code: str
    bns_title: str

    description: str

    chapter: str

    keywords: List[str]

    ai_summary: str

    validation_rules: List[str]

    created_at: str
    updated_at: str