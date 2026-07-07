"""
================================================================================
 ⚠️  อ่านก่อนแก้ไฟล์นี้  ⚠️
================================================================================
ไฟล์นี้แบ่งเป็น 2 ส่วน:

  1) ส่วน "ตั้งค่า" (อยู่ด้านบน) — แก้ได้ตามสบาย:
     - BOT_TOKEN       ใส่ Bot Token จาก Discord Developer Portal
     - ADMIN_IDS       ใส่ User ID ของแอดมิน (ตัวเลขล้วน ไม่มี "")
     - SHOP_CHANNEL_ID ใส่ Channel ID ของช่องที่ต้องการให้บอทโพสต์ร้านค้า
     - STATS_CATEGORY_ID ใส่ Category ID ที่ต้องการให้แสดง Server Stats
     - PRODUCTS        เพิ่ม/ลบ/แก้สินค้าได้ที่นี่

  2) ส่วน "โค้ดหลัก" (ตั้งแต่ def/class ลงไป)
     ❌ ห้ามแก้ ❌ ถ้าไม่แน่ใจ — ให้ Claude แก้ให้

================================================================================
คำสั่งทั้งหมดใน Discord:

  [ทุกคนใช้ได้]
  /redeem <key>       กรอกคีย์เพื่อใช้งานสินค้าที่ซื้อ

  [เฉพาะแอดมิน]
  /shop               เปิดเมนูร้านค้า
  /stats              แสดง Server Stats
  /addcredit @user amount     เติมเครดิตให้คนนั้น
  /removecredit @user amount  ลดเครดิตจากคนนั้น
  /setcredit @user amount     ตั้งเครดิตเป็นตัวเลขที่ต้องการ
  /checkcredit @user          เช็คเครดิตของคนอื่น
  /addproduct name price duration  เพิ่มสินค้าใหม่
  /removeproduct name         ลบสินค้า
  /postshop                   สั่งให้บอทโพสต์เมนูร้านค้าในช่องที่กำหนด

ระบบยศ:
  ซื้อครั้งแรก           → Level 1 (ปลดล็อคช่อง redeem-key)
  ซื้อสะสมครบ 500 เครดิต → Level 2

วิธีติดตั้ง (รันใน CMD/Terminal):
  pip install discord.py
  py "discord_shop_bot.py"
================================================================================
"""

import sqlite3
import asyncio
import uuid

try:
    import discord
    from discord import app_commands
except ImportError:
    print("ไม่พบไลบรารี 'discord.py'")
    print("กรุณารันคำสั่งนี้ก่อน: pip install discord.py")
    raise SystemExit(1)

# =============================================================================
#  ================  ตั้งค่าทั้งหมดอยู่ในส่วนนี้  ================
# =============================================================================

# -----------------------------------------------------------------------------
# 1) Bot Token
#    วิธีที่ 1 (รันใน CMD): ใส่ token ตรงนี้เลย
#    วิธีที่ 2 (รันบน Render): ทิ้งว่างไว้ แล้วตั้ง Environment Variable
#                               ชื่อ SHOP_BOT_TOKEN ใน Render Dashboard แทน
# -----------------------------------------------------------------------------
import os
BOT_TOKEN = os.environ.get("SHOP_BOT_TOKEN", "")  # ถ้าไม่มี env var จะใช้ค่าว่าง

# -----------------------------------------------------------------------------
# 2) Admin User IDs
#    วิธีหา: เปิด Developer Mode ใน Discord -> คลิกขวาชื่อตัวเอง -> Copy User ID
#    ⚠️ ต้องเป็นตัวเลขล้วน ห้ามมีเครื่องหมาย "" ครอบ ❌ "123..." ✅ 123...
#    ใส่ได้หลายคน คั่นด้วย comma เช่น:
#    ADMIN_IDS = [
#        111222333444555666,
#        777888999000111222,
#    ]
# -----------------------------------------------------------------------------
ADMIN_IDS = [
    # ใส่ User ID ของคุณตรงนี้ เช่น:
    # 123456789012345678,
]

