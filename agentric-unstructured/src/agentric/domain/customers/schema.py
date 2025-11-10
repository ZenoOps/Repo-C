from agentric.domain.requests.schemas import Request
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional
from agentric.lib.schema import CamelizedBaseStruct
from agentric.lib import dto
from advanced_alchemy.extensions.litestar.dto import SQLAlchemyDTO
from agentric.db import models as m

class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name:str
    address: Optional[str] = None
    requests: list[Request]

class CustomerCreate(CamelizedBaseStruct):
    """Schema for creating a new Customer, including all required fields for registration"""

    name:str
    email_address:str
    password:str

class CustomerLogin(CamelizedBaseStruct):
    """Schema for customer log in"""

    username:str
    password:str

class CustomerDTO(SQLAlchemyDTO[m.Customer]):
    """Data Transfer Object for the Customer model.
    Configures serialization and deserialization for API responses.
    """

    config = dto.config(
        max_nested_depth=0, exclude={"created_at", "updated_at", "hashed_name","hashed_password"}
    )