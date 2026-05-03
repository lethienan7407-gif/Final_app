from flask import Flask, render_template, request, jsonify
import numpy as np
import skfuzzy as fuzzy
from skfuzzy import control as ctrl
from datetime import datetime
import random

app = Flask(__name__)

# --- HỆ THỐNG LOGIC MỜ (Dựa trên cấu trúc chuẩn của bạn) ---
dist = ctrl.Antecedent(np.arange(0, 21, 1), 'dist')
weather = ctrl.Antecedent(np.arange(0, 11, 1), 'weather')
traffic = ctrl.Antecedent(np.arange(0, 11, 1), 'traffic')
rush_hour = ctrl.Antecedent(np.arange(0, 2, 1), 'rush_hour')
# Driver_dist không khai báo trong hệ mờ để đơn giản hóa logic giá

price_multiplier = ctrl.Consequent(np.arange(10, 31, 1), 'price_multiplier')

dist.automf(3, names=['gan', 'vua', 'xa'])
weather.automf(3, names=['dep', 'mua_nhe', 'mua_to'])
traffic.automf(3, names=['vang', 'on_dinh', 'tac_duong'])

rush_hour['binh_thuong'] = fuzzy.trimf(rush_hour.universe, [0, 0, 1])
rush_hour['cao_diem'] = fuzzy.trimf(rush_hour.universe, [0, 1, 1])

price_multiplier['re'] = fuzzy.trimf(price_multiplier.universe, [10, 10, 15])
price_multiplier['trung_binh'] = fuzzy.trimf(price_multiplier.universe, [12, 18, 25])
price_multiplier['dat'] = fuzzy.trimf(price_multiplier.universe, [20, 30, 30])

# --- HỆ LUẬT THEO TRỌNG SỐ BÁO CÁO (image_1a55b3.png) ---
# Quy tắc đẩy giá dựa trên Weather và Rush Hour
rule1 = ctrl.Rule(weather['mua_to'] | rush_hour['cao_diem'] | traffic['tac_duong'], price_multiplier['dat'])
rule2 = ctrl.Rule(weather['mua_nhe'] & traffic['on_dinh'], price_multiplier['trung_binh'])
rule3 = ctrl.Rule(weather['dep'] & traffic['vang'], price_multiplier['re'])
rule4 = ctrl.Rule(dist['xa'] & weather['dep'], price_multiplier['trung_binh'])

booking_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4])
simulation = ctrl.ControlSystemSimulation(booking_ctrl)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/booking')
def booking(): return render_template('booking.html')

@app.route('/calculate_price', methods=['POST'])
def calculate_price():
    data = request.get_json()
    dist_km = float(data.get('distance', 0))
    weather_val = float(data.get('weather', 2))

    # 1. Logic Thời gian (Giờ cao điểm)
    now = datetime.now()
    is_rush = 1 if (7 <= now.hour <= 9 or (16 <= now.hour <= 18 and now.minute >= 30) or now.hour == 19) else 0

    # 2. Tự động hóa Traffic dựa trên báo cáo
    # Đảm bảo traffic tương ứng với mức độ thời tiết
    if is_rush:
        auto_traffic = 9.0 # Cao điểm luôn tắc
    else:
        if weather_val >= 8: # Mưa to/Bão
            auto_traffic = 8.5
        elif weather_val >= 4: # Mưa nhẹ
            auto_traffic = 5.0
        else: # Trời đẹp
            auto_traffic = 2.0

    # 3. Biến Driver Distance chỉ để hiển thị
    d_dist = round(random.uniform(0.5, 3.5), 1)

    # 4. Tính toán hệ mờ
    simulation.input['dist'] = min(dist_km, 20)
    simulation.input['weather'] = weather_val
    simulation.input['traffic'] = auto_traffic
    simulation.input['rush_hour'] = is_rush
    simulation.compute()

    m_val = round(simulation.output['price_multiplier'] / 10, 1)

    # 5. Công thức tính giá tiền
    d_charge = max(0, dist_km - 2)
    p_bike = int((12000 + d_charge * 4000) * m_val)
    p_car4 = int((25000 + d_charge * 12000) * m_val)
    p_car7 = int((35000 + d_charge * 15000) * m_val)

    # Giả lập thời gian di chuyển
    avg_speed = 20 if is_rush or weather_val >= 8 else 35
    travel_time = int((dist_km / avg_speed) * 60) + random.randint(2, 5)

    return jsonify({
        'm_val': m_val,
        'dist_km': round(dist_km, 2),
        'time': travel_time,
        'driver_dist': d_dist,
        'prices': {
            'bike': p_bike,
            'car4': p_car4,
            'car7': p_car7
        }
    })

if __name__ == '__main__':
    app.run(debug=True)