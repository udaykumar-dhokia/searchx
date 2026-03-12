from sqlalchemy import Column, String, UUID, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from . import Base

class Response(Base):
    __tablename__ = "responses"

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    vector_id = Column(UUID(as_uuid=True), nullable=False)
    query = Column(String)
    sources = Column(ARRAY(String))
    response = Column(String)
    created_at = Column(DateTime, server_default=func.now())