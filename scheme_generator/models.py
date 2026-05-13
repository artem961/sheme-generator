# models.py
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class EdgeObject(BaseModel):
    from_node: str = Field(alias="from")
    to_node: str = Field(alias="to")
    label: Optional[str] = None

class NodeObject(BaseModel):
    type: int = Field(ge=1, le=6)
    layer: int = Field(ge=0)
    text: str
    order: Optional[int] = None

    @property
    def formatted_text(self) -> str:
        # Заменяем подстрочные индексы вида _{i} на <sub>i</sub>
        processed = re.sub(r'\_\{([^}]+)\}', r'<sub>\1</sub>', self.text)
        return processed

class SchemeSchema(BaseModel):
    meta: Dict[str, str]
    nodes: Dict[str, NodeObject]
    edges: List[EdgeObject]

