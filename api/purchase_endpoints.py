"""
API endpoints for automated Amazon purchases.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
import logging
import uuid

from agentic.payment_agent import get_purchase_agent, PurchaseAgent

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/purchases",
    tags=["purchases"]
)


# Request/Response Models
class PurchaseRequest(BaseModel):
    """Request model for initiating a purchase."""
    product_url: HttpUrl = Field(..., description="Amazon product URL")
    user_approved: bool = Field(False, description="User approval status")
    auto_approved: bool = Field(False, description="System auto-approval status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_url": "https://www.amazon.com/dp/B08N5WRWNW",
                "user_approved": True,
                "auto_approved": False
            }
        }


class PurchaseResponse(BaseModel):
    """Response model for purchase execution."""
    status: str = Field(..., description="success, error, or rejected")
    message: str
    product_url: str
    order_number: Optional[str] = None
    actions_taken: Optional[int] = None


def get_purchase_agent_dependency(headless: bool = Query(True, description="Run browser in headless mode")) -> PurchaseAgent:
    """Dependency to get purchase agent with configurable headless mode."""
    return get_purchase_agent(headless=headless)


# Endpoints
@router.post("/execute", response_model=PurchaseResponse)
async def execute_purchase(
    request: PurchaseRequest,
    agent: PurchaseAgent = Depends(get_purchase_agent_dependency)
):
    """
    Execute an automated Amazon purchase.
    
    This endpoint triggers the AI agent to:
    1. Navigate to the product URL
    2. Add product to cart
    3. Complete checkout with saved credentials
    4. Return order confirmation
    
    Requires either user_approved or auto_approved to be True.
    """
    # Check approval status
    approved = request.user_approved or request.auto_approved
    
    if not approved:
        raise HTTPException(
            status_code=403,
            detail="Purchase not approved. Set user_approved or auto_approved to true."
        )
    
    logger.info(f"Purchase request received for: {request.product_url}")
    
    # Execute purchase using agent
    result = await agent.execute_purchase(
        product_url=str(request.product_url)
    )
    
    # Handle different result statuses
    if result["status"] == "error":
        raise HTTPException(
            status_code=500,
            detail=result["message"]
        )
    
    return PurchaseResponse(**result)


@router.post("/execute-background")
async def execute_purchase_background(
    request: PurchaseRequest,
    background_tasks: BackgroundTasks,
    agent: PurchaseAgent = Depends(get_purchase_agent_dependency)
):
    """
    Execute purchase in background (non-blocking).
    
    Returns immediately with task_id.
    """
    approved = request.user_approved or request.auto_approved
    
    if not approved:
        raise HTTPException(status_code=403, detail="Purchase not approved")
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Add to background tasks
    background_tasks.add_task(
        agent.execute_purchase,
        product_url=str(request.product_url)
    )
    
    return {
        "status": "processing",
        "task_id": task_id,
        "message": "Purchase started in background."
    }


@router.get("/health")
async def health_check():
    """Check if purchase service is healthy."""
    return {
        "status": "healthy",
        "service": "automated-purchases",
    }
