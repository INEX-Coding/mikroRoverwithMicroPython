from machine import Pin, PWM
import rp2
import time

UART_PIN   = 12    # ขา D3
BAUD_RATE  = 9600
TIMEOUT_MS = 150   # เวลาเช็คปล่อยมือ
SPEED      = 60    # ความเร็ว (0-100)

# m1 = ซ้าย, m2 = ขวา
m1a = PWM(Pin(13)); m1a.freq(1000) 
m1b = PWM(Pin(14)); m1b.freq(1000)
m2a = PWM(Pin(16)); m2a.freq(1000)
m2b = PWM(Pin(17)); m2b.freq(1000)

# ตัวช่วยแปลงความเร็ว (0-100 -> 0-65535)
def set_speed(pin, value):
    duty = int(max(0, min(100, value)) * 655.35)
    pin.duty_u16(duty)

def stop():
    m1a.duty_u16(0); m1b.duty_u16(0)
    m2a.duty_u16(0); m2b.duty_u16(0)

def forward(s):  # เดินหน้า
    m1a.duty_u16(0); set_speed(m1b, s) # ซ้ายเดินหน้า (แก้แล้ว)
    m2a.duty_u16(0); set_speed(m2b, s) # ขวาเดินหน้า (แก้แล้ว)

def backward(s): # ถอยหลัง
    set_speed(m1a, s); m1b.duty_u16(0) # ซ้ายถอย (แก้แล้ว)
    set_speed(m2a, s); m2b.duty_u16(0) # ขวาถอย (แก้แล้ว)

def turn_left(s): # เลี้ยวซ้าย (หมุนตัว)
    set_speed(m1a, s); m1b.duty_u16(0) 
    m2a.duty_u16(0); set_speed(m2b, s)

def turn_right(s): # เลี้ยวขวา (หมุนตัว)
    m1a.duty_u16(0); set_speed(m1b, s)
    set_speed(m2a, s); m2b.duty_u16(0)

BUTTONS = {
    0x0011:"LU", 0x0021:"LL", 0x0081:"LD", 0x0041:"LR"
}

@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0); set(x, 7) [10]; label("b")
    in_(pins, 1); nop() [5]; jmp(x_dec, "b")

sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)
print("Ready!")

b1, wait, press, last = 0, 1, 0, time.ticks_ms()

while True:
    now = time.ticks_ms()

    # --- เช็คปล่อยมือ (Safety) ---
    if press and time.ticks_diff(now, last) > TIMEOUT_MS:
        stop() # เรียกฟังก์ชันหยุด
        print("-> หยุด")
        press = 0

    # --- รับข้อมูล ---
    if sm.rx_fifo():
        data = sm.get() & 0xFF; last = now
        
        if wait: 
            b1 = data; wait = 0
        else:
            code = (b1 << 8) | data
            name = BUTTONS.get(code, "Unknown")
            wait = 1
            
            if code not in (0, 1):
                press = 1
                # --- เรียกใช้ฟังก์ชันที่แยกไว้ ---
                if   name == "LU": forward(SPEED)     # เดินหน้า
                elif name == "LD": backward(SPEED)    # ถอยหลัง
                elif name == "LL": turn_left(SPEED)   # เลี้ยวซ้าย
                elif name == "LR": turn_right(SPEED)  # เลี้ยวขวา
