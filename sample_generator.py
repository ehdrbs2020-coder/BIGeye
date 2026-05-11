import pandas as pd
import random

def generate_samples(num_rows=10000):
    platforms = ['스마트스토어', '쿠팡', '11번가', '옥션', '지마켓', '무신사']
    
    # 대규모 테스트를 위해 1000개의 유의 키워드 생성
    large_keywords = [f"키워드_{i}" for i in range(1000)]
    
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
    
    # 키워드 중 일부를 상품명에 강제로 넣기
    for i in range(10):
        large_keywords[i] = base_products[i][0].split()[-1]

    data_list = []
    for i in range(num_rows):
        plat = random.choice(platforms)
        code = f"PROD_{i:05d}"
        prod_name, _ = random.choice(base_products)
        
        # 10% 확률로 임의의 유의 키워드 삽입
        if random.random() < 0.1:
            prod_name = f"{prod_name} {random.choice(large_keywords)}"
            
        data_list.append({
            '플랫폼명': plat,
            '상품코드': code,
            '상품명': prod_name
        })
        
    df = pd.DataFrame(data_list)
    df.to_excel('input.xlsx', index=False)
    print(f"input.xlsx 파일이 생성되었습니다. (총 {num_rows}건)")

    keyword_data = {
        '유의키워드': large_keywords
    }
    kdf = pd.DataFrame(keyword_data)
    kdf.to_excel('keywords.xlsx', index=False)
    print(f"keywords.xlsx 파일이 생성되었습니다. (총 {len(large_keywords)}건)")

if __name__ == '__main__':
    generate_samples(10000)
