import time
import re
import pandas as pd
import csv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def rating_to_exact_tier(rating):
    if pd.isna(rating):
        return "Unrated"
    rating = float(rating)
    if rating >= 3000:
        return "Master"
    elif rating >= 2950:
        return "Ruby I"
    elif rating >= 2900:
        return "Ruby II"
    elif rating >= 2850:
        return "Ruby III"
    elif rating >= 2800:
        return "Ruby IV"
    elif rating >= 2700:
        return "Ruby V"
    elif rating >= 2600:
        return "Diamond I"
    elif rating >= 2500:
        return "Diamond II"
    elif rating >= 2400:
        return "Diamond III"
    elif rating >= 2300:
        return "Diamond IV"
    elif rating >= 2200:
        return "Diamond V"
    elif rating >= 2100:
        return "Platinum I"
    elif rating >= 2000:
        return "Platinum II"
    elif rating >= 1900:
        return "Platinum III"
    elif rating >= 1750:
        return "Platinum IV"
    elif rating >= 1600:
        return "Platinum V"
    elif rating >= 1400:
        return "Gold I"
    elif rating >= 1250:
        return "Gold II"
    elif rating >= 1100:
        return "Gold III"
    elif rating >= 950:
        return "Gold IV"
    elif rating >= 800:
        return "Gold V"
    elif rating >= 650:
        return "Silver I"
    elif rating >= 500:
        return "Silver II"
    elif rating >= 400:
        return "Silver III"
    elif rating >= 300:
        return "Silver IV"
    elif rating >= 200:
        return "Silver V"
    elif rating >= 150:
        return "Bronze I"
    elif rating >= 120:
        return "Bronze II"
    elif rating >= 90:
        return "Bronze III"
    elif rating >= 60:
        return "Bronze IV"
    elif rating >= 30:
        return "Bronze V"
    else:
        return "Unrated"




#1. 사용자 닉네임 입력
nickname = input("본인의 Solved.ac 닉네임을 입력하세요: ")

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument('--headless')  # 필요에 따라 헤드리스 모드 사용
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
wait = WebDriverWait(driver, 4)

def get_algorithm_tags(user_name):
    url = f"https://solved.ac/profile/{user_name}"
    driver.get(url)
    time.sleep(1)

    tags_ratings_problems = {}

    # 1. 사용자 티어와 레이팅을 API로 가져오기
    try:
        api_url = f"https://solved.ac/api/v3/user/show?handle={user_name}"
        response = requests.get(api_url)
        if response.status_code == 200:
            user_data = response.json()
            user_rating = user_data.get('rating', 0)
            user_tier_num = user_data.get('tier', 0)
            user_tier_alt = rating_to_exact_tier(user_rating)
            print(f"API로 가져온 사용자 티어: {user_tier_alt}, 레이팅: {user_rating}")
        else:
            print(f"API 요청 실패: 상태 코드 {response.status_code}")
            user_tier_alt = "Unrated"
            user_rating = 0
    except Exception as e:
        print(f"API 요청 중 오류: {e}")
        user_tier_alt = "Unrated"
        user_rating = 0

    # 사용자 티어와 레이팅을 딕셔너리에 저장
    tags_ratings_problems['user_tier'] = user_tier_alt
    tags_ratings_problems['user_rating'] = user_rating

    # 2. 페이지를 끝까지 스크롤
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)

    # 3. "더 보기" 버튼을 두 번 클릭
    try:
        for _ in range(2):
            driver.execute_script("""
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].innerText.includes('더 보기')) {
                    buttons[i].click();
                    break;
                }
            }
            """)
            print("JavaScript로 '더 보기' 버튼을 클릭했습니다.")
            time.sleep(1)
    except Exception as e:
        print(f"더 보기 버튼 클릭 오류: {e}")

    # 4. 다시 페이지를 끝까지 스크롤
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(0.5)

    # 5. 태그별 레이팅 및 티어 수집
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        print(f"태그 테이블에서 {len(rows)}개의 행을 찾았습니다.")

        for index, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 4:
                    continue

                # 태그명 추출
                tag_name_element = cells[0].find_element(By.TAG_NAME, "a")
                tag_name = tag_name_element.text.strip()
                tag_name_cleaned = tag_name.replace('#', '').strip()

                # 푼 문제 수 추출
                problems_solved = cells[1].text.strip()

                # 티어와 레이팅 추출
                rating_td = cells[3]
                tier_img = rating_td.find_element(By.TAG_NAME, "img")
                tier = tier_img.get_attribute("alt").strip()

                rating_text = rating_td.text.strip()
                rating_value_match = re.search(r'(\d+)', rating_text)
                rating_value = rating_value_match.group(1) if rating_value_match else "0"

                combined_rating = f"{tier}, {rating_value}"

                # 미리 정의된 태그 리스트에 있는 경우에만 추가
                if tag_name_cleaned in tag_list:
                    tags_ratings_problems[f"{tag_name_cleaned}_rating"] = combined_rating
                    tags_ratings_problems[f"{tag_name_cleaned}_problems_solved"] = problems_solved
                    print(f"{index + 1}번째 행 - 태그: {tag_name_cleaned}, 티어와 레이팅: {combined_rating}")
            except Exception as e:
                print(f"{index + 1}번째 행 파싱 중 오류: {e}")

    except Exception as e:
        print(f"알고리즘 태그 및 티어 수집 오류: {e}")
        for tag in tag_list:
            tags_ratings_problems[f"{tag}_rating"] = "Unrated, 0"
            tags_ratings_problems[f"{tag}_problems_solved"] = "0"
        return tags_ratings_problems

    # 태그 리스트에 없는 경우 기본값 설정
    for tag in tag_list:
        if f"{tag}_rating" not in tags_ratings_problems:
            tags_ratings_problems[f"{tag}_rating"] = "Unrated, 0"
            tags_ratings_problems[f"{tag}_problems_solved"] = "0"

    return tags_ratings_problems

