from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from MRI.appDatas.appDatabase.database.db import get_db
from MRI.appDatas.appDatabase.database.models import Category, Article, Tag
from MRI.appDatas.appDatabase.schemas.knowledge import (
    CategoryCreate, Category, ArticleCreate, Article, ArticleUpdate,
    TagCreate, Tag, ArticleList, SearchResult
)
from MRI.appDatas.appDatabase.routers.user_router import get_current_user
from MRI.appDatas.appDatabase.database.models import Users

router = APIRouter(
    prefix="/knowledge",
    tags=["知识库"],
    responses={404: {"description": "未找到"}},
)

# 分类相关路由
@router.post("/categories", response_model=Category)
async def create_category(
    category: CategoryCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建知识分类"""
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories", response_model=List[Category])
async def get_categories(db: Session = Depends(get_db)):
    """获取所有分类"""
    return db.query(Category).all()

@router.get("/categories/{category_id}", response_model=Category)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    """获取指定分类"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    return category

# 文章相关路由
@router.post("/articles", response_model=Article)
async def create_article(
    article: ArticleCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建文章"""
    # 检查分类是否存在
    category = db.query(Category).filter(Category.id == article.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")
    
    # 创建文章
    db_article = Article(
        **article.dict(exclude={'tag_ids'}),
        author_id=current_user.id
    )
    
    # 添加标签
    if article.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(article.tag_ids)).all()
        db_article.tags = tags
    
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article

@router.get("/articles", response_model=ArticleList)
async def get_articles(
    skip: int = 0,
    limit: int = 10,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取文章列表"""
    query = db.query(Article)
    
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if tag_id:
        query = query.filter(Article.tags.any(Tag.id == tag_id))
    
    total = query.count()
    articles = query.offset(skip).limit(limit).all()
    
    return {"total": total, "items": articles}

@router.get("/articles/{article_id}", response_model=Article)
async def get_article(article_id: int, db: Session = Depends(get_db)):
    """获取指定文章"""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 增加浏览次数
    article.view_count += 1
    db.commit()
    
    return article

@router.put("/articles/{article_id}", response_model=Article)
async def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新文章"""
    db_article = db.query(Article).filter(Article.id == article_id).first()
    if not db_article:
        raise HTTPException(status_code=404, detail="文章不存在")
    
    # 检查权限
    if db_article.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限修改此文章")
    
    # 更新文章
    update_data = article_update.dict(exclude_unset=True)
    if "tag_ids" in update_data:
        tag_ids = update_data.pop("tag_ids")
        tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        db_article.tags = tags
    
    for key, value in update_data.items():
        setattr(db_article, key, value)
    
    db.commit()
    db.refresh(db_article)
    return db_article

# 标签相关路由
@router.post("/tags", response_model=Tag)
async def create_tag(
    tag: TagCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建标签"""
    db_tag = Tag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/tags", response_model=List[Tag])
async def get_tags(db: Session = Depends(get_db)):
    """获取所有标签"""
    return db.query(Tag).all()

# 搜索路由
@router.get("/search", response_model=SearchResult)
async def search_knowledge(
    keyword: str = Query(..., description="搜索关键词"),
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """搜索知识库"""
    # 搜索文章
    query = db.query(Article).filter(
        (Article.title.ilike(f"%{keyword}%")) |
        (Article.content.ilike(f"%{keyword}%")) |
        (Article.summary.ilike(f"%{keyword}%"))
    )
    
    if category_id:
        query = query.filter(Article.category_id == category_id)
    if tag_id:
        query = query.filter(Article.tags.any(Tag.id == tag_id))
    
    articles = query.all()
    
    # 获取相关分类
    categories = db.query(Category).all()
    
    # 获取相关标签
    tags = db.query(Tag).all()
    
    return {
        "total": len(articles),
        "items": articles,
        "categories": categories,
        "tags": tags
    } 