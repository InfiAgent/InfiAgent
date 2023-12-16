from fastapi import APIRouter, File, Form, UploadFile
from typing import List, Optional

try:
    import infiagent
    from infiagent.services.chat_complete_service import predict
except ImportError:
    print("import infiagent failed, please install infiagent by 'pip install .' in the pipeline directory of ADA-Agent")
    from ..services.chat_complete_service import predict

predict_router = APIRouter()


@predict_router.post("/predict")
async def chat_predict(
    prompt: str = Form(...),
    model_name: str = Form(...),
    psm: Optional[str] = Form(None),
    dc: Optional[str] = Form(None),
    temperature: Optional[str] = Form(None),
    top_p: Optional[str] = Form(None),
    top_k: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    kwargs = {}
    if psm:
        kwargs['psm'] = psm
    if dc:
        kwargs['dc'] = dc
    if temperature:
        kwargs['temperature'] = float(temperature)
    if top_p:
        kwargs['top_p'] = float(top_p)
    if top_k:
        kwargs['top_k'] = float(top_k)

    response = await predict(prompt, model_name, files, **kwargs)

    return {
        "answer": response
    }
