"""
校园版咸鱼 - 主应用
一个面向高校学生的二手商品交易平台
"""
import os
import sys
import json
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, abort, send_from_directory
)
from werkzeug.utils import secure_filename
from models import db, User, Category, Product, PurchaseRequest, Message, Order, Comment, Report
from config import (
    SECRET_KEY, SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
    UPLOAD_FOLDER, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH, PER_PAGE,
    CAMPUSES, CONDITIONS, TRANSACTION_METHODS, ORDER_STATUSES
)

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

db.init_app(app)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ===================== 工具函数 =====================

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("请先登录", "warning")
            return redirect(url_for("login"))
        user = User.query.get(session["user_id"])
        if not user or not user.is_admin:
            flash("无权限访问", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user():
    if "user_id" in session:
        return User.query.get(session["user_id"])
    return None


def save_uploaded_files(files):
    """保存上传的图片文件, 返回路径列表"""
    saved_paths = []
    for f in files:
        if f and f.filename and allowed_file(f.filename):
            # Generate unique filename
            ext = f.filename.rsplit(".", 1)[1].lower()
            filename = f"product_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            f.save(filepath)
            saved_paths.append(filename)
    return saved_paths


# ===================== 上下文处理器 - 全局注入模板变量 =====================

@app.context_processor
def inject_globals():
    user = get_current_user()
    # 获取未读消息数
    unread_count = 0
    if user:
        unread_count = Message.query.filter_by(
            receiver_id=user.id, is_read=False
        ).count()
    return {
        "current_user": user,
        "all_categories": Category.query.order_by(Category.sort).all(),
        "campuses": CAMPUSES,
        "conditions": CONDITIONS,
        "transaction_methods": TRANSACTION_METHODS,
        "unread_count": unread_count,
    }


# ===================== 前端构建产物托管（CloudStudio 单端口） =====================
# 前端 npm run build 后由 Flask 在 /app/ 下托管，
# CloudStudio 只需暴露 8000 端口即可同时访问后端模板页面和前端页面。

FRONTEND_DIST = os.path.join(app.root_path, "frontend", "dist")


@app.route("/app/")
@app.route("/app/<path:filename>")
def frontend_app(filename="index.html"):
    """托管 Vue 构建产物，访问地址：/app/"""
    if not os.path.isdir(FRONTEND_DIST):
        abort(404, description="前端尚未构建，请在 frontend 目录执行 npm run build")
    # SPA 前端路由回退到 index.html（当前无 vue-router，预留兼容）
    if not os.path.isfile(os.path.join(FRONTEND_DIST, filename)):
        filename = "index.html"
    return send_from_directory(FRONTEND_DIST, filename)


@app.route("/api/health")
def api_health():
    """前端健康检查接口：验证前后端连通"""
    return {
        "code": 0,
        "data": {
            "service": "校园版咸鱼",
            "version": "1.0.0",
            "status": "ok",
        },
    }


# ===================== 首页 & 商品列表 =====================

@app.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    category_id = request.args.get("category_id", type=int)
    campus = request.args.get("campus", "")
    condition = request.args.get("condition", "")
    keyword = request.args.get("keyword", "")
    sort_by = request.args.get("sort", "newest")

    query = Product.query.filter_by(status="approved")

    if category_id:
        query = query.filter_by(category_id=category_id)
    if campus:
        query = query.filter_by(campus=campus)
    if condition:
        query = query.filter_by(condition=condition)
    if keyword:
        query = query.filter(Product.title.contains(keyword))

    if sort_by == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort_by == "price_desc":
        query = query.order_by(Product.price.desc())
    else:
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    products = [p.to_dict() for p in pagination.items]

    return render_template(
        "index.html",
        products=products,
        pagination=pagination,
        filters={
            "category_id": category_id,
            "campus": campus,
            "condition": condition,
            "keyword": keyword,
            "sort": sort_by,
        }
    )


# ===================== 商品详情 =====================

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    # 增加浏览量
    product.views += 1
    db.session.commit()

    comments = Comment.query.filter_by(product_id=product_id).order_by(
        Comment.created_at.desc()
    ).all()
    comment_list = [c.to_dict() for c in comments]

    # 检查是否有已有订单
    existing_order = None
    user = get_current_user()
    if user and user.id != product.seller_id:
        existing_order = Order.query.filter_by(
            product_id=product_id, buyer_id=user.id
        ).first()

    return render_template(
        "product_detail.html",
        product=product.to_dict(),
        comments=comment_list,
        existing_order=existing_order.to_dict() if existing_order else None,
    )


# ===================== 发布/编辑商品 =====================

@app.route("/publish", methods=["GET", "POST"])
@login_required
def publish_product():
    user = get_current_user()
    if not user.is_approved:
        flash("您的账号尚未通过审核，暂时无法发布商品", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", type=float)
        original_price = request.form.get("original_price", type=float)
        category_id = request.form.get("category_id", type=int)
        condition = request.form.get("condition", "")
        campus = request.form.get("campus", "")
        transaction_method = request.form.get("transaction_method", "当面交易")

        if not title or not price or not category_id or not condition or not campus:
            flash("请填写所有必填项", "danger")
            return redirect(url_for("publish_product"))

        # 处理图片上传
        files = request.files.getlist("images")
        saved_images = save_uploaded_files(files)
        images_json = json.dumps(saved_images) if saved_images else None

        product = Product(
            title=title,
            description=description,
            price=price,
            original_price=original_price,
            category_id=category_id,
            condition=condition,
            campus=campus,
            transaction_method=transaction_method,
            images=images_json,
            seller_id=user.id,
            status="approved",  # 默认直接通过, 也可改为 pending 待审核
        )
        db.session.add(product)
        db.session.commit()
        flash("商品发布成功！", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    return render_template("publish.html", product=None)


@app.route("/product/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    user = get_current_user()
    product = Product.query.get_or_404(product_id)

    if product.seller_id != user.id and not user.is_admin:
        abort(403)

    if request.method == "POST":
        product.title = request.form.get("title", "").strip()
        product.description = request.form.get("description", "").strip()
        product.price = request.form.get("price", type=float)
        product.original_price = request.form.get("original_price", type=float)
        product.category_id = request.form.get("category_id", type=int)
        product.condition = request.form.get("condition", "")
        product.campus = request.form.get("campus", "")
        product.transaction_method = request.form.get("transaction_method", "当面交易")

        # 新图片
        files = request.files.getlist("images")
        new_images = save_uploaded_files(files)
        if new_images:
            existing = json.loads(product.images) if product.images else []
            existing.extend(new_images)
            product.images = json.dumps(existing)

        product.updated_at = datetime.utcnow()
        db.session.commit()
        flash("商品更新成功！", "success")
        return redirect(url_for("product_detail", product_id=product.id))

    return render_template("publish.html", product=product.to_dict())


@app.route("/product/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    user = get_current_user()
    product = Product.query.get_or_404(product_id)

    if product.seller_id != user.id and not user.is_admin:
        abort(403)

    # 删除关联的图片文件
    if product.images:
        for img in json.loads(product.images):
            img_path = os.path.join(app.config["UPLOAD_FOLDER"], img)
            if os.path.exists(img_path):
                os.remove(img_path)

    db.session.delete(product)
    db.session.commit()
    flash("商品已删除", "success")
    return redirect(url_for("my_products"))


@app.route("/product/<int:product_id>/toggle-shelf", methods=["POST"])
@login_required
def toggle_shelf(product_id):
    user = get_current_user()
    product = Product.query.get_or_404(product_id)

    if product.seller_id != user.id:
        abort(403)

    if product.status == "off_shelf":
        product.status = "approved"
        flash("商品已上架", "success")
    else:
        product.status = "off_shelf"
        flash("商品已下架", "success")

    db.session.commit()
    return redirect(url_for("product_detail", product_id=product.id))


# ===================== 留言评论 =====================

@app.route("/product/<int:product_id>/comment", methods=["POST"])
@login_required
def add_comment(product_id):
    content = request.form.get("content", "").strip()
    if not content:
        flash("留言内容不能为空", "danger")
        return redirect(url_for("product_detail", product_id=product_id))

    user = get_current_user()
    comment = Comment(
        product_id=product_id,
        user_id=user.id,
        content=content,
    )
    db.session.add(comment)
    db.session.commit()
    flash("留言成功", "success")
    return redirect(url_for("product_detail", product_id=product_id))


# ===================== 求购管理 =====================

@app.route("/purchase-requests")
def purchase_request_list():
    page = request.args.get("page", 1, type=int)
    keyword = request.args.get("keyword", "")

    query = PurchaseRequest.query.filter_by(status="active")
    if keyword:
        query = query.filter(PurchaseRequest.item_name.contains(keyword))

    query = query.order_by(PurchaseRequest.created_at.desc())
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)
    requests_list = [r.to_dict() for r in pagination.items]

    return render_template(
        "purchase_list.html",
        requests=requests_list,
        pagination=pagination,
        keyword=keyword,
    )


@app.route("/purchase-requests/create", methods=["GET", "POST"])
@login_required
def create_purchase_request():
    user = get_current_user()
    if not user.is_approved:
        flash("账号未审核通过", "warning")
        return redirect(url_for("index"))

    if request.method == "POST":
        item_name = request.form.get("item_name", "").strip()
        budget_min = request.form.get("budget_min", type=float)
        budget_max = request.form.get("budget_max", type=float)
        expected_condition = request.form.get("expected_condition", "")
        description = request.form.get("description", "").strip()
        campus = request.form.get("campus", "")

        if not item_name:
            flash("请填写物品名称", "danger")
            return redirect(url_for("create_purchase_request"))

        pr = PurchaseRequest(
            user_id=user.id,
            item_name=item_name,
            budget_min=budget_min,
            budget_max=budget_max,
            expected_condition=expected_condition,
            description=description,
            campus=campus,
            status="active",
        )
        db.session.add(pr)
        db.session.commit()
        flash("求购信息发布成功！", "success")
        return redirect(url_for("purchase_request_list"))

    return render_template("purchase_publish.html")


@app.route("/purchase-requests/<int:pr_id>/delete", methods=["POST"])
@login_required
def delete_purchase_request(pr_id):
    user = get_current_user()
    pr = PurchaseRequest.query.get_or_404(pr_id)
    if pr.user_id != user.id and not user.is_admin:
        abort(403)
    db.session.delete(pr)
    db.session.commit()
    flash("求购信息已删除", "success")
    return redirect(url_for("purchase_request_list"))


# ===================== 私信聊天 =====================

@app.route("/messages")
@login_required
def message_list():
    """会话列表"""
    user = get_current_user()
    # 获取与每个用户的最新消息
    sent_ids = {m.receiver_id for m in Message.query.filter_by(sender_id=user.id).all()}
    received_ids = {m.sender_id for m in Message.query.filter_by(receiver_id=user.id).all()}
    contact_ids = sent_ids | received_ids

    conversations = []
    for cid in contact_ids:
        contact = User.query.get(cid)
        if not contact:
            continue
        latest_msg = Message.query.filter(
            ((Message.sender_id == user.id) & (Message.receiver_id == cid)) |
            ((Message.sender_id == cid) & (Message.receiver_id == user.id))
        ).order_by(Message.created_at.desc()).first()

        unread = Message.query.filter_by(
            sender_id=cid, receiver_id=user.id, is_read=False
        ).count()

        if latest_msg and contact:
            conversations.append({
                "contact_id": cid,
                "contact_name": contact.username,
                "contact_college": contact.college,
                "contact_avatar": contact.avatar or "",
                "latest_content": latest_msg.content,
                "latest_time": latest_msg.created_at.strftime("%Y-%m-%d %H:%M"),
                "unread": unread,
            })

    # 按最新消息时间排序
    conversations.sort(key=lambda x: x["latest_time"], reverse=True)

    return render_template("messages.html", conversations=conversations)


@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):
    """与某个用户的私聊"""
    current = get_current_user()
    contact = User.query.get_or_404(user_id)

    if user_id == current.id:
        flash("不能和自己聊天", "warning")
        return redirect(url_for("message_list"))

    # 标记消息为已读
    Message.query.filter_by(
        sender_id=user_id, receiver_id=current.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()

    # 获取聊天记录
    messages = Message.query.filter(
        ((Message.sender_id == current.id) & (Message.receiver_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id == current.id))
    ).order_by(Message.created_at.asc()).all()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            msg = Message(
                sender_id=current.id,
                receiver_id=user_id,
                content=content,
            )
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("chat", user_id=user_id))

    return render_template(
        "chat.html",
        contact=contact.to_dict(),
        messages=[m.to_dict() for m in messages],
    )


# ===================== 订单管理 =====================

@app.route("/orders")
@login_required
def order_list():
    """我的订单"""
    user = get_current_user()
    tab = request.args.get("tab", "all")  # all / buyer / seller
    status_filter = request.args.get("status", "")

    if tab == "seller":
        query = Order.query.filter_by(seller_id=user.id)
    elif tab == "buyer":
        query = Order.query.filter_by(buyer_id=user.id)
    else:
        query = Order.query.filter(
            (Order.buyer_id == user.id) | (Order.seller_id == user.id)
        )

    if status_filter:
        query = query.filter_by(status=status_filter)

    query = query.order_by(Order.created_at.desc())
    orders = [o.to_dict() for o in query.all()]

    return render_template(
        "orders.html",
        orders=orders,
        tab=tab,
        status_filter=status_filter,
        order_statuses=ORDER_STATUSES,
    )


@app.route("/product/<int:product_id>/create-order", methods=["POST"])
@login_required
def create_order(product_id):
    user = get_current_user()
    product = Product.query.get_or_404(product_id)

    if product.seller_id == user.id:
        flash("不能购买自己的商品", "danger")
        return redirect(url_for("product_detail", product_id=product_id))

    if product.status == "sold":
        flash("该商品已售出", "danger")
        return redirect(url_for("product_detail", product_id=product_id))

    # 检查是否已有订单
    existing = Order.query.filter_by(
        product_id=product_id, buyer_id=user.id
    ).filter(Order.status != "cancelled").first()

    if existing:
        flash("您已有一个进行中的订单", "info")
        return redirect(url_for("order_list"))

    order = Order(
        product_id=product_id,
        buyer_id=user.id,
        seller_id=product.seller_id,
        status="pending_communication",
        remark=request.form.get("remark", "").strip(),
    )
    db.session.add(order)
    db.session.commit()
    flash("已创建订单，请与卖家沟通交易细节", "success")
    return redirect(url_for("order_list"))


@app.route("/order/<int:order_id>/update-status", methods=["POST"])
@login_required
def update_order_status(order_id):
    user = get_current_user()
    order = Order.query.get_or_404(order_id)

    # 买卖双方都可以更新状态
    if order.buyer_id != user.id and order.seller_id != user.id:
        abort(403)

    new_status = request.form.get("status")
    meeting_location = request.form.get("meeting_location", "").strip()
    meeting_time = request.form.get("meeting_time", "").strip()

    if new_status not in ORDER_STATUSES:
        flash("无效的订单状态", "danger")
        return redirect(url_for("order_list"))

    order.status = new_status
    if meeting_location:
        order.meeting_location = meeting_location
    if meeting_time:
        order.meeting_time = meeting_time
    order.updated_at = datetime.utcnow()

    # 如果完成交易，标记商品为已售出
    if new_status == "completed":
        product = order.product
        if product:
            product.status = "sold"

    db.session.commit()
    flash(f"订单状态已更新为: {ORDER_STATUSES[new_status]}", "success")
    return redirect(url_for("order_list"))


# ===================== 举报 =====================

@app.route("/product/<int:product_id>/report", methods=["POST"])
@login_required
def report_product(product_id):
    user = get_current_user()
    reason = request.form.get("reason", "").strip()

    if not reason:
        flash("请填写举报原因", "danger")
        return redirect(url_for("product_detail", product_id=product_id))

    report = Report(
        reporter_id=user.id,
        product_id=product_id,
        reason=reason,
        status="pending",
    )
    db.session.add(report)
    db.session.commit()
    flash("举报已提交，管理员将尽快处理", "success")
    return redirect(url_for("product_detail", product_id=product_id))


# ===================== 用户认证 =====================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        student_id = request.form.get("student_id", "").strip()
        college = request.form.get("college", "").strip()
        phone = request.form.get("phone", "").strip()

        if not username or not password or not student_id or not college:
            flash("请填写所有必填项", "danger")
            return redirect(url_for("register"))

        # 检查用户名/学号是否已存在
        if User.query.filter_by(username=username).first():
            flash("用户名已存在", "danger")
            return redirect(url_for("register"))
        if User.query.filter_by(student_id=student_id).first():
            flash("该学号已注册", "danger")
            return redirect(url_for("register"))

        user = User(
            username=username,
            student_id=student_id,
            college=college,
            phone=phone,
            role="student",
            status="approved",  # 默认直接通过
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash("注册成功！请登录", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            flash(f"欢迎回来，{user.username}！", "success")
            return redirect(url_for("index"))
        else:
            flash("用户名或密码错误", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("已退出登录", "info")
    return redirect(url_for("index"))


# ===================== 个人中心 =====================

@app.route("/profile")
@login_required
def profile():
    user = get_current_user()
    my_products = Product.query.filter_by(seller_id=user.id).order_by(
        Product.created_at.desc()
    ).all()
    my_requests = PurchaseRequest.query.filter_by(user_id=user.id).order_by(
        PurchaseRequest.created_at.desc()
    ).all()
    return render_template(
        "profile.html",
        my_products=[p.to_dict() for p in my_products],
        my_requests=[r.to_dict() for r in my_requests],
    )


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = get_current_user()

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        avatar_file = request.files.get("avatar")

        if phone:
            user.phone = phone

        if avatar_file and avatar_file.filename and allowed_file(avatar_file.filename):
            ext = avatar_file.filename.rsplit(".", 1)[1].lower()
            filename = f"avatar_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            avatar_file.save(filepath)
            user.avatar = filename

        db.session.commit()
        flash("资料更新成功", "success")
        return redirect(url_for("profile"))

    return render_template("edit_profile.html")


@app.route("/my-products")
@login_required
def my_products():
    user = get_current_user()
    products = Product.query.filter_by(seller_id=user.id).order_by(
        Product.created_at.desc()
    ).all()
    return render_template(
        "my_products.html",
        products=[p.to_dict() for p in products],
    )


# ===================== 管理后台 =====================

@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "total_users": User.query.count(),
        "pending_users": User.query.filter_by(status="pending").count(),
        "total_products": Product.query.count(),
        "pending_products": Product.query.filter_by(status="pending").count(),
        "total_orders": Order.query.count(),
        "active_orders": Order.query.filter(
            Order.status.in_(["pending_communication", "pending_transaction"])
        ).count(),
        "pending_reports": Report.query.filter_by(status="pending").count(),
        "total_categories": Category.query.count(),
    }
    # 最近注册的用户
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    # 最近发布的商品
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(5).all()
    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_users=[u.to_dict() for u in recent_users],
        recent_products=[p.to_dict() for p in recent_products],
    )


@app.route("/admin/products")
@admin_required
def admin_products():
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    query = Product.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Product.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    products = [p.to_dict() for p in pagination.items]
    return render_template(
        "admin/products.html",
        products=products,
        pagination=pagination,
        status_filter=status,
    )


@app.route("/admin/product/<int:product_id>/review", methods=["POST"])
@admin_required
def admin_review_product(product_id):
    action = request.form.get("action")  # approve / reject
    product = Product.query.get_or_404(product_id)

    if action == "approve":
        product.status = "approved"
        flash("商品已审核通过", "success")
    elif action == "reject":
        product.status = "rejected"
        flash("商品已驳回", "info")
    elif action == "off_shelf":
        product.status = "off_shelf"
        flash("商品已强制下架", "info")

    db.session.commit()
    return redirect(url_for("admin_products"))


@app.route("/admin/users")
@admin_required
def admin_users():
    page = request.args.get("page", 1, type=int)
    query = User.query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=20, error_out=False)
    users = [u.to_dict() for u in pagination.items]
    return render_template("admin/users.html", users=users, pagination=pagination)


@app.route("/admin/user/<int:user_id>/update-status", methods=["POST"])
@admin_required
def admin_update_user_status(user_id):
    status = request.form.get("status")
    user = User.query.get_or_404(user_id)
    if status in ("approved", "pending", "rejected"):
        user.status = status
        db.session.commit()
        flash(f"用户 {user.username} 状态已更新", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sort = request.form.get("sort", 0, type=int)
        if name:
            cat = Category(name=name, sort=sort)
            db.session.add(cat)
            db.session.commit()
            flash("分类添加成功", "success")
        return redirect(url_for("admin_categories"))

    categories = Category.query.order_by(Category.sort).all()
    return render_template("admin/categories.html", categories=categories)


@app.route("/admin/categories/<int:cat_id>/delete", methods=["POST"])
@admin_required
def admin_delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    if cat.products.count() > 0:
        flash("该分类下还有商品，无法删除", "danger")
        return redirect(url_for("admin_categories"))
    db.session.delete(cat)
    db.session.commit()
    flash("分类已删除", "success")
    return redirect(url_for("admin_categories"))


@app.route("/admin/reports")
@admin_required
def admin_reports():
    status = request.args.get("status", "pending")
    reports = Report.query.filter_by(status=status).order_by(
        Report.created_at.desc()
    ).all()
    return render_template(
        "admin/reports.html",
        reports=[r.to_dict() for r in reports],
        status_filter=status,
    )


@app.route("/admin/report/<int:report_id>/handle", methods=["POST"])
@admin_required
def admin_handle_report(report_id):
    action = request.form.get("action")  # handled / dismissed
    report = Report.query.get_or_404(report_id)
    if action in ("handled", "dismissed"):
        report.status = action
        db.session.commit()
        flash("举报已处理", "success")
    return redirect(url_for("admin_reports"))


# ===================== 文件访问 =====================

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ===================== 错误页面 =====================

@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", code=404, message="页面不存在"), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="无权限访问"), 403


@app.errorhandler(413)
def too_large(e):
    return render_template("error.html", code=413, message="文件太大，最大5MB"), 413


# ===================== 启动 =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    # 端口可通过环境变量配置（本地默认 5000，CloudStudio / 前端代理模式设为 8000）
    PORT = int(os.environ.get("PORT", 5000))

    try:
        from waitress import serve

        print()
        print("=" * 40)
        print("  校园版咸鱼 服务已启动")
        print(f"  后端页面: http://127.0.0.1:{PORT}/")
        print(f"  前端页面: http://127.0.0.1:{PORT}/app/  (需先 npm run build)")
        print("  管理员账号: admin / admin123")
        print("  提示: CloudStudio 用户请用端口面板中")
        print(f"        {PORT} 端口的公网链接访问上述路径")
        print("  按 Ctrl+C 停止服务")
        print("=" * 40)
        print()

        serve(app, host="0.0.0.0", port=PORT)
    except OSError as e:
        if "Address already in use" in str(e) or e.errno in (48, 98):
            print()
            print("!" * 40)
            print(f"  ✗ 端口 {PORT} 已被占用！")
            print(f"  可能是上次的进程未正常退出。")
            print(f"  解决方法: 执行以下命令杀掉旧进程后重试")
            print(f"    lsof -t -i:{PORT} | xargs kill -9")
            print(f"  或: fuser -k {PORT}/tcp")
            print(f"  或: pkill -f app.py")
            print("!" * 40)
        else:
            raise
    except ImportError:
        import warnings

        warnings.filterwarnings("ignore", message=".*development server.*")
        app.run(host="0.0.0.0", port=PORT, debug=True)
