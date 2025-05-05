from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

from app.lambda_2 import repository

app = APIGatewayRestResolver()
items_repo = repository.Repository({})


@app.get("/health")
def health():
    return {"message": items_repo.get_health()}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    items_repo.connect()
    return app.resolve(event, context)
