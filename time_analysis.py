import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import os

# CSV 저장 파일 위치
FILE_PATH = "time_log.csv"

# 카테고리 색상 정의
CATEGORY_COLORS = {
    '생산적': "#4C91AF",  # 블루
    '비생산적': "#F35F98"  # 핑크
}

# matplotlib 한글 설정(환경 따라 조정)
plt.rcParams["axes.unicode_minus"] = False

# 운영체제별 폰트 설정 (예시)
try:
    # Windows 사용자
    plt.rcParams['font.family'] = 'Malgun Gothic'
    # plt.rcParams['font.family'] = 'NanumGothic' # 나눔고딕 설치시
except:
    try:
        # Mac 사용자
        plt.rcParams['font.family'] = 'AppleGothic'
        # plt.rcParams['font.family'] = 'NanumGothic' # 나눔고딕 설치시
    except:
        # Linux 사용자 (예: 우분투에서 'sudo apt-get install fonts-nanum' 등으로 나눔 폰트 설치 필요)
        plt.rcParams['font.family'] = 'NanumGothic'
        # 모든 시도 실패 시 경고
        print("경고: 한글 폰트 설정에 실패했습니다. 그래프에 한글이 깨져 보일 수 있습니다.")
ㄴ

# -----------------------------
# 데이터 로드 또는 초기화
# -----------------------------
def load_or_initialize_data():
    """CSV 파일을 불러오거나 없으면 새 DataFrame 생성."""
    
    if os.path.exists(FILE_PATH):
        try:
            df = pd.read_csv(
                FILE_PATH,
                parse_dates=["Date", "Start_Time", "End_Time"],
                converters={"Duration": lambda x: pd.to_timedelta(x)}
            )
            
            # Date 타입 보장
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            
            # Hours 컬럼 없다면 계산하여 추가
            if "Hours" not in df.columns:
                df["Hours"] = df["Duration"].dt.total_seconds() / 3600

            print(f"기존 데이터 {len(df)}개 불러옴.")
            return df
        except Exception as e:
            print(f"데이터 로드 오류: {e}")

    # 새 구조 생성    
    df = pd.DataFrame({
        'Date': pd.Series([], dtype='datetime64[ns]'),
        'Start_Time': pd.Series([], dtype='datetime64[ns]'),
        'End_Time': pd.Series([], dtype='datetime64[ns]'),
        'Activity': pd.Series([], dtype='object'),
        'Category': pd.Series([], dtype='object'),
        'Duration': pd.Series([], dtype='timedelta64[ns]'),
        'Hours': pd.Series([], dtype='float64')
    })
    return df


# -----------------------------
# 활동 기록 추가 기능
# -----------------------------
def add_activity(df, activity, category, start_str, end_str):
    """활동을 DataFrame에 추가하고 저장."""
    
    try:
        today = datetime.now().date()

        start = datetime.strptime(f"{today} {start_str}", "%Y-%m-%d %H:%M")
        end = datetime.strptime(f"{today} {end_str}", "%Y-%m-%d %H:%M")

        if end <= start:
            # 1. 종료 시간이 시작 시간보다 이전이면 (예: 23:00 -> 01:00), 다음 날로 처리
            if end < start:
                end += timedelta(days=1)
            # 2. 시작 시간과 종료 시간이 같으면 (0시간 활동) 기록 거부
            else: # end == start
                print("시작 시간과 종료 시간이 같습니다. 0시간 활동은 기록할 수 없습니다.")
                return df

        duration = end - start
        hours = duration.total_seconds() / 3600
        
        new_row = {
            "Date": today,
            "Start_Time": start,
            "End_Time": end,
            "Activity": activity,
            "Category": category,
            "Duration": duration,
            "Hours": hours
        }

        df.loc[len(df)] = new_row

        df.to_csv(FILE_PATH, index=False)
        print(f"'{activity}' 기록 저장 완료! ({hours:.2f}시간)")

    except ValueError:
        print("시간 형식 오류: HH:MM 형태로 입력해야 합니다.")
    except Exception as e:
        print(f"활동 추가 중 오류 발생: {e}")

    return df


