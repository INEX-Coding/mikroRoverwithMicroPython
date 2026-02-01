from machine import Pin, PWM
import time

# --- ตั้งค่าการควบคุมมอเตอร์ (Motor Setup) ---
# มอเตอร์ 1 (ซ้าย) ต่อกับขา 13 และ 14
M1_B = PWM(Pin(13))
M1_A = PWM(Pin(14))

# มอเตอร์ 2 (ขวา) ต่อกับขา 16 และ 17 
M2_B = PWM(Pin(16))
M2_A = PWM(Pin(17))

# กำหนดความถี่ 1000Hz สำหรับมอเตอร์ทั้ง 2 ล้อ
M1_A.freq(1000); M1_B.freq(1000)
M2_A.freq(1000); M2_B.freq(1000)

# ปุ่มสำหรับกดเริ่มภารกิจ (SW1 ขา 8)
start_button = Pin(8, Pin.IN, Pin.PULL_UP)

# ฟังก์ชันจำกัดค่าความเร็วให้อยู่ในช่วง 0-100% และแปลงเป็นค่า PWM (0-65535)
def _map_constrain(speed):
    if speed < 0: speed = 0
    if speed > 100: speed = 100
    return int(speed / 100 * 65535)

# --- กลุ่มฟังก์ชันควบคุมทิศทาง (Movement Functions) ---
def fd(speed): # เดินหน้า
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def bk(speed): # ถอยหลัง
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def sl(speed): # หมุนซ้าย (Spin Left)
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def sr(speed): # หมุนขวา (Spin Right)
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def tl(speed): # เลี้ยวซ้าย (Turn Left)
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def tr(speed): # เลี้ยวขวา (Turn Right)
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)

def ao(): # หยุดทำงาน (All Off)
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)

# ฟังก์ชันเดินหน้าแบบแยกความเร็วล้อซ้าย-ขวา
def fd2(speed1, speed2):
    pwm1 = _map_constrain(speed1)
    pwm2 = _map_constrain(speed2)
    M1_A.duty_u16(pwm1); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm2); M2_B.duty_u16(0)

# ฟังก์ชันถอยหลังแบบแยกความเร็วล้อซ้าย-ขวา
def bk2(speed1, speed2):
    pwm1 = _map_constrain(speed1)
    pwm2 = _map_constrain(speed2)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm1)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm2)

# "รอ" จนกว่าจะมีการกดปุ่ม SW1 ที่หุ่นยนต์
while start_button.value() == 1:
    time.sleep_ms(10)

# เมื่อกดปุ่มแล้ว หุ่นยนต์จะเริ่มทำการทดสอบการเคลื่อนที่ทุกทิศทางตามลำดับ (ท่าละ 1 วินาที)
fd(50); time.sleep(1) # เดินหน้า 50%
ao(); time.sleep(1)   # หยุด
bk(50); time.sleep(1) # ถอยหลัง 50%
ao(); time.sleep(1)   # หยุด
sl(50); time.sleep(1) # หมุนซ้าย
ao(); time.sleep(1)   # หยุด
sr(50); time.sleep(1) # หมุนขวา
ao(); time.sleep(1)   # หยุด
tl(50); time.sleep(1) # เลี้ยวซ้าย
ao(); time.sleep(1)   # หยุด
tr(50); time.sleep(1) # เลี้ยวขวา
ao(); time.sleep(1)   # หยุด
