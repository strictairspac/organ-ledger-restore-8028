from fastapi import APIRouter, Depends

from src.config.resources import engine
from src.controllers.access import identity, operator
from src.schemas.corrections import CorrectionEntry, CorrectionInput
from src.services import corrections

router = APIRouter(prefix="/cases/{case_id}/corrections", tags=["Corrections"])


@router.get("", response_model=list[CorrectionEntry], dependencies=[Depends(identity)])
def list_corrections(case_id: int):
    with engine.connect() as db:
        return corrections.list_for_case(db, case_id)


@router.post("", response_model=CorrectionEntry, status_code=201)
def correct(case_id: int, form: CorrectionInput, user=Depends(operator)):
    with engine.begin() as db:
        return corrections.apply(db, case_id, form, user["username"])
