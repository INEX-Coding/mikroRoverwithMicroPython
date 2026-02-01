from machine import Pin, PWM, I2C, ADC 
from ssd1306 import SSD1306_I2C       
import time                          

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000) # กำหนดขา SDA=4, SCL=5 ความเร็ว 400kHz 
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)    # สร้างออบเจกต์จอภาพที่แอดเดรส 0x3C 

M1_B = PWM(Pin(13)); M1_A = PWM(Pin(14)) # มอเตอร์ 1 (ล้อซ้าย) 
M2_B = PWM(Pin(16)); M2_A = PWM(Pin(17)) # มอเตอร์ 2 (ล้อขวา) 
M1_A.freq(1000); M1_B.freq(1000)         # ตั้งความถี่ PWM 1000Hz 
M2_A.freq(1000); M2_B.freq(1000)

start_button = Pin(8, Pin.IN, Pin.PULL_UP) # ปุ่ม SW1 (ขา 8) 
adc_sensor = ADC(Pin(27))                 # เซนเซอร์วัดระยะทาง (ขา 27) 

# ฟังก์ชันคำนวณความเร็ว (0-100%) เป็นค่า PWM (0-65535)
def _map_constrain(speed):
    if speed < 0: speed = 0
    if speed > 100: speed = 100
    return int(speed / 100 * 65535)

# --- ฟังก์ชันควบคุมทิศทาง ---
def fd(speed): # เดินหน้า 
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def bk(speed): # ถอยหลัง 
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def sl(speed): # เลี้ยวซ้ายหมุนอยู่กับที่ 
    pwm = _map_constrain(speed)
    M1_A.duty_u16(0); M1_B.duty_u16(pwm)
    M2_A.duty_u16(pwm); M2_B.duty_u16(0)

def sr(speed): # เลี้ยวขวาหมุนอยู่กับที่ 
    pwm = _map_constrain(speed)
    M1_A.duty_u16(pwm); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(pwm)

def ao(): # หยุดจ่ายไฟมอเตอร์ทั้งหมด 
    M1_A.duty_u16(0); M1_B.duty_u16(0)
    M2_A.duty_u16(0); M2_B.duty_u16(0)

# แสดงข้อความเตรียมพร้อมที่หน้าจอ
display.fill(0)
display.text("Press SW1", 0, 10, 1)
display.text("to Start...", 0, 25, 1)
display.show()

# วนลูปรอการกดปุ่ม SW1 เพื่อเริ่มทำงาน 
while start_button.value() == 1:
    time.sleep_ms(10)

speed = 50
fd(speed) # เริ่มเดินหน้าด้วยความเร็ว 50% 

while True:
    # อ่านค่าจากเซนเซอร์และคำนวณระยะทางในหน่วยเซนติเมตร 
    raw_value_16bit = adc_sensor.read_u16()
    distance = raw_value_16bit // 640 # แปลงค่า ADC เป็นระยะทางโดยประมาณ 
    
    # อัปเดตข้อมูลบนจอ OLED ตลอดเวลาขณะเคลื่อนที่ 
    display.fill(0)
    display.text("Moving Forward", 0, 10, 1)
    display.text("Dist: " + str(distance) + " cm", 0, 25, 1)
    display.show()
    
    # ตรวจสอบสิ่งกีดขวางในระยะน้อยกว่า 17 ซม. 
    if distance < 17:
        ao() # หยุดรถทันที 
        display.fill(0)
        display.text("Obstacle!", 0, 10, 1)
        display.text("Avoiding...", 0, 25, 1)
        display.show()
        
        # --- ขั้นตอนการหลบสิ่งกีดขวาง ---
        time.sleep_ms(500)
        sr(speed); time.sleep_ms(400) # เลี้ยวขวาหลบ 
        ao(); time.sleep_ms(200)
        fd(speed); time.sleep_ms(500) # เดินหน้าผ่าน 
        ao(); time.sleep_ms(200)
        sl(speed); time.sleep_ms(400) # เลี้ยวซ้ายกลับเข้าทางหลัก 
        ao(); time.sleep_ms(200)
        fd(speed); time.sleep_ms(600) # เดินหน้าผ่านสิ่งกีดขวาง 
        ao(); time.sleep_ms(200)
        sl(speed); time.sleep_ms(400) # เลี้ยวซ้ายอีกครั้ง 
        ao(); time.sleep_ms(200)
        fd(speed); time.sleep_ms(500) # เดินหน้า 
        ao(); time.sleep_ms(200)
        sr(speed); time.sleep_ms(400) # เลี้ยวขวาตั้งลำ 
        ao(); time.sleep_ms(200)
        
        fd(speed) # กลับเข้าสู่โหมดเดินหน้าตรวจจับตามปกติ 
        
    time.sleep_ms(50) 