# -----------------------------------------------------------------------------
# 3) Channel ID ของช่องร้านค้า
#    วิธีหา: เปิด Developer Mode -> คลิกขวาที่ชื่อช่อง -> Copy Channel ID
# -----------------------------------------------------------------------------
SHOP_CHANNEL_ID = 0  # ใส่ Channel ID ของช่องร้านค้า เช่น 1234567890123456789

# -----------------------------------------------------------------------------
# 4) Category ID สำหรับ Server Stats (ชื่อช่องอัปเดตอัตโนมัติ)
#    วิธีหา: เปิด Developer Mode -> คลิกขวาที่ชื่อ Category -> Copy ID
#    บอทจะสร้างช่องใน Category นี้อัตโนมัติ ชื่อว่า:
#      "🌍 Total: xxxx", "🟢 Online: xxxx", "🤖 Bots: xx"
#    อัปเดตทุก 10 นาที (ข้อจำกัดของ Discord)
# -----------------------------------------------------------------------------
STATS_CATEGORY_ID = 0  # ใส่ Category ID เช่น 1234567890123456789

# -----------------------------------------------------------------------------
# 5) รายการสินค้า (แก้/เพิ่ม/ลบได้ที่นี่)
#    name     = ชื่อสินค้า
#    price    = ราคา (หน่วยเครดิต)
#    duration = อายุการใช้งาน (ข้อความอธิบาย)
# -----------------------------------------------------------------------------
PRODUCTS = [
    {"name": "Sample Product A", "price": 100, "duration": "30 days"},
    {"name": "Sample Product B", "price": 250, "duration": "60 days"},
]

# -----------------------------------------------------------------------------
# 6) ข้อความตอนกด "Top Up Credit"
# -----------------------------------------------------------------------------
TOPUP_MESSAGE = (
    "💳 **Top Up Credit**\n"
    "Please contact an admin to add credit to your account.\n"
    "An admin will use `/addcredit` to add credit for you."
)

# -----------------------------------------------------------------------------
# 7) ระบบยศ (Role IDs)
#    วิธีหา Role ID: เปิด Developer Mode -> Server Settings -> Roles
#                   -> คลิกขวาที่ชื่อยศ -> Copy ID
#
#    ROLE_LEVEL_1_ID  = ยศที่ได้ตอนซื้อครั้งแรก (ปลดล็อคช่อง redeem-key)
#    ROLE_LEVEL_2_ID  = ยศที่ได้ตอนซื้อสะสมครบ 500 เครดิต
#    LEVEL_2_THRESHOLD = จำนวนเครดิตที่ต้องซื้อสะสมเพื่อขึ้น Level 2
# -----------------------------------------------------------------------------
ROLE_LEVEL_1_ID = 0   # ใส่ Role ID ของ Level 1 เช่น 1234567890123456789
ROLE_LEVEL_2_ID = 0   # ใส่ Role ID ของ Level 2 เช่น 1234567890123456789
LEVEL_2_THRESHOLD = 500  # เครดิตที่ต้องซื้อสะสมเพื่อขึ้น Level 2

# -----------------------------------------------------------------------------
# 8) ชื่อไฟล์ฐานข้อมูล
# -----------------------------------------------------------------------------
DB_FILE = "shop.db"

# =============================================================================
#  ================  จบส่วนตั้งค่า (แก้ได้แค่ถึงตรงนี้)  ================
# =============================================================================
#
#  ⛔ หยุด ⛔ ห้ามแก้โค้ดด้านล่างนี้ ⛔
#  นี่คือ "โค้ดหลัก" ของโปรแกรม ถ้าแก้แล้วระบบอาจพังทั้งหมดได้
#  ถ้าต้องการเพิ่ม/เปลี่ยนฟีเจอร์ ให้ขอให้ Claude แก้ให้
# =============================================================================


# ─── Database ────────────────────────────────────────────────────────────────

