from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from halo.bot.links import brand_link
from halo.db import get_session
from halo.models import Brand
from halo.schemas import BrandIn, BrandOut, BrandPatch, TelegramLinkOut

router = APIRouter(prefix="/brands", tags=["brands"])


def to_out(brand: Brand) -> BrandOut:
    out = BrandOut.model_validate(brand)
    out.telegram_connected = brand.telegram_chat_id is not None
    return out


async def get_brand_or_404(session: AsyncSession, brand_id: int) -> Brand:
    brand = await session.get(Brand, brand_id)
    if brand is None:
        raise HTTPException(404, "Brand not found")
    return brand


@router.post("", response_model=BrandOut, status_code=201)
async def create_brand(body: BrandIn, session: AsyncSession = Depends(get_session)):
    brand = Brand(**body.model_dump())
    session.add(brand)
    await session.commit()
    await session.refresh(brand)
    return to_out(brand)


@router.get("", response_model=list[BrandOut])
async def list_brands(session: AsyncSession = Depends(get_session)):
    return [to_out(b) for b in await session.scalars(select(Brand).order_by(Brand.id))]


@router.get("/{brand_id}", response_model=BrandOut)
async def get_brand(brand_id: int, session: AsyncSession = Depends(get_session)):
    return to_out(await get_brand_or_404(session, brand_id))


@router.patch("/{brand_id}", response_model=BrandOut)
async def update_brand(brand_id: int, body: BrandPatch, session: AsyncSession = Depends(get_session)):
    brand = await get_brand_or_404(session, brand_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(brand, key, value)
    await session.commit()
    return to_out(brand)


@router.get("/{brand_id}/telegram-link", response_model=TelegramLinkOut)
async def telegram_link(brand_id: int, session: AsyncSession = Depends(get_session)):
    brand = await get_brand_or_404(session, brand_id)
    return TelegramLinkOut(url=brand_link(brand.id), connected=brand.telegram_chat_id is not None)
