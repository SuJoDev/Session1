from pydantic import BaseModel
from typing import Dict

class UsersShema(BaseModel):
    name: str
    password: str
    
class AuthorShema(BaseModel):
    name: str
    position: str
    
class DocumentComents(BaseModel):
    document_id: int
    text:str
    date_created: str
    date_updated: str
    author: AuthorShema