# 3. 태그 리스트 정의
tag_list = [
    "브루트포스 알고리즘",
    "구현",
    "수학",
    "사칙연산",
    "그리디 알고리즘",
    "이분 탐색",
    "기하학",
    "그래프 이론",
    "그래프 탐색",
    "조합론",
    "너비 우선 탐색",
    "다이나믹 프로그래밍",
    "백트래킹",
    "자료 구조",
    "깊이 우선 탐색",
    "시뮬레이션",
    "문자열",
    "정수론",
    "트리"
]

# 4. 알고리즘 태그 데이터 가져오기
algorithm_data = get_algorithm_tags(nickname)

# 사용자 티어와 레이팅 출력
print(f"사용자 티어: {algorithm_data['user_tier']}, 레이팅: {algorithm_data['user_rating']}")

# 드라이버 종료
driver.quit()

# 5. 사용자 데이터를 딕셔너리 리스트로 저장
user_data_list = []
for tag in tag_list:
    rating_info = algorithm_data.get(f"{tag}_rating", "Unrated, 0")
    tier, rating = rating_info.split(",")
    user_data_list.append({
        'User': nickname,
        'user_tier': algorithm_data['user_tier'],
        'Algorithm': tag,
        'Tier': tier.strip(),
        'Rating': rating.strip(),
        'Problems Solved': algorithm_data.get(f"{tag}_problems_solved", "0")
    })

# 6. DataFrame으로 변환
user_df = pd.DataFrame(user_data_list)

# 7. 평균 레이팅 데이터 불러오기
average_ratings = pd.read_csv('solved_ac_tier_weighted_average_quantile.csv')

# 8. 사용자 티어 가져오기
user_tier_name = algorithm_data['user_tier']

# 9. 평균 레이팅 데이터에서 사용자 티어에 해당하는 행 추출
tier_data = average_ratings[average_ratings['티어'] == user_tier_name]

if tier_data.empty:
    print(f"평균 레이팅 데이터에 {user_tier_name} 티어에 대한 정보가 없습니다.")
else:
    # 10. 비교 결과를 저장할 열 추가
    user_df['Comparison'] = ''
    user_df['Universal_alg_tier'] = ''
    user_df['Universal_alg_rating'] = ''
    user_df['User_alg_tier'] = ''
    user_df['User_alg_rating'] = ''

    # 11. 각 알고리즘 태그별로 비교 수행
    for idx, row in user_df.iterrows():
        algorithm = row['Algorithm']
        user_alg_rating = float(row['Rating'])
        user_alg_tier = row['Tier'].strip()

        # 평균 레이팅 데이터의 해당 열 이름
        avg_rating_col = algorithm + ' 레이팅'

        if avg_rating_col in tier_data.columns:
            average_rating_info = tier_data.iloc[0][avg_rating_col]
            avg_rating_str, avg_tier = average_rating_info.split(', ')
            avg_rating = float(avg_rating_str)
            avg_tier = avg_tier.strip()

            # 비교 로직 수정
            diff = user_alg_rating - avg_rating
            threshold = avg_rating * 0.1  # 평균 레이팅의 10%를 임계값으로 설정

            if user_alg_rating == 0.0 and avg_rating == 0.0:
                status = 'Normal'
            elif avg_rating == 0.0:
                status = 'Cannot compare'
            else:
                if abs(diff) <= threshold:
                    status = 'Normal'
                elif diff > threshold:
                    status = 'High'
                else:
                    status = 'low'

            # 비교 결과 문자열 생성 및 저장 (영어로 표현)
            comparison_str = f"{status}, universal {algorithm} rating for this tier: {avg_rating}, {avg_tier}, User's {algorithm} tier: {user_alg_tier}, Rating: {user_alg_rating}"
            user_df.at[idx,'Comparison'] = status
            user_df.at[idx,'Universal_alg_tier'] = avg_tier
            user_df.at[idx,'Universal_alg_rating'] = avg_rating
            user_df.at[idx,'User_alg_tier'] = user_alg_tier
            user_df.at[idx,'User_alg_rating'] = user_alg_rating
        else:
            comparison_str = f"No data available for universal {algorithm} rating at this tier."


        # 비교 결과 저장
        # user_df.at[idx, 'Comparison'] = comparison_str
        print(comparison_str)

    # 12. 결과 출력
    print(user_df)

    # 13. 결과를 CSV 파일로 저장
    user_df.to_csv(f'{nickname}_data_with_comparison.csv', index=False, encoding='utf-8-sig')
