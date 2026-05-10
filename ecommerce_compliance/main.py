import io
import datetime
import urllib.parse
import base64
import pandas as pd
from fastapi import FastAPI, UploadFile, Form, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 기존 초고속 병렬 검수 로직 재사용
from compliance_checker import process_all_data

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/extract-keywords")
async def extract_keywords(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        if '유의키워드' in df.columns:
            kws = df['유의키워드'].dropna().astype(str).tolist()
        else:
            kws = df.iloc[:, 0].dropna().astype(str).tolist()
        return {"keywords": kws}
    except Exception as e:
        raise HTTPException(status_code=400, detail="키워드 엑셀 파일을 읽을 수 없습니다.")

@app.post("/api/inspect")
async def inspect_products(
    file: UploadFile = File(...),
    keywords: str = Form(...)
):
    try:
        # 1. 엑셀 파일 로드 (메모리에서 바로 읽음)
        content = await file.read()
        try:
            input_df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail="유효한 엑셀 파일이 아닙니다.")

        if not all(col in input_df.columns for col in ['플랫폼명', '상품코드', '상품명']):
            raise HTTPException(status_code=400, detail="엑셀 파일에 '플랫폼명', '상품코드', '상품명' 열이 모두 포함되어야 합니다.")

        # 2. 키워드 파싱
        keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
        if not keywords_list:
            raise HTTPException(status_code=400, detail="키워드를 하나 이상 입력해주세요.")

        # 3. 비동기 AI 검수 실행 (compliance_checker의 함수 재사용)
        analysis_results_dict = await process_all_data(input_df, keywords_list)

        # 4. 데이터 후처리 및 동적 열 매핑
        final_rows = []
        for index, row in input_df.iterrows():
            p_code = str(row['상품코드'])
            analysis = analysis_results_dict.get(p_code, {})
            
            result_row = {
                '플랫폼명': row['플랫폼명'],
                '상품코드': p_code,
                '상품명': row['상품명'],
                'status': analysis.get('status', '미처리'),
                'reason': analysis.get('reason', ''),
            }
            
            result_row['_detected_keywords'] = analysis.get('detected_keywords', [])
            final_rows.append(result_row)
            
        result_df = pd.DataFrame(final_rows)
        
        max_keywords = result_df['_detected_keywords'].apply(
            lambda x: len(x) if isinstance(x, list) else 0
        ).max()
        
        for i in range(max_keywords):
            col_name = f'Keyword_{i+1}'
            result_df[col_name] = result_df['_detected_keywords'].apply(
                lambda x: x[i] if isinstance(x, list) and i < len(x) else ""
            )
            
        result_df.drop(columns=['_detected_keywords'], inplace=True)

        # 5. 메모리 버퍼에 엑셀 저장
        output_io = io.BytesIO()
        with pd.ExcelWriter(output_io, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False)
        output_io.seek(0)
        
        # Base64 인코딩
        excel_base64 = base64.b64encode(output_io.read()).decode('utf-8')

        # 6. JSON 응답 생성 (요약 정보)
        today_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"검수결과_{today_str}.xlsx"
        
        warning_count = len(result_df[result_df['status'] == '유의상품'])
        ok_count = len(result_df[result_df['status'] == '정상'])
        
        return JSONResponse(content={
            "success": True,
            "filename": output_filename,
            "warning_count": int(warning_count),
            "ok_count": int(ok_count),
            "total_count": len(result_df),
            "file_base64": excel_base64
        })

    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print(f"Error occurred: {tb_str}") # print to console
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}\n\n{tb_str}")

# 정적 파일 서빙 (HTML/CSS/JS)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
