"""
数据库初始化脚本 - 创建表并填充初始数据
"""
import os
import sys

# Add project dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, User, Category, Product, PurchaseRequest, Comment
from config import CAMPUSES


def init_db():
    with app.app_context():
        # 删除旧数据库(如果存在)
        db_path = os.path.join(os.path.dirname(__file__), "campus_flea.db")
        if os.path.exists(db_path):
            os.remove(db_path)
            print("[OK] 已删除旧数据库")

        # 创建所有表
        db.create_all()
        print("[OK] 数据库表创建完成")

        # 创建管理员账号
        admin = User(
            username="admin",
            student_id="000000",
            college="管理中心",
            phone="13800000000",
            role="admin",
            status="approved",
        )
        admin.set_password("admin123")
        db.session.add(admin)

        # 创建测试学生账号
        test_users = [
            ("张三", "20230001", "计算机科学与技术学院", "13800000001"),
            ("李四", "20230002", "电子信息学院", "13800000002"),
            ("王五", "20230003", "数学科学学院", "13800000003"),
        ]
        for name, sid, college, phone in test_users:
            u = User(
                username=name,
                student_id=sid,
                college=college,
                phone=phone,
                role="student",
                status="approved",
            )
            u.set_password("123456")
            db.session.add(u)

        db.session.commit()
        print("[OK] 已创建管理员和测试用户账号")
        print("      管理员: admin / admin123")
        print("      测试学生: 张三/李四/王五, 密码均为 123456")

        # 创建商品分类
        categories = [
            "教材书籍", "电子产品", "生活用品", "运动器材",
            "服装鞋包", "乐器", "美妆护肤", "其他",
        ]
        for idx, name in enumerate(categories):
            c = Category(name=name, sort=idx)
            db.session.add(c)

        db.session.commit()
        print(f"[OK] 已创建 {len(categories)} 个商品分类")

        # 获取用户和分类引用
        zhang = User.query.filter_by(username="张三").first()
        li = User.query.filter_by(username="李四").first()
        wang = User.query.filter_by(username="王五").first()

        cat_book = Category.query.filter_by(name="教材书籍").first()
        cat_elec = Category.query.filter_by(name="电子产品").first()
        cat_life = Category.query.filter_by(name="生活用品").first()
        cat_sport = Category.query.filter_by(name="运动器材").first()
        cat_cloth = Category.query.filter_by(name="服装鞋包").first()
        cat_music = Category.query.filter_by(name="乐器").first()

        # 创建测试商品
        products = [
            Product(
                title="高等数学第七版 同济大学",
                description="九成新，笔记很少，适合期末复习。包邮可议价。",
                price=15.00, original_price=45.90,
                category_id=cat_book.id, condition="几乎全新",
                campus="独墅湖校区", transaction_method="当面交易",
                seller_id=zhang.id, status="approved", views=128,
            ),
            Product(
                title="线性代数 同济版 第六版",
                description="封面有轻微折痕，内页干净无笔记。",
                price=10.00, original_price=32.80,
                category_id=cat_book.id, condition="轻微使用痕迹",
                campus="本部校区", transaction_method="当面交易",
                seller_id=li.id, status="approved", views=56,
            ),
            Product(
                title="大学物理教程 第三版",
                description="上下册全套，有少量铅笔批注，不影响阅读。",
                price=20.00, original_price=58.00,
                category_id=cat_book.id, condition="轻微使用痕迹",
                campus="阳澄湖校区", transaction_method="自取",
                seller_id=wang.id, status="approved", views=34,
            ),
            Product(
                title="罗技 G304 无线游戏鼠标",
                description="用了半年，功能正常，送一节5号电池。",
                price=80.00, original_price=169.00,
                category_id=cat_elec.id, condition="几乎全新",
                campus="独墅湖校区", transaction_method="当面交易",
                seller_id=zhang.id, status="approved", views=203,
            ),
            Product(
                title="小米充电宝 10000mAh",
                description="大三毕业出闲置，Type-C和USB-A双口输出，成色很新。",
                price=45.00, original_price=99.00,
                category_id=cat_elec.id, condition="几乎全新",
                campus="本部校区", transaction_method="邮寄",
                seller_id=li.id, status="approved", views=89,
            ),
            Product(
                title="飞利浦电动牙刷 HX3216",
                description="用了不到一年，刷头刚换新的，搬家出闲置。",
                price=35.00, original_price=159.00,
                category_id=cat_life.id, condition="轻微使用痕迹",
                campus="北校区", transaction_method="当面交易",
                seller_id=wang.id, status="approved", views=45,
            ),
            Product(
                title="尤尼克斯羽毛球拍 双拍套装",
                description="两只拍+一筒球，拍线完好，适合入门。",
                price=60.00, original_price=180.00,
                category_id=cat_sport.id, condition="轻微使用痕迹",
                campus="独墅湖校区", transaction_method="当面交易",
                seller_id=zhang.id, status="approved", views=72,
            ),
            Product(
                title="优衣库 男士连帽卫衣 M码",
                description="黑色，只穿过两次，洗后未变形不起球。",
                price=50.00, original_price=199.00,
                category_id=cat_cloth.id, condition="几乎全新",
                campus="南校区", transaction_method="自取",
                seller_id=li.id, status="approved", views=61,
            ),
            Product(
                title="雅马哈 F310 入门民谣吉他",
                description="大一买的，弦距适中，音色不错，送琴包和变调夹。",
                price=200.00, original_price=450.00,
                category_id=cat_music.id, condition="轻微使用痕迹",
                campus="独墅湖校区", transaction_method="当面交易",
                seller_id=wang.id, status="approved", views=156,
            ),
            Product(
                title="考研英语真题黄皮书 2010-2024",
                description="全套15年真题+解析，部分有笔记，解析部分干净。",
                price=25.00, original_price=89.00,
                category_id=cat_book.id, condition="明显使用痕迹",
                campus="本部校区", transaction_method="邮寄",
                seller_id=zhang.id, status="approved", views=198,
            ),
            Product(
                title="宜家折叠椅",
                description="搬家出闲置，白色，承重好，折叠后不占地方。",
                price=30.00, original_price=79.00,
                category_id=cat_life.id, condition="几乎全新",
                campus="阳澄湖校区", transaction_method="自取",
                seller_id=li.id, status="approved", views=28,
            ),
            Product(
                title="iPad Air3 64GB WiFi版",
                description="19年购入，有Apple Pencil一代，屏幕无划痕，电池健康91%。",
                price=1800.00, original_price=3896.00,
                category_id=cat_elec.id, condition="轻微使用痕迹",
                campus="独墅湖校区", transaction_method="当面交易",
                seller_id=wang.id, status="approved", views=412,
            ),
        ]
        for p in products:
            db.session.add(p)
        db.session.commit()
        print(f"[OK] 已创建 {len(products)} 条测试商品")

        # 创建求购信息
        requests = [
            PurchaseRequest(
                user_id=zhang.id,
                item_name="C语言程序设计 谭浩强版",
                budget_min=10, budget_max=25,
                expected_condition="轻微使用痕迹",
                description="急需C语言教材备考，有的同学请联系我。",
                campus="独墅湖校区",
                status="active",
            ),
            PurchaseRequest(
                user_id=li.id,
                item_name="机械键盘 红轴 87键",
                budget_min=100, budget_max=200,
                expected_condition="几乎全新",
                description="想要一把红轴机械键盘，IKBC或杜伽优先。",
                campus="本部校区",
                status="active",
            ),
            PurchaseRequest(
                user_id=wang.id,
                item_name="自行车 26寸变速",
                budget_min=150, budget_max=300,
                expected_condition="轻微使用痕迹",
                description="校区内代步用，要求变速正常，刹车灵敏。",
                campus="阳澄湖校区",
                status="active",
            ),
        ]
        for r in requests:
            db.session.add(r)
        db.session.commit()
        print(f"[OK] 已创建 {len(requests)} 条求购信息")

        # 创建留言
        comments = [
            Comment(product_id=1, user_id=li.id, content="请问还在吗？可以小刀吗？"),
            Comment(product_id=1, user_id=wang.id, content="独墅湖校区可以面交吗？"),
            Comment(product_id=4, user_id=wang.id, content="鼠标滚轮正常吗？"),
            Comment(product_id=12, user_id=zhang.id, content="1800能少一点吗？1750当面交易。"),
        ]
        for c in comments:
            db.session.add(c)
        db.session.commit()
        print(f"[OK] 已创建 {len(comments)} 条留言")

        print("\n数据库初始化完成!")
        print("运行 python app.py 启动应用")


if __name__ == "__main__":
    init_db()
