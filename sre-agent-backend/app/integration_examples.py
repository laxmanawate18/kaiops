"""
Optional integration examples for using new error handling, caching, and validation.

These are reference implementations that can be gradually integrated into existing routes.
Non-breaking: can be added incrementally without affecting current functionality.
"""

# ============================================================================
# EXAMPLE 1: Using custom exceptions in login route
# ============================================================================

"""
# In app/auth/routes.py - optional replacement for current login logic

from app.exceptions import (
    ValidationError, 
    CredentialsError, 
    ResourceNotFoundError,
    RequestContext,
    DatabaseError
)
from app.models import SuccessResponse

@router.post("/login", response_model=SuccessResponse)
async def login(user_credentials: UserLogin, request: Request):
    '''Authenticate user with improved error handling.'''
    try:
        # Extract context from middleware
        context = getattr(request.state, 'context', RequestContext())
        
        # Validate input
        if not user_credentials.username or not user_credentials.password:
            raise ValidationError(
                "Username and password are required",
                details={
                    "username": "Required" if not user_credentials.username else None,
                    "password": "Required" if not user_credentials.password else None
                },
                context=context
            )
        
        # Authenticate
        user = user_db.get_user(user_credentials.username)
        
        if not user or not verify_password(user_credentials.password, user["password_hash"]):
            raise CredentialsError(context=context)
        
        if not user["is_active"]:
            raise ResourceNotFoundError(
                "User", 
                user_credentials.username,
                context=context
            )
        
        # Create token
        access_token = create_access_token(
            data={"sub": user["username"], "role": user["role"]}
        )
        
        return SuccessResponse(
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"]
                }
            },
            request_id=context.request_id,
            timestamp=context.timestamp
        )
    
    except KaiOpsException:
        raise  # Re-raise KaiOps exceptions (handled by global exception handler)
    except Exception as e:
        raise DatabaseError(
            f"Login failed: {str(e)}",
            cause=e,
            context=context
        )
"""


# ============================================================================
# EXAMPLE 2: Using cache in metadata service
# ============================================================================

"""
# In app/metadata/service.py - optional caching

from app.cache import cached, get_cache_manager

class MetadataService:
    
    @cached(ttl_seconds=600, key_prefix="metadata_all")
    async def list_all_metadata(self, use_cache: bool = True):
        '''List all metadata with caching.'''
        if not use_cache:
            # Invalidate cache if requested
            self.list_all_metadata.cache_invalidate_all()
        
        # This will be cached for 10 minutes
        return await self._fetch_all_metadata()
    
    @cached(ttl_seconds=300, key_prefix="metadata_app")
    async def get_metadata(self, app_name: str):
        '''Get metadata for specific app with caching.'''
        return await self._fetch_metadata(app_name)
    
    async def update_metadata(self, app_name: str, data: Dict):
        '''Update metadata and invalidate cache.'''
        result = await self._update_metadata_db(app_name, data)
        
        # Invalidate specific and all metadata caches
        self.get_metadata.cache_invalidate(app_name)
        self.list_all_metadata.cache_invalidate_all()
        
        return result
"""


# ============================================================================
# EXAMPLE 3: Using timeout in agent service
# ============================================================================

"""
# In app/chat/agent_service.py - optional timeout handling

from app.utils import TimeoutManager
from app.exceptions import TimeoutError as KaiOpsTimeoutError

async def process_message(
    message: str,
    session_id: str,
    user_id: str,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    '''Process message with timeout protection.'''
    try:
        # Execute agent with timeout
        response_parts = []
        
        async with asyncio.timeout(timeout_seconds):
            async for event in _runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=message)])
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_parts.append(part.text)
        
        return {
            "response": "".join(response_parts),
            "success": True
        }
    
    except asyncio.TimeoutError:
        raise KaiOpsTimeoutError(
            operation="Agent execution",
            timeout_seconds=timeout_seconds
        )
"""


