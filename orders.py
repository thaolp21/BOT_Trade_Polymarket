import requests
import hmac
import hashlib
import json
import time
from web3 import Web3

class PolymarketTrader:
    def __init__(self, api_key, api_secret, private_key=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.private_key = private_key
        self.base_url = "https://clob.polymarket.com"
        self.market_url = "https://gamma-api.polymarket.com"
        
        # Kết nối đến Polygon network
        self.w3 = Web3(Web3.HTTPProvider("https://polygon-rpc.com"))
        
    def create_signature(self, message):
        """Tạo chữ ký HMAC cho request"""
        return hmac.new(
            self.api_secret.encode(), 
            message.encode(), 
            hashlib.sha256
        ).hexdigest()
    
    def get_market_id(self, slug):
        """Lấy market ID từ slug"""
        url = f"{self.market_url}/markets"
        response = requests.get(url)
        
        if response.status_code == 200:
            markets = response.json()
            for market in markets:
                if market.get('slug') == slug:
                    return market.get('id')
        return None
    
    def create_batch_orders(self, slug, orders):
        """
        Tạo nhiều lệnh cùng lúc
        
        orders: Danh sách các lệnh cần đặt
        Ví dụ: [
            {"side": "buy", "price": "0.45", "size": "1000000"},
            {"side": "sell", "price": "0.55", "size": "1000000"}
        ]
        """
        # Lấy market ID
        market_id = self.get_market_id(slug)
        if not market_id:
            raise Exception(f"Không tìm thấy market với slug: {slug}")
        
        # Chuẩn bị batch orders
        batch_orders = []
        nonce = int(time.time() * 1000)
        
        for i, order in enumerate(orders):
            batch_orders.append({
                "market": market_id,
                "side": order["side"],
                "price": order["price"],
                "size": order["size"],
                "nonce": nonce + i,  # Mỗi order có nonce khác nhau
                "expiration": int((time.time() + 86400) * 1000)  # 24 giờ
            })
        
        # Tạo signature
        message = json.dumps(batch_orders, separators=(",", ":"))
        signature = self.create_signature(message)
        
        # Gửi request
        url = f"{self.base_url}/orders/batch"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}:{signature}"
        }
        
        response = requests.post(url, json=batch_orders, headers=headers)
        return response.json()
    
    def get_order_book(self, slug):
        """Lấy thông tin order book của thị trường"""
        market_id = self.get_market_id(slug)
        if not market_id:
            raise Exception(f"Không tìm thấy market với slug: {slug}")
        
        url = f"{self.base_url}/order-book?market={market_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            return response.json()
        return None

# Sử dụng
if __name__ == "__main__":
    # Thay thế bằng thông tin của bạn
    API_KEY = "your_api_key_here"
    API_SECRET = "your_api_secret_here"
    PRIVATE_KEY = "your_private_key_here"  # Cần cho giao dịch thực
    
    # Khởi tạo trader
    trader = PolymarketTrader(API_KEY, API_SECRET, PRIVATE_KEY)
    
    # Slug của thị trường
    slug = "btc-up-or-down-15m-1758125700"
    
    # Kiểm tra order book trước khi đặt lệnh
    order_book = trader.get_order_book(slug)
    print("Order book:", order_book)
    
    # Tạo nhiều lệnh
    orders = [
        {"side": "buy", "price": "0.45", "size": "1000000"},  # Mua ở 0.45
        {"side": "buy", "price": "0.44", "size": "2000000"},  # Mua ở 0.44
        {"side": "sell", "price": "0.55", "size": "1000000"},  # Bán ở 0.55
        {"side": "sell", "price": "0.56", "size": "2000000"}   # Bán ở 0.56
    ]
    
    try:
        # Đặt nhiều lệnh
        result = trader.create_batch_orders(slug, orders)
        print("Kết quả đặt lệnh:", result)
    except Exception as e:
        print("Lỗi khi đặt lệnh:", e)