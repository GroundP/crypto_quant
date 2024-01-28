from decimal import Decimal, getcontext

# Decimal 모듈의 정밀도 설정 (원하는 정밀도로 조절 가능)
#getcontext().prec = 4  # 예시로 4자리까지 정밀도 설정

value = round(350 / 2357.86 / 0.01) * 0.01
print((str(value)))
#print(Decimal(value))
# 부동 소수점 값을 Decimal 객체로 변환
original_value = Decimal('16.60000000000001')
print(str(original_value))

# Decimal 객체로 계산
result = original_value * Decimal('2.5')

print(result)  # 출력: 41.5
