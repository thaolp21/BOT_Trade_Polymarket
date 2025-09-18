"""
Tạo order_specs tự động cho cả 2 outcome:
- Outcome 0 = Up
- Outcome 1 = Down
- 10 lệnh mỗi bên, giá 0.01→0.10, size 14→5
"""

def generate_specs():
    
    prices = [round(0.01 * i, 2) for i in range(1, 11)]  # 0.01→0.10
    sizes = [14 - (i - 1) for i in range(1, 11)]         # 14→5
    specs = []

    for outcome_idx in [0, 1]:  # 0=Up, 1=Down
        for p, s in zip(prices, sizes):
            specs.append({
                "outcome_index": outcome_idx,
                "price": p,
                "size": s,
                "side": "buy",         # hoặc "sell" nếu muốn đặt lệnh bán
                "order_type": "GTC",
            })
    return specs

if __name__ == "__main__":
    # test
    s = generate_specs()
    for spec in s:
        print(spec)
