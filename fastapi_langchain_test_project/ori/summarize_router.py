# path: app/routers/summarize_router.py

from fastapi import APIRouter, File, UploadFile, HTTPException
# APIRouter : 라우팅(앤드포인트)을 별도의 모듈 단위로 분리 및 관리하기 위한 클래스임
# File : multipart 로 업로드되는 파일 받는 클래스임
# UploadFile : 업로드 파일을 다루기 위한 클래스임 (스트리밍, 메타정보 제공)

from fastapi.responses import HTMLResponse # 응답을 html 로 반환할 때 사용하는 Response 클래스임

from app.core.config import settings
from app.services.pdf_service import save_upload_to_temp, load_pdf_documents
from app.services.summarize_service import summarize_documents

router = APIRouter(prefix="/api", tags=["summarize"])
# prefix="/api" : 라우터로 정의되는 모든 경로 앞에 자동으로 "/api"가 붙도록 지정함
# 예) @router.get("/") => 실제 경로는 "/api/" 
# tags=["summarize"] : Swagger (API 문서)에서 이 라우터 앤드포인트들을 "summarize" 그룹으로 묶어주라는 설정임

@router.get("/", response_class=HTMLResponse)  # response_class=HTMLResponse : 리턴값을 html로 응답하도록 함
def home():
  # 간단한 테스트용 업로드 폼
  return '''
  <html>
    <body>
      <h2>PDF Summarizer</h2>
      <form action="/api/summarize" enctype="multipart/form-data" method="post">
        <input name="file" type="file" accept="application/pdf" />
        <button type="submit">Upload & Summarize</button>
      </form>
    </body>
  </html>
  '''
# def home() -----------------------------------------

# -----------------------------------------------
'''
POST /api/summarize 요청 처리하는 앤드포인트
 - 사용자가 pdf 를 업로드하면,
  1. 파일 타입, 크기 검증
  2. 임시 파일 저장
  3. pdf 텍스트 추출
  4. 요약
  5. json 결과 반환
'''
@router.post("/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
  # FastAPI 파일 업로드는 UploagFile 사용함  
  if file.content_type not in ("application/pdf", "application/x-pdf"):
    raise HTTPException(status_code=400, detail="pdf 파일만 업로드할 수 있습니다.")
  
  data = await file.read()
  if len(data) > settings.MAX_UPLOAD_SIZE:
    raise HTTPException(status_code=413, detail="파일이 큽니다. (20MB 초과임)")
  
  temp_path = save_upload_to_temp(data)
  try:
    docs, page_count = load_pdf_documents(temp_path)
    if page_count == 0:
      raise HTTPException(status_code=400, detail="pdf 에서 텍스트를 추출하지 못했습니다.")
    
    summary = summarize_documents(docs)
    
    return {
      "filename": file.filename,
      "pages": page_count,
      "summary": summary,
    }
  except HTTPException:
    raise
  except Exception as e:    
    raise HTTPException(status_code=500, detail=f"요약 처리 중 오류 발생: {str(e)}")
# async def summarize_pdf() ----------------------------------
  