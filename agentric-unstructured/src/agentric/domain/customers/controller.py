from typing import Annotated
from uuid import UUID

from litestar import Controller, get
from litestar.exceptions import HTTPException
from structlog import getLogger

from agentric.domain.customers.deps import provide_customer_service
from agentric.domain.customers.services import CustomerService

from . import schema as s

logger = getLogger()


class CustomerController(Controller):
    tags = ["Customer"]
    path = "/api/customers"

    dependencies = {"customer_service": provide_customer_service}
    return_dto = s.CustomerDTO

    @get("/{customer_id:uuid}")
    async def get_customer(
        self,
        customer_service: CustomerService,
        customer_id: Annotated[UUID, "The Request ID"],
    ) -> s.Customer:
        customer_obj = await customer_service.get_one_or_none(id=customer_id)

        if customer_obj is None:
            raise HTTPException(status_code=404, detail="Customer not found")

        return customer_service.to_schema(customer_obj, schema_type=s.Customer)

    @get("/list")
    async def list_customer(self, customer_service: CustomerService) -> list[s.Customer]:
        customers, _ = await customer_service.list_and_count()
        return [customer_service.to_schema(customer, schema_type=s.Customer) for customer in customers]
