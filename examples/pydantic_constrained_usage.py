from __future__ import annotations

from pydantic import BaseModel, ValidationError

from base_typed_string import BaseConstrainedTypedString


class RequestExecutionDigest(BaseConstrainedTypedString):
    min_length = 64
    max_length = 64
    pattern = r"^[0-9a-f]{64}$"


class RequestModel(BaseModel):
    digest: RequestExecutionDigest


def main() -> None:
    request_model = RequestModel.model_validate({"digest": "a" * 64})

    print(f"runtime value: {request_model.digest!r}")
    print(f"runtime type: {type(request_model.digest).__name__}")
    print(f"plain dump: {request_model.model_dump()}")
    print(f"JSON Schema: {RequestModel.model_json_schema()}")

    try:
        RequestModel.model_validate({"digest": "invalid"})
    except ValidationError as validation_error:
        print(f"rejected: {validation_error.errors()[0]['type']}")


if __name__ == "__main__":
    main()
