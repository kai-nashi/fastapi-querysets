from typing import Final
from typing import List

from fastapi import HTTPException

ERROR_INTEGER: Final = "type_error.integer"
ERROR_DOES_NOT_EXIST: Final = "does_not_exist"
ERROR_PERMISSION_DENIED: Final = "permission_denied"
ERROR_UNIQUE: Final = "not_unique"


def create_validation_detail(msg: str, loc: List[str], _type: str = "type_error.integer"):
    return {
        "loc": loc,
        "msg": msg,
        "type": _type,
    }


def create_validation_exception(
    msg: str,
    loc: List[str],
    status_code: int = 422,
    _type: str = ERROR_INTEGER,
) -> HTTPException:
    return HTTPException(status_code, detail=[create_validation_detail(msg, loc, _type)])
