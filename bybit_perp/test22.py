import pandas as pd
import numpy as np

# 랜덤한 데이터 생성
data = {
    'A': np.random.rand(50),
    'B': np.random.rand(50),
    'C': np.random.rand(50),
    'D': np.random.rand(50),
    'E': np.random.rand(50),
    'F': np.random.rand(50),
    'G': np.random.rand(50),
    'H': np.random.rand(50)
}

# 데이터프레임 생성
df = pd.DataFrame(data)

# CSV 파일로 저장
df.to_csv('data.csv', index=False)