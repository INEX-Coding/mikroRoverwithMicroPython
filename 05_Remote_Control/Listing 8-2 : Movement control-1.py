from machine import Pin, PWM 
import rp2                   # เรียกใช้คำสั่งคุม PIO (ตัวอ่านสัญญาณความเร็วสูง)
import time

UART_PIN   = 12    # ขา D3 (GPIO 12) ที่เสียบสายสีเหลืองจากจอย
BAUD_RATE  = 9600  # ความเร็วในการส่งข้อมูลของจอย Wireless-X14
TIMEOUT_MS = 150   # เวลาความปลอดภัย (ถ้าจอยเงียบเกิน 0.15 วิ ให้หยุดหุ่น)
SPEED      = 60    # ความเร็วในการวิ่งของหุ่นยนต์ (ค่า 0 ถึง 100)

# m1 = มอเตอร์ซ้าย, m2 = มอเตอร์ขวา
m1a = PWM(Pin(13)); m1a.freq(1000) 
m1b = PWM(Pin(14)); m1b.freq(1000)
m2a = PWM(Pin(16)); m2a.freq(1000)
m2b = PWM(Pin(17)); m2b.freq(1000)

# ฟังก์ชันแปลงเลข 0-100 ให้เป็นเลขที่บอร์ดเข้าใจ (0-65535)
def set_speed(pin, value):
    duty = int(max(0, min(100, value)) * 655.35)
    pin.duty_u16(duty) 

# ฟังก์ชันสั่งหยุด
def stop():
    m1a.duty_u16(0); m1b.duty_u16(0) # ตัดไฟมอเตอร์ซ้าย
    m2a.duty_u16(0); m2b.duty_u16(0) # ตัดไฟมอเตอร์ขวา

# ฟังก์ชันเดินหน้า
def forward(s):  
    m1a.duty_u16(0); set_speed(m1b, s) # ล้อซ้ายเดินหน้า
    m2a.duty_u16(0); set_speed(m2b, s) # ล้อขวาเดินหน้า

# ฟังก์ชันถอยหลัง
def backward(s):
    set_speed(m1a, s); m1b.duty_u16(0) # ล้อซ้ายถอย
    set_speed(m2a, s); m2b.duty_u16(0) # ล้อขวาถอย

BUTTONS = {
    0x0011: "LU",  
    0x0081: "LD"
}

# สร้างโปรแกรมภาษา Assembly จำลองการทำงานเป็นตัวรับ UART
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0)      # 1. รอจนกว่าจะมีสัญญาณเริ่ม (Start Bit เป็น 0)
    set(x, 7) [10]       # 2. ตั้งตัวนับจำนวน 8 รอบ (สำหรับ 8 บิต)
    label("b")           # 3. จุดปักหมุดสำหรับวนลูป
    in_(pins, 1)         # 4. อ่านค่ามา 1 บิต เก็บใส่กล่อง
    nop() [5]            # 5. รอเวลานิดนึง (ให้ตรงจังหวะความเร็ว)
    jmp(x_dec, "b")      # 6. วนกลับไปทำข้อ 4 จนครบ 8 ครั้ง
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1) # สั่งให้เริ่มทำงาน
print("Ready! Forward/Backward Only")

b1 = 0                 # ตัวแปรพักข้อมูลไบต์แรก
wait = 1               # ตัวแปรสถานะ (1=รอไบต์แรก, 0=รอไบต์สอง)
press = 0              # สถานะการกดปุ่ม (0=ไม่ได้กด, 1=กำลังกด)
last = time.ticks_ms() # เวลาล่าสุดที่มีข้อมูลเข้ามา
while True:
    now = time.ticks_ms() # ดูเวลาปัจจุบัน
    # ถ้า "มีการกดปุ่มอยู่" และ "เวลาผ่านไปเกิน 0.15 วิ" โดยไม่มีข้อมูลใหม่
    if press and time.ticks_diff(now, last) > TIMEOUT_MS:
        stop()    # สั่งหยุดรถทันที
        press = 0 # รีเซ็ตสถานะว่าปล่อยมือแล้ว

    if sm.rx_fifo(): # ถ้ามีข้อมูลมารออยู่ในกล่องรับ (FIFO)
        data = sm.get() & 0xFF # หยิบข้อมูลออกมา 1 ตัว
        last = now             # อัปเดตเวลาล่าสุดทันที (เพื่อไม่ให้ timeout ทำงาน)
        if wait: 
            b1 = data; wait = 0 
        else:
            code = (b1 << 8) | data 
            # แปลงรหัสตัวเลข
            name = BUTTONS.get(code, "Unknown")
            wait = 1 # เตรียมตัวรอรับชุดใหม่
            if name != "Unknown": 
                press = 1         
                if   name == "LU": forward(SPEED)   
                elif name == "LD": backward(SPEED) 
