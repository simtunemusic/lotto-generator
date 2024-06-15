import requests
import random
import csv
import schedule
import time
from collections import Counter
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# API 키 설정
WEATHER_API_KEY = 'd4a828a7cd2ef69eae63ec87aaba688'
NASA_API_KEY = '8kc8ru1I70hLhwr8sOdpM1wUpVCTVpDrELWbItiB'
NOAA_API_KEY = 'mwtBWFzDKRnXTtAXldxjnaLRfxvMnGpe'

# API URL 설정
WEATHER_API_URL = f"http://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={WEATHER_API_KEY}"
MAGNETIC_API_URL = f"https://api.noaa.gov/magnetic?date={datetime.today().strftime('%Y-%m-%d')}&apikey={NOAA_API_KEY}"
SOLAR_ACTIVITY_API_URL = f"https://api.nasa.gov/DONKI/FLR?startDate={datetime.today().strftime('%Y-%m-%d')}&api_key={NASA_API_KEY}"

# 전역 변수로 데이터 저장
weather_data = None
magnetic_data = None
solar_activity_data = None

def read_lotto_numbers(filename):
    past_lotto_numbers = []
    try:
        with open(filename, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                past_lotto_numbers.append([int(num) for num in row])
        print("CSV 파일에서 읽은 로또 번호:", past_lotto_numbers)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
    except ValueError:
        print("Error: Ensure the CSV file contains only numbers.")
    return past_lotto_numbers

# 업로드된 CSV 파일의 경로
csv_file_path = 'lotto_numbers.csv'
past_lotto_numbers = read_lotto_numbers(csv_file_path)

def update_weather_data():
    global weather_data
    try:
        response = requests.get(WEATHER_API_URL)
        response.raise_for_status()
        weather_data = response.json()
        print("Weather data updated.")
    except requests.RequestException as e:
        print(f"Error fetching weather data: {e}")

def update_magnetic_data():
    global magnetic_data
    try:
        response = requests.get(MAGNETIC_API_URL)
        response.raise_for_status()
        magnetic_data = response.json()
        print("Magnetic data updated.")
    except requests.RequestException as e:
        print(f"Error fetching magnetic data: {e}")

def update_solar_activity_data():
    global solar_activity_data
    try:
        response = requests.get(SOLAR_ACTIVITY_API_URL)
        response.raise_for_status()
        solar_activity_data = response.json()
        print("Solar activity data updated.")
    except requests.RequestException as e:
        print(f"Error fetching solar activity data: {e}")

def schedule_updates():
    schedule.every().saturday.at("19:00").do(update_weather_data)
    schedule.every().saturday.at("19:00").do(update_magnetic_data)
    schedule.every().saturday.at("19:00").do(update_solar_activity_data)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

def analyze_past_numbers(past_numbers):
    all_numbers = [num for sublist in past_numbers for num in sublist]
    number_frequency = Counter(all_numbers)
    most_common_numbers = [num for num, count in number_frequency.most_common(6)]
    return most_common_numbers

def generate_lotto_numbers(past_numbers, user_favorites=None, exclude_numbers=None):
    if weather_data and magnetic_data and solar_activity_data:
        randomness_seed = (
            int(weather_data['main']['temp']) +
            int(magnetic_data['kp_index']) +
            len(solar_activity_data)
        )
    else:
        randomness_seed = random.randint(1, 100)
    
    random.seed(randomness_seed)
    
    if user_favorites is None:
        user_favorites = []
    
    if exclude_numbers is None:
        exclude_numbers = []

    common_numbers = analyze_past_numbers(past_numbers)
    selected_numbers = set(user_favorites)
    all_numbers = set(range(1, 46)) - set(exclude_numbers)
    
    while len(selected_numbers) < 6:
        selected_numbers.add(random.choice(list(all_numbers - selected_numbers)))
    
    return sorted(selected_numbers)

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    user_favorites = data.get('favorites', [])
    exclude_numbers = data.get('excludes', [])
    
    if len(user_favorites) > 5:
        return jsonify({"error": "행운의 숫자는 최대 5개까지 입력할 수 있습니다."}), 400

    lotto_sets = []
    for _ in range(10):
        lotto_numbers = generate_lotto_numbers(past_lotto_numbers, user_favorites, exclude_numbers)
        lotto_sets.append(lotto_numbers)
    
    return jsonify({"lotto_sets": lotto_sets})

if __name__ == "__main__":
    # 스케줄러 설정 및 실행
    schedule_updates()
    import threading
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    app.run(debug=True)
