"""Admin: blog post CRUD with Markdown body, a cover image, and a photo gallery."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import BlogImage, BlogPost, User
from ..security import assert_csrf, require_admin
from ..services import images, storage, text
from ..templating import templates

router = APIRouter(prefix="/admin/blog")

# Maximum number of additional gallery images per post (on top of the cover).
MAX_GALLERY_IMAGES = 10


def _get_post_or_404(db: Session, post_id: int) -> BlogPost:
    post = db.get(BlogPost, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


async def _maybe_store_cover(cover: UploadFile | None) -> str | None:
    if cover is None or not cover.filename:
        return None
    data = await cover.read()
    if not data:
        return None
    try:
        return images.process_blog_image(data)
    except images.InvalidImageError:
        return None


async def _store_gallery(
    files: list[UploadFile], post: BlogPost, db: Session, *, limit: int
) -> int:
    """Validate and attach up to ``limit`` gallery images. Returns count added."""
    if limit <= 0:
        return 0
    next_order = (
        db.scalar(select(func.max(BlogImage.sort_order)).where(BlogImage.post_id == post.id))
        or 0
    )
    added = 0
    for upload in files:
        if added >= limit:
            break
        if upload is None or not upload.filename:
            continue
        data = await upload.read()
        if not data:
            continue
        try:
            filename = images.process_blog_image(data)
        except images.InvalidImageError:
            continue
        next_order += 1
        db.add(BlogImage(post_id=post.id, filename=filename, sort_order=next_order))
        added += 1
    return added


@router.get("")
def list_posts(request: Request, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    posts = db.scalars(select(BlogPost).order_by(BlogPost.created_at.desc())).all()
    return templates.TemplateResponse(
        "admin/blog_list.html", {"request": request, "posts": posts}
    )


@router.get("/new")
def new_post_form(request: Request, user: User = Depends(require_admin)):
    return templates.TemplateResponse(
        "admin/blog_form.html",
        {"request": request, "post": None, "max_gallery": MAX_GALLERY_IMAGES},
    )


@router.post("")
async def create_post(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    title: str = Form(...),
    excerpt: str = Form(""),
    body: str = Form(""),
    published: str | None = Form(None),
    cover: UploadFile | None = File(None),
    gallery: list[UploadFile] = File(default=[]),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    post = BlogPost(
        title=title.strip() or "Untitled post",
        slug=text.unique_slug(db, BlogPost, title),
        excerpt=excerpt,
        body=body,
        published=bool(published),
        cover_image=await _maybe_store_cover(cover),
    )
    db.add(post)
    db.flush()  # assign post.id for gallery rows
    await _store_gallery(gallery, post, db, limit=MAX_GALLERY_IMAGES)
    db.commit()
    return RedirectResponse("/admin/blog", status_code=303)


@router.get("/{post_id}")
def edit_post_form(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    post = _get_post_or_404(db, post_id)
    return templates.TemplateResponse(
        "admin/blog_form.html",
        {"request": request, "post": post, "max_gallery": MAX_GALLERY_IMAGES},
    )


@router.post("/{post_id}")
async def update_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    title: str = Form(...),
    excerpt: str = Form(""),
    body: str = Form(""),
    published: str | None = Form(None),
    remove_cover: str | None = Form(None),
    cover: UploadFile | None = File(None),
    remove_images: list[str] = Form(default=[]),
    gallery: list[UploadFile] = File(default=[]),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    post = _get_post_or_404(db, post_id)
    post.title = title.strip() or post.title
    post.excerpt = excerpt
    post.body = body
    post.published = bool(published)

    new_cover = await _maybe_store_cover(cover)
    if new_cover is not None:
        storage.delete_blog_image(post.cover_image)
        post.cover_image = new_cover
    elif remove_cover:
        storage.delete_blog_image(post.cover_image)
        post.cover_image = None

    _remove_gallery_images(db, post, remove_images)

    remaining = MAX_GALLERY_IMAGES - len(post.gallery)
    await _store_gallery(gallery, post, db, limit=remaining)

    db.commit()
    return RedirectResponse("/admin/blog", status_code=303)


def _remove_gallery_images(db: Session, post: BlogPost, remove_ids: list[str]) -> None:
    wanted = {int(value) for value in remove_ids if value.strip().isdigit()}
    if not wanted:
        return
    for image in list(post.gallery):
        if image.id in wanted:
            storage.delete_blog_image(image.filename)
            db.delete(image)


@router.post("/{post_id}/delete")
def delete_post(
    post_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
    csrf_token: str = Form(...),
):
    assert_csrf(request, csrf_token)
    post = _get_post_or_404(db, post_id)
    filenames = [post.cover_image, *[image.filename for image in post.gallery]]
    db.delete(post)
    db.commit()
    for filename in filenames:
        storage.delete_blog_image(filename)
    return RedirectResponse("/admin/blog", status_code=303)
