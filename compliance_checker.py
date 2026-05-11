import os
import datetime
import pandas as pd

# 성능 최적화를 위해 동기 함수로 변경 (main.py에서 asyncio.to_thread로 호출 권장)
def process_all_data(input_df, keywords_list):
    """
    파이썬 내부 문자열 매칭(Rule-based)을 최적화하여 유의 키워드를 검출합니다.
    """
    final_results = {}
    
    # 키워드 전처리: 미리 소문자화하여 루프 내 연산 최소화
    keyword_pairs = [(k.strip(), k.strip().lower()) for k in keywords_list if k.strip()]
    
    for index, row in input_df.iterrows():
        p_code = str(row.get('상품코드', ''))
        p_name = str(row.get('상품명', ''))
        p_name_lower = p_name.lower() # 상품명 소문자화 1회만 수행
        
        detected_keywords = []
        for kw_original, kw_lower in keyword_pairs:
            # 미리 소문자화된 키워드와 상품명 비교
            if kw_lower in p_name_lower:
                detected_keywords.append(kw_original)
        
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
    
    # 동기식 호출
    analysis_results_dict = process_all_data(input_df, keywords_list)
    
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
