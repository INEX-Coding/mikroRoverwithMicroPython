from machine import Pin, PWM, I2C   
from ssd1306 import SSD1306_I2C    
import time                        

i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400000) # เชื่อมต่อจอที่ขา SDA=4, SCL=5
display = SSD1306_I2C(128, 64, i2c, addr=0x3C)    # กำหนดที่อยู่จอเป็น 0x3C

# --- ตั้งค่าเซอร์โวมอเตอร์สำหรับแขนยก (Lift Servo) ---
SV2_PIN = 19               # กำหนดขาเชื่อมต่อเซอร์โวตัวยกเป็นขา GPIO19 
sv_grip = PWM(Pin(SV2_PIN)) # สร้างออบเจกต์ PWM เพื่อควบคุมเซอร์โว 
sv_grip.freq(50)           # ตั้งค่าความถี่มาตรฐานสำหรับเซอร์โวมอเตอร์ที่ 50Hz

sw1 = Pin(8, Pin.IN, Pin.PULL_UP) # ปุ่ม SW1 สำหรับลดองศา 
sw2 = Pin(9, Pin.IN, Pin.PULL_UP) # ปุ่ม SW2 สำหรับเพิ่มองศา 

current_angle = 90 # เริ่มต้นตั้งองศาที่ 90 องศา (ตำแหน่งกึ่งกลาง) 

# ฟังก์ชันเทียบเคียงค่า (Mapping) เพื่อแปลงองศาเป็นค่าความกว้างพัลส์ (ns)
def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

# ฟังก์ชันสั่งการเซอร์โวมอเตอร์ตามองศา (0-180)
def set_servo_angle(servo_pwm, angle):
    if angle < 0: angle = 0      # จำกัดองศาไม่ให้ต่ำกว่า 0 
    if angle > 180: angle = 180  # จำกัดองศาไม่ให้เกิน 180 
    # แปลงองศาเป็นหน่วยนาโนวินาที (500,000ns - 2,500,000ns)
    duty_ns = map_value(angle, 0, 180, 500000, 2500000)
    servo_pwm.duty_ns(int(duty_ns))

# วนลูปรอจนกว่าจะกดปุ่ม SW1 เพื่อเริ่มโปรแกรมทดสอบ 
while sw1.value() == 1:
    time.sleep_ms(10)

set_servo_angle(sv_grip, current_angle) # เริ่มต้นสั่งเซอร์โวไปที่ตำแหน่ง 90

while True:
    sw1_pressed = (sw1.value() == 0) # อ่านสถานะปุ่ม SW1 
    sw2_pressed = (sw2.value() == 0) # อ่านสถานะปุ่ม SW2 
    
    # เงื่อนไข: ถ้ากด SW1 ให้ค่อยๆ ลดองศาลง 
    if sw1_pressed and not sw2_pressed and current_angle > 0:
        current_angle -= 1
    # เงื่อนไข: ถ้ากด SW2 ให้ค่อยๆ เพิ่มองศาขึ้น 
    elif not sw1_pressed and sw2_pressed and current_angle < 180:
        current_angle += 1
        
    set_servo_angle(sv_grip, current_angle) # อัปเดตตำแหน่งเซอร์โว
    display.fill(0)
    display.text("SV2 (GP19):", 0, 10, 1)      # แสดงชื่อขาเซอร์โว
    display.text(str(current_angle), 0, 25, 1) # แสดงเลของศาปัจจุบัน
    display.show()
    
    time.sleep_ms(50) # หน่วงเวลาเล็กน้อยเพื่อให้ขยับอย่างต่อเนื่องแต่ไม่เร็วเกินไป [cite: 1949]
