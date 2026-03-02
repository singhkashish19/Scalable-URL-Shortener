"""
API routes / endpoints.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse

from app.application.use_cases.url_use_cases import (
    GetAnalyticsUseCase,
    ResolveURLUseCase,
    ShortenURLUseCase,
)
from app.core.exceptions import AppException
from app.interfaces.api.dependencies import (
    get_get_analytics_use_case,
    get_rate_limiter,
    get_resolve_url_use_case,
    get_shorten_url_use_case,
)
from app.interfaces.schemas import (
    AnalyticsSchema,
    ErrorResponseSchema,
    ShortenRequestSchema,
    ShortenResponseSchema,
)

# Create router
router = APIRouter(prefix="/api/v1")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    if request.client:
        return request.client.host
    return request.headers.get("X-Forwarded-For", "127.0.0.1").split(",")[0]


# Health check - MUST be before dynamic routes
@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


@router.post(
    "/shorten",
    response_model=ShortenResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponseSchema},
        409: {"model": ErrorResponseSchema},
        429: {"model": ErrorResponseSchema},
    },
)
async def shorten_url(
    body: ShortenRequestSchema,
    http_request: Request,
    use_case: ShortenURLUseCase = Depends(get_shorten_url_use_case),
) -> ShortenResponseSchema:
    """
    Shorten a URL.
    
    - Validates the input URL
    - Supports custom aliases
    - Supports expiration dates
    """
    try:
        result = await use_case.execute(
            long_url=body.long_url,
            custom_alias=body.custom_alias,
            expiration_days=body.expiration_days,
        )
        return ShortenResponseSchema(**result)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Analytics endpoint - MUST be before generic {short_code} route
@router.get(
    "/analytics/{short_code}",
    response_model=AnalyticsSchema,
    responses={
        404: {"model": ErrorResponseSchema},
    },
)
async def get_analytics(
    short_code: str,
    days: int = Query(30, ge=1, le=365),
    use_case: GetAnalyticsUseCase = Depends(get_get_analytics_use_case),
) -> AnalyticsSchema:
    """
    Get analytics for a shortened URL.
    
    Returns:
    - Total clicks
    - Unique visitors
    - Clicks per day
    - Top referrers
    - Country distribution
    """
    try:
        analytics = await use_case.execute(short_code=short_code, days=days)
        return AnalyticsSchema(**analytics)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


# Dynamic route - MUST be last
@router.get(
    "/{short_code}",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    responses={
        404: {"model": ErrorResponseSchema},
        410: {"model": ErrorResponseSchema},
    },
)
async def redirect_url(
    short_code: str,
    http_request: Request,
    use_case: ResolveURLUseCase = Depends(get_resolve_url_use_case),
) -> RedirectResponse:
    """
    Redirect to the original URL.
    
    - Tracks click event
    - Returns 307 Temporary Redirect
    - Fast cache lookup
    """
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent")
    referrer = http_request.headers.get("Referer")

    try:
        long_url = await use_case.execute(
            short_code=short_code,
            ip_address=client_ip,
            user_agent=user_agent,
            referrer=referrer,
        )
        return RedirectResponse(url=long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