# ============================================================================
# EXAMPLE 4: Using audit logger for application operations
# ============================================================================

"""
# In app/applications/routes.py - optional audit logging

from app.audit import AuditLogger

@router.post("/", response_model=ApplicationResponse, status_code=201)
async def create_application(
    app_data: ApplicationCreate,
    current_user: UserResponse = Depends(get_current_admin_or_team_lead)
):
    '''Create application with audit trail.'''
    try:
        app_dict = app_data.model_dump()
        application = application_db.create_application(current_user.id, app_dict)
        
        # Log creation for audit
        AuditLogger.log_application_created(
            app_id=application["id"],
            app_name=application["application_name"],
            created_by=current_user.username,
            cloud_provider=app_data.cloud_provider
        )
        
        return build_application_response(application)
    
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise


@router.delete("/applications/{app_id}")
async def delete_application(
    app_id: str,
    current_user: UserResponse = Depends(get_current_admin_user)
):
    '''Delete application with audit trail.'''
    try:
        app = application_db.get_application(app_id)
        if not app:
            raise ResourceNotFoundError("Application", app_id)
        
        application_db.delete_application(app_id)
        
        # Log deletion for audit
        AuditLogger.log_application_deleted(
            app_id=app_id,
            app_name=app["application_name"],
            deleted_by=current_user.username
        )
        
        return {"message": "Application deleted"}
    
    except Exception as e:
        logger.error(f"Error deleting application: {e}")
        raise
"""


# ============================================================================
# EXAMPLE 5: Using health checker in application creation
# ============================================================================

"""
# In app/applications/routes.py - optional integration validation

from app.integrations import get_health_checker, IntegrationStatus
from app.exceptions import IntegrationError

health_checker = get_health_checker()

@router.post("/", response_model=ApplicationResponse, status_code=201)
async def create_application(
    app_data: ApplicationCreate,
    current_user: UserResponse = Depends(get_current_admin_or_team_lead),
    request: Request
):
    '''Create application with integration validation (optional).'''
    try:
        context = getattr(request.state, 'context', RequestContext())
        
        # Optionally validate integrations if provided
        if app_data.github_repo and os.getenv("VALIDATE_INTEGRATIONS"):
            check = await health_checker.check_github(
                token=os.getenv("GITHUB_TOKEN"),
                repo=app_data.github_repo
            )
            if check.status == IntegrationStatus.UNHEALTHY:
                raise IntegrationError(
                    "GitHub",
                    check.error_message,
                    context=context
                )
        
        # Continue with creation...
        app_dict = app_data.model_dump()
        application = application_db.create_application(current_user.id, app_dict)
        
        return build_application_response(application)
    
    except IntegrationError:
        raise
    except Exception as e:
        raise DatabaseError(str(e), cause=e, context=context)
"""


# ============================================================================
# EXAMPLE 6: Using standard response models for paginated endpoints
# ============================================================================

"""
# In app/applications/routes.py - optional pagination improvements

from app.models import PaginatedResponse, PaginationParams

@router.get("/", response_model=PaginatedResponse)
async def list_applications(
    params: PaginationParams = Depends(),
    current_user: UserResponse = Depends(get_current_user)
):
    '''List applications with standard pagination response.'''
    try:
        skip = (params.page - 1) * params.page_size
        
        applications, total_count = application_db.list_applications(
            skip=skip,
            limit=params.page_size,
            sort_by=params.sort_by,
            sort_order=params.sort_order
        )
        
        total_pages = (total_count + params.page_size - 1) // params.page_size
        
        return PaginatedResponse(
            data=[build_application_response(app) for app in applications],
            pagination={
                "total": total_count,
                "page": params.page,
                "page_size": params.page_size,
                "total_pages": total_pages,
                "has_next": params.page < total_pages,
                "has_previous": params.page > 1
            },
            request_id=getattr(request.state, 'request_id', ''),
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        raise DatabaseError(str(e), cause=e)
"""
