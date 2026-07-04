"""Public blog: list of published posts and individual post pages."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BlogPost
from ..templating import templates

router = APIRouter(prefix="/blog")


@router.get("")
def blog_index(request: Request, db: Session = Depends(get_db)):
    posts = db.scalars(
        select(BlogPost)
        .where(BlogPost.published.is_(True))
        .order_by(BlogPost.created_at.desc())
    ).all()
    return templates.TemplateResponse(
        "blog/list.html", {"request": request, "posts": posts}
    )


@router.get("/{slug}")
def blog_post(slug: str, request: Request, db: Session = Depends(get_db)):
    post = db.scalar(
        select(BlogPost).where(
            BlogPost.slug == slug, BlogPost.published.is_(True)
        )
    )
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return templates.TemplateResponse(
        "blog/post.html", {"request": request, "post": post}
    )
