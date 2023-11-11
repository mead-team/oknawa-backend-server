from pydantic import BaseModel, Field


class RequestHotplace(BaseModel):
    category_group_code: str = Field("CE7", title="카테고리 코드", description="카테고리 코드")
    x: str = Field(title="x좌표", description="x좌표")
    y: str = Field(title="y좌표", description="y좌표")
    radius: int = Field(500, title="범위 (미터)", description="범위")
    page: int = Field(1, title="범위 (미터)", description="범위")
    size: int = Field(15, title="범위 (미터)", description="범위")
    sort: str = Field("accuracy", title="범위 (미터)", description="범위")
    
    
class Hotplace(BaseModel):
    address_name: str
    category_group_code: str
    category_group_name: str
    category_name: str
    distance: str
    id: str
    phone: str
    place_name: str
    place_url: str
    road_address_name: str
    x: str
    y: str
    
    
class Meta(BaseModel):
    is_end: bool
    pageable_count: int
    total_count: int

    
class ResponseHotplace(BaseModel):
    documents: list[Hotplace]
    meta: Meta
    