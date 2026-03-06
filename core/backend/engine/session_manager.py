import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from .contracts import ProcessingSession
from .repository import Repository

_repo = Repository()

async def create(app_name: str, input_hash: str, metadata: Dict[str, Any]) -> ProcessingSession:
    """Crea una nueva sesión de procesamiento."""
    session = ProcessingSession(
        id=str(uuid.uuid4()),
        app_name=app_name,
        input_hash=input_hash,
        input_metadata=metadata,
        status="active"
    )
    return await _repo.create_session(session)

async def get(session_id: str) -> Optional[ProcessingSession]:
    """Recupera una sesión por su ID."""
    return await _repo.get_session(session_id)

async def expire_inactive(ttl_minutes: int = None) -> int:
    """
    Expira las sesiones que han estado inactivas por más tiempo del TTL.
    Si ttl_minutes no se provee, se usa el individual de cada sesión.
    Devuelve la cantidad de sesiones expiradas.
    """
    # Para simplicidad y eficiencia en MongoDB, buscamos sesiones activas 
    # cuyo last_active + su propio ttl_minutes sea menor a ahora.
    
    count = 0
    # Obtenemos sesiones activas
    cursor = _repo._sessions.find({"status": "active"})
    now = datetime.now(timezone.utc)
    
    async for doc in cursor:
        session = ProcessingSession(**doc)
        effective_ttl = ttl_minutes or session.ttl_minutes
        
        if session.last_active.replace(tzinfo=timezone.utc) + timedelta(minutes=effective_ttl) < now:
            await _repo.update_session(session.id, {"status": "expired"})
            count += 1
            
    return count
