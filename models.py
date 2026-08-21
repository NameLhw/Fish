"""
数据库模型 - 校园版咸鱼
"""
import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """用户模型"""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    student_id = db.Column(db.String(20), unique=True, nullable=False)  # 学号
    college = db.Column(db.String(100), nullable=False)  # 学院
    phone = db.Column(db.String(20))  # 联系电话
    avatar = db.Column(db.String(255), default="default_avatar.png")
    role = db.Column(db.String(20), default="student")  # admin / student
    status = db.Column(db.String(20), default="approved")  # pending / approved / rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联关系
    products = db.relationship("Product", backref="seller", lazy="dynamic")
    purchase_requests = db.relationship("PurchaseRequest", backref="requester", lazy="dynamic")
    messages_sent = db.relationship("Message", foreign_keys="Message.sender_id", backref="sender", lazy="dynamic")
    messages_received = db.relationship("Message", foreign_keys="Message.receiver_id", backref="receiver", lazy="dynamic")
    comments = db.relationship("Comment", backref="user", lazy="dynamic")
    orders_as_buyer = db.relationship("Order", foreign_keys="Order.buyer_id", backref="buyer", lazy="dynamic")
    orders_as_seller = db.relationship("Order", foreign_keys="Order.seller_id", backref="seller_ref", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_approved(self):
        return self.status == "approved"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "student_id": self.student_id,
            "college": self.college,
            "phone": self.phone,
            "avatar": self.avatar,
            "role": self.role,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class Category(db.Model):
    """商品分类"""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    sort = db.Column(db.Integer, default=0)
    products = db.relationship("Product", backref="category", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "sort": self.sort}


class Product(db.Model):
    """二手商品"""
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    original_price = db.Column(db.Float)  # 原价(可选)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    condition = db.Column(db.String(50), nullable=False)  # 新旧程度
    campus = db.Column(db.String(50), nullable=False)  # 校区
    transaction_method = db.Column(db.String(50), default="当面交易")
    images = db.Column(db.Text)  # JSON array of image paths
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / approved / rejected / sold / off_shelf
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    comments = db.relationship("Comment", backref="product", lazy="dynamic")
    orders = db.relationship("Order", backref="product", lazy="dynamic")

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "original_price": self.original_price,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "condition": self.condition,
            "campus": self.campus,
            "transaction_method": self.transaction_method,
            "images": json.loads(self.images) if self.images else [],
            "seller_id": self.seller_id,
            "seller_name": self.seller.username if self.seller else "",
            "seller_college": self.seller.college if self.seller else "",
            "seller_avatar": self.seller.avatar if self.seller else "",
            "status": self.status,
            "views": self.views,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class PurchaseRequest(db.Model):
    """求购信息"""
    __tablename__ = "purchase_requests"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    budget_min = db.Column(db.Float)
    budget_max = db.Column(db.Float)
    expected_condition = db.Column(db.String(50))  # 期望成色
    description = db.Column(db.Text)
    campus = db.Column(db.String(50))
    status = db.Column(db.String(20), default="active")  # active / fulfilled / closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.requester.username if self.requester else "",
            "college": self.requester.college if self.requester else "",
            "item_name": self.item_name,
            "budget_min": self.budget_min,
            "budget_max": self.budget_max,
            "expected_condition": self.expected_condition,
            "description": self.description,
            "campus": self.campus,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class Message(db.Model):
    """私信消息"""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.username if self.sender else "",
            "receiver_id": self.receiver_id,
            "receiver_name": self.receiver.username if self.receiver else "",
            "product_id": self.product_id,
            "content": self.content,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class Order(db.Model):
    """订单(线下交易约定)"""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="pending_communication")
    # pending_communication / pending_transaction / completed / cancelled
    meeting_location = db.Column(db.String(200))  # 交易地点
    meeting_time = db.Column(db.String(100))  # 交易时间
    remark = db.Column(db.Text)  # 备注
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        from config import ORDER_STATUSES
        return {
            "id": self.id,
            "product_id": self.product_id,
            "product_title": self.product.title if self.product else "",
            "product_price": self.product.price if self.product else 0,
            "product_image": (json.loads(self.product.images)[0] if self.product and self.product.images else ""),
            "buyer_id": self.buyer_id,
            "buyer_name": self.buyer.username if self.buyer else "",
            "seller_id": self.seller_id,
            "seller_name": self.seller_ref.username if self.seller_ref else "",
            "status": self.status,
            "status_text": ORDER_STATUSES.get(self.status, self.status),
            "meeting_location": self.meeting_location,
            "meeting_time": self.meeting_time,
            "remark": self.remark,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class Comment(db.Model):
    """商品留言"""
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else "",
            "user_avatar": self.user.avatar if self.user else "",
            "content": self.content,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }


class Report(db.Model):
    """违规举报"""
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=True)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending / handled / dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reporter = db.relationship("User", backref="reports")
    product = db.relationship("Product", backref="reports")

    def to_dict(self):
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "reporter_name": self.reporter.username if self.reporter else "",
            "product_id": self.product_id,
            "product_title": self.product.title if self.product else "",
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }
