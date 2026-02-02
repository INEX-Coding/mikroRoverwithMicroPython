from machine import Pin, PWM
import rp2
import time
UART_PIN   = 12    # ขา D3 รับสัญญาณจอย
BAUD_RATE  = 9600
# ตั้งค่า Servo (ต่อที่ขา 18)
sv1 = PWM(Pin(18))
sv1.freq(50)
def set_servo(servo, angle):
    # สูตรแปลงมุม (0-180 องศา) เป็นสัญญาณไฟฟ้า (Duty Cycle)
    duty = 500_000 + int(angle * 2_000_000 // 180)
    servo.duty_ns(duty)
BUTTONS = {
    0x0009: "L1",  # ปุ่ม L1
    0x0005: "L2"   # ปุ่ม L2
}
@rp2.asm_pio(in_shiftdir=rp2.PIO.SHIFT_LEFT, autopush=True, push_thresh=8)
def uart_rx():
    wait(0, pin, 0); set(x, 7) [10]; label("b")
    in_(pins, 1); nop() [5]; jmp(x_dec, "b")
sm = rp2.StateMachine(0, uart_rx, freq=8*BAUD_RATE, in_base=Pin(UART_PIN, Pin.IN, Pin.PULL_UP))
sm.active(1)
b1, wait = 0, 1
current_angle = 90
set_servo(sv1, current_angle)
print("Servo Test Ready: Press L1 / L2")
while True:
    if sm.rx_fifo():
        data = sm.get() & 0xFF
        if wait: 
            b1 = data; wait = 0
        else:
            code = (b1 << 8) | data
            name = BUTTONS.get(code)
            wait = 1
            if name:
                print(f"Pressed: {name}")
                if name == "L1":
                    # เพิ่มมุมทีละ 5 องศา
                    current_angle = current_angle + 1
                
                elif name == "L2":
                    # ลดมุมทีละ 5 องศา
                    current_angle = current_angle - 1
                # เพื่อป้องกันเซอร์โวหมุนจนเฟืองแตก
                if current_angle > 180: current_angle = 180
                if current_angle < 0:   current_angle = 0
                # ส่งคำสั่งไปที่เซอร์โว
                set_servo(sv1, current_angle)
                print(f"Angle: {current_angle}")