def db_init():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS credits (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER NOT NULL,
            duration TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS spent_total (
            user_id INTEGER PRIMARY KEY,
            total INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
    _sync_products()


def get_spent_total(user_id: int) -> int:
    """เครดิตที่ใช้ซื้อสะสมทั้งหมด"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT total FROM spent_total WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def add_spent_total(user_id: int, amount: int) -> int:
    """เพิ่มยอดใช้จ่ายสะสม คืนค่ายอดใหม่"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO spent_total (user_id, total) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET total = total + ?
    """, (user_id, amount, amount))
    cur.execute("SELECT total FROM spent_total WHERE user_id = ?", (user_id,))
    new_total = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return new_total


def _sync_products():
    """sync PRODUCTS list จาก config ลง database ตอนเริ่มต้น"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    for p in PRODUCTS:
        cur.execute("""
            INSERT INTO products (name, price, duration) VALUES (?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET price=?, duration=?
        """, (p["name"], p["price"], p["duration"], p["price"], p["duration"]))
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT balance FROM credits WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def set_balance(user_id: int, new_balance: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO credits (user_id, balance) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET balance = ?
    """, (user_id, new_balance, new_balance))
    conn.commit()
    conn.close()


def modify_balance(user_id: int, delta: int) -> int:
    new_balance = max(0, get_balance(user_id) + delta)
    set_balance(user_id, new_balance)
    return new_balance


def record_order(user_id: int, product_name: str, price: int) -> str:
    """บันทึก order และ return key ที่เจนให้"""
    key = "-".join([uuid.uuid4().hex[:6].upper() for _ in range(4)])
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # สร้างตาราง keys ถ้ายังไม่มี
    cur.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            key TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            redeemed INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
    """)
    cur.execute(
        "INSERT INTO orders (user_id, product_name, price) VALUES (?, ?, ?)",
        (user_id, product_name, price),
    )
    cur.execute(
        "INSERT INTO keys (key, user_id, product_name) VALUES (?, ?, ?)",
        (key, user_id, product_name),
    )
    conn.commit()
    conn.close()
    return key


def redeem_key(key: str, user_id: int):
    """ตรวจสอบและ redeem key คืนค่า (product_name, error_message)"""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT user_id, product_name, redeemed FROM keys WHERE key = ?", (key,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return None, "❌ Key not found. Please check and try again."
    owner_id, product_name, redeemed = row
    if redeemed:
        conn.close()
        return None, "❌ This key has already been redeemed."
    cur.execute("UPDATE keys SET redeemed = 1 WHERE key = ?", (key,))
    conn.commit()
    conn.close()
    return product_name, None


def get_orders(user_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT product_name, price, created_at FROM orders "
        "WHERE user_id = ? ORDER BY id DESC LIMIT 10",
        (user_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def db_get_products():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT name, price, duration FROM products ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [{"name": r[0], "price": r[1], "duration": r[2]} for r in rows]


def db_add_product(name: str, price: int, duration: str) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("INSERT INTO products (name, price, duration) VALUES (?, ?, ?)",
                    (name, price, duration))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def db_remove_product(name: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE name = ?", (name,))
    affected = cur.rowcount
    conn.commit()
    conn.close()
    return affected > 0


# ─── Discord Setup ───────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ชื่อช่อง stats ที่สร้างไว้ (เก็บ reference ไว้เพื่ออัปเดต)
stats_channels = {"total": None, "online": None, "bots": None}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── Stats Channel Auto-Update ───────────────────────────────────────────────

async def update_stats_channels(guild: discord.Guild):
    """อัปเดตชื่อช่อง stats ทุก 10 นาที"""
    global stats_channels
    category = guild.get_channel(STATS_CATEGORY_ID)
    if not category or not isinstance(category, discord.CategoryChannel):
        return

    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    bots = sum(1 for m in guild.members if m.bot)

    targets = {
        "total":  ("🌍", f"🌍 Total: {total}"),
        "online": ("🟢", f"🟢 Online: {online}"),
        "bots":   ("🤖", f"🤖 Bots: {bots}"),
    }

    for key, (prefix, new_name) in targets.items():
        ch = stats_channels[key]
        # ถ้ายังไม่มี reference → หาใน category ที่มีอยู่แล้วด้วย emoji prefix
        if ch is None:
            ch = next(
                (c for c in category.voice_channels if c.name.startswith(prefix)),
                None,
            )
            if ch:
                stats_channels[key] = ch

        if ch:
            # อัปเดตชื่อถ้าต่างจากเดิม (ลด rate limit)
            if ch.name != new_name:
                try:
                    await ch.edit(name=new_name)
                except discord.HTTPException:
                    pass
        else:
            # สร้างใหม่แค่ครั้งแรกครั้งเดียว
            try:
                new_ch = await guild.create_voice_channel(name=new_name, category=category)
                await new_ch.set_permissions(guild.default_role, connect=False)
                stats_channels[key] = new_ch
            except discord.HTTPException:
                pass
                stats_channels[key] = new_ch
            except discord.HTTPException:
                pass


async def stats_loop():
    await client.wait_until_ready()
    while not client.is_closed():
        if STATS_CATEGORY_ID != 0:
            for guild in client.guilds:
                await update_stats_channels(guild)
        await asyncio.sleep(600)  # 10 นาที


# ─── Shop UI ─────────────────────────────────────────────────────────────────

class ProductSelect(discord.ui.Select):
    def __init__(self):
        products = db_get_products()
        if not products:
            options = [discord.SelectOption(label="No products available", value="none")]
        else:
            options = [
                discord.SelectOption(
                    label=p["name"],
                    description=f"{p['price']} credits | {p['duration']}",
                    value=p["name"],
                )
                for p in products
            ]
        super().__init__(placeholder="Select a product to view...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await interaction.response.send_message("No products available.", ephemeral=True)
            return
        products = db_get_products()
        chosen = next((p for p in products if p["name"] == self.values[0]), None)
        if not chosen:
            await interaction.response.send_message("Product not found.", ephemeral=True)
            return

        embed = discord.Embed(title=f"📦 {chosen['name']}", color=discord.Color.blue())
        embed.add_field(name="💰 Price", value=f"{chosen['price']} credits", inline=True)
        embed.add_field(name="⏳ Duration", value=chosen["duration"], inline=True)
        embed.add_field(name="📦 Stock", value="Unlimited", inline=True)

        view = discord.ui.View()
        view.add_item(BuyButton(chosen))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class BuyButton(discord.ui.Button):
    def __init__(self, product):
        super().__init__(label=f"Buy — {product['price']} credits", style=discord.ButtonStyle.success, emoji="✅")
        self.product = product

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        balance = get_balance(user_id)
        price = self.product["price"]

        if balance < price:
            await interaction.response.send_message(
                f"❌ เครดิตไม่พอ\n"
                f"เครดิตของคุณ: **{balance}** เครดิต\n"
                f"ราคาสินค้า: **{price}** เครดิต\n\n"
                f"{TOPUP_MESSAGE}",
                ephemeral=True,
            )
            return

        new_balance = balance - price
        set_balance(user_id, new_balance)
        key = record_order(user_id, self.product["name"], price)
        new_total = add_spent_total(user_id, price)

        await interaction.response.send_message(
            f"✅ ซื้อสำเร็จ!\n"
            f"**{self.product['name']}** | -{price} เครดิต\n"
            f"เครดิตคงเหลือ: **{new_balance}** เครดิต\n\n"
            f"🔑 คีย์ถูกส่งไปยัง DM ของคุณแล้ว!",
            ephemeral=True,
        )

        # ─── ระบบยศ ───────────────────────────────────────────────
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        if member:
            # Level 1 — ซื้อครั้งแรก (total >= price แปลว่าซื้อแล้วอย่างน้อย 1 ครั้ง)
            if ROLE_LEVEL_1_ID != 0:
                role_l1 = interaction.guild.get_role(ROLE_LEVEL_1_ID)
                if role_l1 and role_l1 not in member.roles:
                    try:
                        await member.add_roles(role_l1, reason="ซื้อครั้งแรก — Level 1")
                        await interaction.followup.send(
                            f"🎉 คุณได้รับยศ **{role_l1.name}**! ตอนนี้คุณสามารถเข้าช่อง redeem-key ได้แล้ว",
                            ephemeral=True,
                        )
                    except discord.Forbidden:
                        pass

            # Level 2 — ซื้อสะสมครบ threshold
            if ROLE_LEVEL_2_ID != 0 and new_total >= LEVEL_2_THRESHOLD:
                role_l2 = interaction.guild.get_role(ROLE_LEVEL_2_ID)
                if role_l2 and role_l2 not in member.roles:
                    try:
                        await member.add_roles(role_l2, reason=f"ซื้อสะสม {new_total} เครดิต — Level 2")
                        await interaction.followup.send(
                            f"⭐ คุณได้รับการเลื่อนยศเป็น **{role_l2.name}**! ยอดซื้อสะสม: {new_total} เครดิต",
                            ephemeral=True,
                        )
                    except discord.Forbidden:
                        pass

        # ─── ส่งคีย์ทาง DM ───────────────────────────────────────
        try:
            await interaction.user.send(
                f"🎉 **ซื้อสำเร็จ!**\n"
                f"สินค้า: **{self.product['name']}**\n"
                f"อายุการใช้งาน: **{self.product['duration']}**\n\n"
                f"🔑 **คีย์ของคุณ:**\n```{key}```\n"
                f"กดปุ่ม **ใช้คีย์** ในช่อง redeem-key แล้ววางคีย์นี้เพื่อเปิดใช้งาน\n"
                f"เครดิตคงเหลือ: **{new_balance}** เครดิต\n"
                f"ยอดซื้อสะสม: **{new_total}** เครดิต"
            )
        except discord.Forbidden:
            pass


class ProductView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(ProductSelect())


class RedeemModal(discord.ui.Modal, title="🔑 กรอกคีย์เพื่อใช้งาน"):
    key_input = discord.ui.TextInput(
        label="คีย์ของคุณ",
        placeholder="XXXXXX-XXXXXX-XXXXXX-XXXXXX",
        min_length=10,
        max_length=50,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        product_name, error = redeem_key(self.key_input.value.strip().upper(), interaction.user.id)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return
        await interaction.response.send_message(
            f"✅ **ใช้คีย์สำเร็จ!**\n"
            f"สินค้า: **{product_name}**\n"
            f"ขอบคุณที่ใช้บริการ 🎉",
            ephemeral=True,
        )


def build_shop_embed():
    embed = discord.Embed(
        title="🛒 ร้านค้า",
        description=(
            "กดปุ่มด้านล่างเพื่อดูสินค้าและซื้อสินค้า\n"
            "เครดิตเติมโดยแอดมิน ติดต่อแอดมินเพื่อเติมเครดิต"
        ),
        color=discord.Color.purple(),
    )
    embed.set_footer(text="Powered by bro bot")
    return embed


class ShopView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="เติมเครดิต", style=discord.ButtonStyle.success, emoji="💳", custom_id="shop:topup")
    async def topup(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(TOPUP_MESSAGE, ephemeral=True)

    @discord.ui.button(label="เลือกสินค้า", style=discord.ButtonStyle.primary, emoji="📦", custom_id="shop:select")
    async def select_product(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "เลือกสินค้าที่ต้องการ:", view=ProductView(), ephemeral=True
        )

    @discord.ui.button(label="ใช้คีย์", style=discord.ButtonStyle.danger, emoji="🔑", custom_id="shop:redeem")
    async def redeem_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RedeemModal())

    @discord.ui.button(label="ประวัติการสั่งซื้อ", style=discord.ButtonStyle.secondary, emoji="📋", custom_id="shop:history")
    async def order_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        orders = get_orders(interaction.user.id)
        if not orders:
            await interaction.response.send_message("📋 ยังไม่มีประวัติการสั่งซื้อ", ephemeral=True)
            return
        lines = [f"• {name} — {price} เครดิต — {created_at}" for name, price, created_at in orders]
        await interaction.response.send_message(
            "**📋 ประวัติการสั่งซื้อล่าสุด (10 รายการ):**\n" + "\n".join(lines), ephemeral=True
        )

    @discord.ui.button(label="เครดิตของฉัน", style=discord.ButtonStyle.secondary, emoji="💰", custom_id="shop:balance")
    async def balance(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"💰 เครดิตของคุณ: **{bal} เครดิต**", ephemeral=True
        )


# ─── Slash Commands ──────────────────────────────────────────────────────────

@tree.command(name="shop", description="(แอดมิน) เปิดเมนูร้านค้า")
async def shop_command(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    await interaction.response.send_message(embed=build_shop_embed(), view=ShopView())


@tree.command(name="stats", description="(แอดมิน) แสดงสถิติเซิร์ฟเวอร์")
async def stats_command(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("❌ ใช้คำสั่งนี้ได้เฉพาะในเซิร์ฟเวอร์เท่านั้น", ephemeral=True)
        return
    total = guild.member_count
    online = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    bots = sum(1 for m in guild.members if m.bot)
    embed = discord.Embed(title="📊 สถิติเซิร์ฟเวอร์", color=discord.Color.green())
    embed.add_field(name="🌍 สมาชิกทั้งหมด", value=str(total), inline=False)
    embed.add_field(name="🟢 ออนไลน์", value=str(online), inline=False)
    embed.add_field(name="🤖 บอท", value=str(bots), inline=False)
    await interaction.response.send_message(embed=embed)


@tree.command(name="addcredit", description="(แอดมิน) เติมเครดิตให้สมาชิก")
@app_commands.describe(user="สมาชิกที่ต้องการเติมเครดิต", amount="จำนวนเครดิตที่จะเติม")
async def addcredit_command(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("❌ จำนวนต้องมากกว่า 0", ephemeral=True)
        return
    new_bal = modify_balance(user.id, amount)
    await interaction.response.send_message(
        f"✅ เติม **{amount}** เครดิตให้ {user.mention} สำเร็จ\n"
        f"เครดิตคงเหลือ: **{new_bal}** เครดิต"
    )
    try:
        await user.send(f"💰 คุณได้รับ **{amount}** เครดิตจากแอดมิน\nเครดิตคงเหลือ: **{new_bal}** เครดิต")
    except discord.Forbidden:
        pass


@tree.command(name="removecredit", description="(แอดมิน) ลดเครดิตสมาชิก")
@app_commands.describe(user="สมาชิกที่ต้องการลดเครดิต", amount="จำนวนเครดิตที่จะลด")
async def removecredit_command(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    if amount <= 0:
        await interaction.response.send_message("❌ จำนวนต้องมากกว่า 0", ephemeral=True)
        return
    new_bal = modify_balance(user.id, -amount)
    await interaction.response.send_message(
        f"✅ ลด **{amount}** เครดิตจาก {user.mention} สำเร็จ\n"
        f"เครดิตคงเหลือ: **{new_bal}** เครดิต"
    )


@tree.command(name="setcredit", description="(แอดมิน) ตั้งเครดิตสมาชิก")
@app_commands.describe(user="สมาชิกที่ต้องการตั้งเครดิต", amount="จำนวนเครดิตใหม่")
async def setcredit_command(interaction: discord.Interaction, user: discord.Member, amount: int):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    if amount < 0:
        await interaction.response.send_message("❌ จำนวนต้องมากกว่าหรือเท่ากับ 0", ephemeral=True)
        return
    set_balance(user.id, amount)
    await interaction.response.send_message(
        f"✅ ตั้งเครดิตของ {user.mention} เป็น **{amount}** เครดิต สำเร็จ"
    )


@tree.command(name="checkcredit", description="(แอดมิน) เช็คเครดิตสมาชิก")
@app_commands.describe(user="สมาชิกที่ต้องการเช็คเครดิต")
async def checkcredit_command(interaction: discord.Interaction, user: discord.Member):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    bal = get_balance(user.id)
    await interaction.response.send_message(
        f"💰 เครดิตของ {user.mention}: **{bal}** เครดิต", ephemeral=True
    )


@tree.command(name="addproduct", description="(แอดมิน) เพิ่มสินค้าใหม่")
@app_commands.describe(name="ชื่อสินค้า", price="ราคา (เครดิต)", duration="อายุการใช้งาน เช่น 30 วัน")
async def addproduct_command(interaction: discord.Interaction, name: str, price: int, duration: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    if price <= 0:
        await interaction.response.send_message("❌ ราคาต้องมากกว่า 0", ephemeral=True)
        return
    success = db_add_product(name, price, duration)
    if success:
        await interaction.response.send_message(f"✅ เพิ่มสินค้า: **{name}** | {price} เครดิต | {duration} สำเร็จ")
    else:
        await interaction.response.send_message(f"❌ สินค้า **{name}** มีอยู่แล้ว", ephemeral=True)


@tree.command(name="removeproduct", description="(แอดมิน) ลบสินค้า")
@app_commands.describe(name="ชื่อสินค้าที่ต้องการลบ")
async def removeproduct_command(interaction: discord.Interaction, name: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    success = db_remove_product(name)
    if success:
        await interaction.response.send_message(f"✅ ลบสินค้า: **{name}** สำเร็จ")
    else:
        await interaction.response.send_message(f"❌ ไม่พบสินค้า **{name}**", ephemeral=True)


@tree.command(name="postshop", description="(แอดมิน) โพสต์เมนูร้านค้าในช่องที่กำหนด")
async def postshop_command(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    if SHOP_CHANNEL_ID == 0:
        await interaction.response.send_message("❌ ยังไม่ได้ตั้งค่า SHOP_CHANNEL_ID", ephemeral=True)
        return
    channel = client.get_channel(SHOP_CHANNEL_ID)
    if not channel:
        await interaction.response.send_message("❌ ไม่พบช่องร้านค้า กรุณาตรวจสอบ SHOP_CHANNEL_ID", ephemeral=True)
        return
    await channel.send(embed=build_shop_embed(), view=ShopView())
    await interaction.response.send_message("✅ โพสต์เมนูร้านค้าสำเร็จ!", ephemeral=True)


# ─── Events ──────────────────────────────────────────────────────────────────


@client.event
async def on_ready():
    db_init()
    client.add_view(ShopView())
    # sync กับทุก guild เพื่อให้คำสั่งใหม่ขึ้นทันที
    for guild in client.guilds:
        await tree.sync(guild=guild)
    await tree.sync()
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    print("✅ Slash commands synced. Bot is ready.")
    print("📋 Commands: /shop /stats /redeem /addcredit /removecredit /setcredit /checkcredit /addproduct /removeproduct /postshop")

    if not ADMIN_IDS:
        print("⚠️  ADMIN_IDS is empty! Admin commands will not work.")
    else:
        print("👑 Admin list:")
        for admin_id in ADMIN_IDS:
            user = client.get_user(admin_id)
            if user:
                print(f"   - {user.name} (ID: {admin_id})")
            else:
                print(f"   - Unknown (ID: {admin_id})")

    client.loop.create_task(stats_loop())


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # ถ้าอยากรันใน CMD ให้ใส่ token ตรงนี้แทน (จะ override ค่าจาก env var)
    LOCAL_TOKEN = ""  # ใส่ token ตรงนี้ถ้ารันใน CMD เช่น "MTQ3..."

    token = LOCAL_TOKEN.strip() or BOT_TOKEN.strip()

    if not token:
        print("=" * 60)
        print("❌ ไม่พบ BOT_TOKEN")
        print("วิธีที่ 1 (CMD): ใส่ token ใน LOCAL_TOKEN ในฟังก์ชัน main()")
        print("วิธีที่ 2 (Render): ตั้ง Environment Variable ชื่อ SHOP_BOT_TOKEN")
        print("=" * 60)
        return
    client.run(token)


if __name__ == "__main__":
    main()
