from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from MRI.appDatas.appDatabase.database.db import Base

# 文章和标签的关联表
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Category(Base):
    """知识分类"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    articles = relationship("Article", back_populates="category")

class Article(Base):
    """知识文章"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    category_id = Column(Integer, ForeignKey("categories.id"))
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    view_count = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)

    # 关联关系
    category = relationship("Category", back_populates="articles")
    author = relationship("User", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags, back_populates="articles")

class Tag(Base):
    """文章标签"""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联关系
    articles = relationship("Article", secondary=article_tags, back_populates="tags")

class Users(Base):
    __tablename__ = "usersK"
    id = Column(Integer , primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)