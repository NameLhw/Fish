import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "campus-flea-market-secret-key-2024"

# Database
SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "campus_flea.db")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Upload settings
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

# Pagination
PER_PAGE = 10

# Campuses
CAMPUSES = ["本部校区", "东校区", "北校区", "南校区", "独墅湖校区", "阳澄湖校区"]

# Product conditions
CONDITIONS = ["全新", "几乎全新", "轻微使用痕迹", "明显使用痕迹", "较旧"]

# Transaction methods
TRANSACTION_METHODS = ["当面交易", "自取", "邮寄"]

# Order statuses
ORDER_STATUSES = {
    "pending_communication": "待沟通",
    "pending_transaction": "待交易",
    "completed": "已完成",
    "cancelled": "已取消",
}
