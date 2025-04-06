from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# 标签模型
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class Tag(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# 分类模型
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# 文章模型
class ArticleBase(BaseModel):
    title: str
    content: str
    summary: Optional[str] = None
    category_id: int
    is_published: bool = False

class ArticleCreate(ArticleBase):
    tag_ids: Optional[List[int]] = None

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    category_id: Optional[int] = None
    is_published: Optional[bool] = None
    tag_ids: Optional[List[int]] = None

class Article(ArticleBase):
    id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    view_count: int
    tags: List[Tag] = []
    category: Category

    class Config:
        from_attributes = True

# 文章列表响应
class ArticleList(BaseModel):
    total: int
    items: List[Article]

# 搜索响应
class SearchResult(BaseModel):
    total: int
    items: List[Article]
    categories: List[Category]
    tags: List[Tag] 