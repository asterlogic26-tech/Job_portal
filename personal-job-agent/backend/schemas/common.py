from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class PaginationMeta(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
