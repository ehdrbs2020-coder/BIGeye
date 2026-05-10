import pandas as pd
import random

def generate_samples(num_rows=5000):
    platforms = ['스마트스토어', '쿠팡', '11번가', '옥션', '지마켓', '무신사']
    
    base_products = [
        ('프리미엄 무선 청소기 흡입력 최고', True),
        ('빠른 체중감량 다이여트 보조제 1등', True),
        ('가정용 혈압계 안전 의료기기 인증', True),
        ('초경량 블루투스 이어폰', False),
        ('성인용 프리미엄 홍삼 스틱 세트', True),
        ('트렌디한 남성용 오버핏 셔츠', False),
        ('무소음 벽시계 인테리어 소품', False),
        ('다이어트 쉐이크 식사대용 최고', True),
        ('최신형 게이밍 마우스', False),
        ('의료기기 인증 허리 보호대', True)
    ]
    
    data_list = []
    for i in range(num_rows):
        plat = random.choice(platforms)
        code = f"PROD_{i:05d}"
        prod_name, has_keyword = random.choice(base_products)
        
        # 약간의 변형을 주어 중복 느낌 제거
        if i % 2 == 0:
            prod_name = f"[특가] {prod_name}"
        if i % 3 == 0:
            prod_name = f"{prod_name} (무료배송)"
            
        data_list.append({
            '플랫폼명': plat,
            '상품코드': code,
            '상품명': prod_name
        })
        
    df = pd.DataFrame(data_list)
    df.to_excel('input.xlsx', index=False)
    print(f"input.xlsx 파일이 생성되었습니다. (총 {num_rows}건)")

    keyword_data = {
        '유의키워드': ['최고', '다이어트', '체중감량', '1등', '의료기기', '성인']
    }
    kdf = pd.DataFrame(keyword_data)
    kdf.to_excel('keywords.xlsx', index=False)
    print("keywords.xlsx 파일이 생성되었습니다.")

if __name__ == '__main__':
    generate_samples(5000)
