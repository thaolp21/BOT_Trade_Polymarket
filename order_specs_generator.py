"""
Tạo order_specs tự động cho cả 2 outcome:
- Outcome 0 = Up
- Outcome 1 = Down
- 10 lệnh mỗi bên, giá 0.01→0.10, size 14→5
"""


from datetime import timedelta
from dateutil import parser

# --- CONFIGURABLE PARAMETERS ---
NUM_ORDERS_PER_SIDE = 5
PRICE_START = 0.05 # Giá bắt đầu từ 1%
PRICE_STEP = -0.01 # Giá tăng 1% mỗi lệnh
SIZE_START = 10 # Size lớn nhất bắt đầu giảm dần
SIZE_STEP = 0 # Size giảm 1 mỗi lệnh
SIDE = "buy"         # "buy" or "sell"
ORDER_TYPE = "GTD"   # "GTC" (hết hạn khi cancelled)  or "GTD" (hết hạn theo thời gian)
CANCEL_MINUTES = 8

def generate_specs(start_time_str: str):
    """
    Generate order specs for both outcomes using module-level config.
    """
    start_time = parser.isoparse(start_time_str)
    cancel_time = start_time + timedelta(minutes=CANCEL_MINUTES)
    expiration = int(cancel_time.timestamp())  # epoch UTC giây

    prices = [round(PRICE_START + PRICE_STEP * i, 2) for i in range(NUM_ORDERS_PER_SIDE)]
    sizes = [SIZE_START + SIZE_STEP * i for i in range(NUM_ORDERS_PER_SIDE)]
    specs = []

    for outcome_idx in [0, 1]:
        for p, s in zip(prices, sizes):
            specs.append({
                "outcome_index": outcome_idx,
                "price": p,
                "size": s,
                "side": SIDE,
                "order_type": ORDER_TYPE,
                "expiration": expiration
            })
    return specs

if __name__ == "__main__":
    # test
    test_start = "2025-09-18T07:15:00Z"
    s = generate_specs(test_start)
    print("First spec example:", s)