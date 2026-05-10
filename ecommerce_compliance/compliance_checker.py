import os
import datetime
import pandas as pd

# 호환성을 위해 async 함수로 정의 (main.py에서 await를 사용하므로)
async def process_all_data(input_df, keywords_list):
    """
    AI API를 사용하지 않고 파이썬 내부 문자열 매칭(Rule-based)을 통해 유의 키워드를 검출합니다.
    """
    final_results = {}
    
    # 키워드 양끝 공백 제거 및 소문자 변환(옵션)으로 비교를 더 정확히
    clean_keywords = [k.strip() for k in keywords_list if k.strip()]
    
    for index, row in input_df.iterrows():
        p_code = str(row.get('상품코드', ''))
        p_name = str(row.get('상품명', ''))
        
        detected_keywords = []
        for kw in clean_keywords:
            # 대소문자 구분 없이 상품명에 키워드가 포함되어 있는지 확인
            if kw.lower() in p_name.lower():
                detected_keywords.append(kw)
        
        if detected_keywords:
            status = "유의상품"
            reason = f"유의 키워드 직접 포함: {', '.join(detected_keywords)}"
        else:
            status = "정상"
            reason = ""
            
        final_results[p_code] = {
            "id": p_code,
            "status": status,
            "reason": reason,
            "detected_keywords": detected_keywords
        }
        
    return final_results

def main():
    print("1. 유의 키워드 목록 로드 중...")
    try:
        keywords_df = pd.read_excel('keywords.xlsx')
        keywords_list = keywords_df.iloc[:, 0].dropna().astype(str).tolist()
        print(f"로드된 유의 키워드: {keywords_list}")
    except Exception as e:
        print(f"keywords.xlsx 읽기 실패: {e}")
        return

    print("2. 입력 데이터 로드 중...")
    try:
        input_df = pd.read_excel('input.xlsx')
    except Exception as e:
        print(f"input.xlsx 읽기 실패: {e}")
        return

    print("3. 로컬 텍스트 매칭 기반 초고속 검수 시작...")
    start_time = datetime.datetime.now()
    
    import asyncio
    # 비동기 함수 동기식 호출
    analysis_results_dict = asyncio.run(process_all_data(input_df, keywords_list))
    
    end_time = datetime.datetime.now()
    print(f"검수 완료! 소요 시간: {end_time - start_time}")
    
    print("4. 데이터 후처리 및 동적 열 매핑...")
    
    final_rows = []
    for index, row in input_df.iterrows():
        p_code = str(row.get('상품코드', ''))
        analysis = analysis_results_dict.get(p_code, {})
        
        result_row = {
            '플랫폼명': row.get('플랫폼명', ''),
            '상품코드': p_code,
            '상품명': row.get('상품명', ''),
            'status': analysis.get('status', '미처리'),
            'reason': analysis.get('reason', ''),
        }
        
        result_row['_detected_keywords'] = analysis.get('detected_keywords', [])
        final_rows.append(result_row)
        
    result_df = pd.DataFrame(final_rows)
    
    # 동적 열 생성
    max_keywords = result_df['_detected_keywords'].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    ).max()
    
    if pd.isna(max_keywords) or max_keywords == 0:
        max_keywords = 0
    else:
        max_keywords = int(max_keywords)
        
    for i in range(max_keywords):
        col_name = f'Keyword_{i+1}'
        result_df[col_name] = result_df['_detected_keywords'].apply(
            lambda x: x[i] if isinstance(x, list) and i < len(x) else ""
        )
        
    result_df.drop(columns=['_detected_keywords'], inplace=True)
    
    # 5. 엑셀 생성 및 저장
    today_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"검수결과_초고속_{today_str}.xlsx"
    
    result_df.to_excel(output_filename, index=False)
    print(f"완료! 대용량 결과가 {output_filename}에 저장되었습니다.")

if __name__ == '__main__':
    main()