# -----------------------------
# 오늘 성찰 리포트 시각화
# -----------------------------
def visualize_daily_report(df):
    """오늘 활동 데이터를 기반으로 파이 차트 2개 시각화"""
    
    if df.empty:
        print("기록이 없습니다.")
        return

    try:
        if df["Date"].dtype != 'datetime64[ns]':
            df["Date"] = pd.to_datetime(df["Date"], errors='coerce').dt.normalize()
    except Exception as e:
        print(f"Date 컬럼 타입 변환 오류: {e}. 시각화 중단.")
        return
    
    today = datetime.now().date()
    today_df = df[df["Date"].dt.date == today]

    if today_df.empty:
        print("오늘 기록이 없습니다.")
        return


    # --------------------
    # 요약 텍스트 출력
    # [수정 1]: 함수 외부의 요약 코드를 함수 내부로 이동
    # --------------------
    total_time = today_df["Hours"].sum()
    # df가 비어있지 않으므로 idxmax() 사용 가능
    top_act = today_df.loc[today_df["Hours"].idxmax()] 

    print("\n오늘 하루 리포트\n---------------------------")
    print(f"날짜: {today}")
    print(f"총 사용 시간: {total_time:.1f}시간")
    print(f"기록된 활동 개수: {len(today_df)}개")
    print(f"가장 오래한 활동: {top_act['Activity']} ({top_act['Hours']:.1f}h)")
    print("\n---------------------------")


    # --------------------
    # 서브플롯 생성: 1행 2열
    # --------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7)) 
    fig.suptitle(f"📆 {today} 시간 분석 리포트", fontsize=18, y=1.02) # 전체 제목

    # --------------------
    # 첫 번째 파이 차트: 활동별 시간 비율
    # --------------------
    activity_summary = today_df.groupby("Activity")["Hours"].sum().sort_values(ascending=False)
        
    # 활동 레이블을 '활동명 (시간h)' 형식으로 변경
    labels_activity = [f"{act} ({hr:.1f}h)" for act, hr in activity_summary.items()]

    ax1.pie(
        activity_summary,
        labels=labels_activity,
        autopct="%.1f%%",
        startangle=90,
        wedgeprops={'edgecolor':'white', 'linewidth': 1}
    )
    ax1.set_title("활동별 시간 비율", fontsize=14)
    ax1.axis('equal') 


    # --------------------
    # 두 번째 파이 차트: 생산적 / 비생산적 비율
    # --------------------
    category_summary = today_df.groupby("Category")["Hours"].sum().sort_values(ascending=False)
    # 카테고리별로 정의된 색상 사용. 없는 카테고리는 'gray' 기본값
    colors = [CATEGORY_COLORS.get(cat, "gray") for cat in category_summary.index]
        
    # 카테고리 레이블을 '카테고리명 (시간h)' 형식으로 변경
    labels_category = [f"{cat} ({hr:.1f}h)" for cat, hr in category_summary.items()]

    ax2.pie(
        category_summary,
        labels=labels_category,
        autopct="%.1f%%",
        colors=colors,
        startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1}
    )
    ax2.set_title("📊 생산적 vs 비생산적 비율", fontsize=14)
    ax2.axis('equal')

    plt.tight_layout(rect=[0, 0.03, 1, 0.98]) # 전체 제목을 위해 여백 조정
    plt.show() # 두 그래프를 동시에 출력
    
    print("\n오늘 하루 잘 마무리했어요.\n")


# -----------------------------
# 실행 UI (CLI 메뉴)
# -----------------------------
def run_app():
    print("\n==============================")
    print("DAILY REFLECTION APP")
    print("==============================")

    global df
    df = load_or_initialize_data()

    while True:
        print("\n--- 메뉴 ---")
        print("1. 활동 추가")
        print("2. 오늘 리포트 보기")
        print("3. 종료")

        user = input("선택: ").strip()

        if user == "1":
            activity = input("활동 내용: ")
            category = input("카테고리 (생산적/비생산적): ")

            if category not in CATEGORY_COLORS:
                print("카테고리는 '생산적' 또는 '비생산적'만 입력 가능.")
                continue

            start_time = input("시작 시간 (HH:MM): ")
            end_time   = input("종료 시간 (HH:MM): ")

            df = add_activity(df, activity, category, start_time, end_time)

        elif user == "2":
            visualize_daily_report(df)

        elif user == "3":
            print("오늘도 수고했어요:) 다음에 만나요!")
            break

        else:
            print("1, 2, 3 중에서 선택해주세요.")



# -----------------------------
# 프로그램 실행
# -----------------------------
if __name__ == "__main__":
    run_app()
