"""
================================================================================
 ⚠️  อ่านก่อนแก้ไฟล์นี้  ⚠️
================================================================================
ไฟล์นี้แบ่งเป็น 2 ส่วน:

  1) ส่วน "ตั้งค่า" (อยู่ด้านบน) — แก้ได้ตามสบาย
  2) ส่วน "โค้ดหลัก" — ❌ ห้ามแก้ ❌

================================================================================
คำสั่งทั้งหมดใน Discord:

  [เฉพาะแอดมิน]
  /postverify    โพสต์ปุ่มยืนยันตัวตนในช่องที่กำหนด
  /postticket    โพสต์ปุ่มเปิด Ticket ในช่องที่กำหนด
  /closeticket   ปิดช่อง Ticket (ใช้ในช่อง Ticket เท่านั้น)

วิธีติดตั้ง:
  1. pip install discord.py
  2. สร้างบอทใหม่ที่ https://discord.com/developers/applications
     (แยกจากบอทร้านค้า)
  3. ใส่ค่าในส่วนตั้งค่าด้านล่าง
  4. py "discord_verify_bot.py"
================================================================================
"""

import asyncio

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
# 1) Bot Token (สร้างบอทใหม่แยกจากบอทร้านค้า)
# -----------------------------------------------------------------------------
BOT_TOKEN = "MTUxNTU4MDIyNjc0MTA4MDE4NA.G387fe.rdHWNPNrmjsq0vZz31CZenkYD-g73PH9ioBHuY"  # ใส่ Token ของบอทยืนยันตัวตน

# -----------------------------------------------------------------------------
# 2) Admin User IDs
#    ⚠️ ตัวเลขล้วน ไม่มี "" ครอบ
# -----------------------------------------------------------------------------
ADMIN_IDS = [
   1227630831212957827,
]

# -----------------------------------------------------------------------------
# 3) Role ID ที่จะได้รับหลังยืนยันตัวตน (Member role)
#    วิธีหา: Server Settings -> Roles -> คลิกขวา -> Copy ID
# -----------------------------------------------------------------------------
MEMBER_ROLE_ID = 1515701093131354222  # ใส่ Role ID ของ Member เช่น 1234567890123456789

# -----------------------------------------------------------------------------
# 4) Channel ID สำหรับโพสต์ข้อความต้อนรับหลังยืนยัน
#    (ช่องที่ต้องการให้บอทส่ง "ยินดีต้อนรับ @ชื่อ")
# -----------------------------------------------------------------------------
WELCOME_CHANNEL_ID = 1515693712225734750 # ใส่ Channel ID ของช่องต้อนรับ

# -----------------------------------------------------------------------------
# 5) Channel ID สำหรับโพสต์ปุ่มยืนยันตัวตน
# -----------------------------------------------------------------------------
VERIFY_CHANNEL_ID = 1515691934687957092  # ใส่ Channel ID ของช่องยืนยันตัวตน

# -----------------------------------------------------------------------------
# 6) ข้อความและ embed ในช่องยืนยันตัวตน (แก้ได้)
# -----------------------------------------------------------------------------
VERIFY_EMBED_TITLE = "✅ ยืนยันตัวตน"
VERIFY_EMBED_DESC = (
    "กดปุ่มด้านล่างเพื่อยืนยันตัวตนและเข้าถึงช่องต่างๆ ในเซิร์ฟเวอร์\n\n"
    "📋 **ขั้นตอน:**\n"
    "1. กดปุ่ม **ยืนยันตัวตน**\n"
    "2. เลือกเพศของคุณ\n"
    "3. กด **ยืนยัน** เพื่อเข้าถึงเซิร์ฟเวอร์"
)

# -----------------------------------------------------------------------------
# 7) ข้อความต้อนรับหลังยืนยัน (แก้ได้)
#    {mention} = แท็กชื่อสมาชิก, {member_count} = จำนวนสมาชิกทั้งหมด
# -----------------------------------------------------------------------------
WELCOME_MESSAGE = "🎉 ยินดีต้อนรับ {mention} สู่เซิร์ฟเวอร์! คุณเป็นสมาชิกลำดับที่ {member_count} 🎊"

# -----------------------------------------------------------------------------
# 8) ระบบ Ticket (ติดต่อแอดมิน)
#    TICKET_CATEGORY_ID  = Category ID ที่จะสร้างช่อง Ticket ไว้ข้างใน
#    TICKET_CHANNEL_ID   = Channel ID ของช่องที่โพสต์ปุ่มเปิด Ticket
#    TICKET_ADMIN_ROLE_ID = Role ID ของแอดมินที่จะมองเห็นช่อง Ticket
#    วิธีหา ID: เปิด Developer Mode -> คลิกขวา -> Copy ID
# -----------------------------------------------------------------------------
TICKET_CATEGORY_ID = 1515693474240790598  # ใส่ Category ID สำหรับเก็บช่อง Ticket
TICKET_CHANNEL_ID =  1515711760793993436  # ใส่ Channel ID ของช่องที่โพสต์ปุ่มเปิด Ticket
TICKET_ADMIN_ROLE_ID = 1515722171790655518  # ใส่ Role ID ของแอดมิน (จะมองเห็นช่อง Ticket ได้)

# ข้อความใน embed ของช่อง Ticket (แก้ได้)
TICKET_EMBED_TITLE = "🎫 ติดต่อแอดมิน"
TICKET_EMBED_DESC = (
    "กดปุ่มด้านล่างเพื่อเปิด Ticket ติดต่อแอดมิน\n\n"
    "📋 **กรุณาอ่านก่อนเปิด Ticket:**\n"
    "• แจ้งเรื่องที่ต้องการให้ชัดเจน\n"
    "• แอดมินจะเข้ามาตอบในช่อง Ticket ของคุณ\n"
    "• ห้ามเปิด Ticket โดยไม่มีเหตุผล"
)

# =============================================================================
#  ================  จบส่วนตั้งค่า (แก้ได้แค่ถึงตรงนี้)  ================
# =============================================================================
#
#  ⛔ หยุด ⛔ ห้ามแก้โค้ดด้านล่างนี้ ⛔
#  นี่คือ "โค้ดหลัก" ของโปรแกรม ถ้าแก้แล้วระบบอาจพังทั้งหมดได้
#  ถ้าต้องการเพิ่ม/เปลี่ยนฟีเจอร์ ให้ขอให้ Claude แก้ให้
# =============================================================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ─── Verification Modal ──────────────────────────────────────────────────────

class GenderSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ชาย", emoji="👦", value="ชาย"),
            discord.SelectOption(label="หญิง", emoji="👧", value="หญิง"),
            discord.SelectOption(label="ไม่ระบุ", emoji="🧑", value="ไม่ระบุ"),
            discord.SelectOption(label="LGBTQ+", emoji="🏳️‍🌈", value="LGBTQ+"),
        ]
        super().__init__(placeholder="เลือกเพศของคุณ...", options=options, custom_id="verify:gender")

    async def callback(self, interaction: discord.Interaction):
        gender = self.values[0]
        member = interaction.guild.get_member(interaction.user.id)

        # ตรวจสอบว่ายืนยันแล้วหรือยัง
        if MEMBER_ROLE_ID != 0:
            role = interaction.guild.get_role(MEMBER_ROLE_ID)
            if role and role in member.roles:
                await interaction.response.send_message(
                    "✅ คุณยืนยันตัวตนแล้ว!", ephemeral=True
                )
                return

        # ให้ยศ Member
        role_given = False
        if MEMBER_ROLE_ID != 0 and member:
            role = interaction.guild.get_role(MEMBER_ROLE_ID)
            if role:
                try:
                    await member.add_roles(role, reason=f"ยืนยันตัวตน เพศ: {gender}")
                    role_given = True
                except discord.Forbidden:
                    pass

        await interaction.response.send_message(
            f"✅ **ยืนยันตัวตนสำเร็จ!**\n"
            f"เพศ: **{gender}**\n"
            f"{'✅ คุณได้รับสิทธิ์เข้าถึงเซิร์ฟเวอร์แล้ว!' if role_given else '⚠️ ไม่สามารถให้ยศได้ กรุณาติดต่อแอดมิน'}",
            ephemeral=True,
        )

        # ส่งข้อความต้อนรับในช่องที่กำหนด
        if WELCOME_CHANNEL_ID != 0 and role_given:
            welcome_ch = client.get_channel(WELCOME_CHANNEL_ID)
            if welcome_ch:
                try:
                    await welcome_ch.send(
                        WELCOME_MESSAGE.format(
                            mention=interaction.user.mention,
                            member_count=interaction.guild.member_count,
                        )
                    )
                except discord.Forbidden:
                    pass


class GenderSelectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(GenderSelect())


class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ยืนยันตัวตน",
        style=discord.ButtonStyle.success,
        emoji="✅",
        custom_id="verify:start"
    )
    async def verify_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        member = interaction.guild.get_member(interaction.user.id)
        # เช็คว่ายืนยันแล้วหรือยัง
        if MEMBER_ROLE_ID != 0 and member:
            role = interaction.guild.get_role(MEMBER_ROLE_ID)
            if role and role in member.roles:
                await interaction.response.send_message(
                    "✅ คุณยืนยันตัวตนแล้ว!", ephemeral=True
                )
                return
        await interaction.response.send_message(
            "👤 **เลือกเพศของคุณเพื่อยืนยันตัวตน:**",
            view=GenderSelectView(),
            ephemeral=True,
        )


# ─── Ticket System ───────────────────────────────────────────────────────────

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="เปิด Ticket ติดต่อแอดมิน",
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        custom_id="ticket:open"
    )
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        # เช็คว่ามี Ticket อยู่แล้วหรือยัง
        existing = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{member.name.lower().replace(' ', '-')}"
        )
        if existing:
            await interaction.response.send_message(
                f"❌ คุณมี Ticket อยู่แล้วที่ {existing.mention}", ephemeral=True
            )
            return

        # หา Category
        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID != 0 else None

        # ตั้งค่าสิทธิ์ช่อง Ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }

        # เพิ่มสิทธิ์แอดมิน
        if TICKET_ADMIN_ROLE_ID != 0:
            admin_role = guild.get_role(TICKET_ADMIN_ROLE_ID)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                )

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.name.lower().replace(' ', '-')}",
                category=category,
                overwrites=overwrites,
                topic=f"Ticket ของ {member.name} (ID: {member.id})",
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ บอทไม่มีสิทธิ์สร้างช่อง กรุณาแจ้งแอดมิน", ephemeral=True
            )
            return

        # ส่งข้อความเริ่มต้นในช่อง Ticket
        embed = discord.Embed(
            title="🎫 Ticket ของคุณถูกสร้างแล้ว",
            description=(
                f"สวัสดี {member.mention}!\n\n"
                f"แอดมินจะเข้ามาช่วยเหลือคุณในไม่ช้า\n"
                f"กรุณาอธิบายปัญหาหรือคำถามของคุณได้เลย\n\n"
                f"กดปุ่ม **ปิด Ticket** เมื่อเสร็จสิ้น"
            ),
            color=discord.Color.blue(),
        )

        admin_mention = ""
        if TICKET_ADMIN_ROLE_ID != 0:
            admin_role = guild.get_role(TICKET_ADMIN_ROLE_ID)
            if admin_role:
                admin_mention = admin_role.mention

        await ticket_channel.send(
            content=f"{member.mention} {admin_mention}",
            embed=embed,
            view=CloseTicketView(),
        )

        await interaction.response.send_message(
            f"✅ Ticket ของคุณถูกสร้างแล้วที่ {ticket_channel.mention}", ephemeral=True
        )


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ปิด Ticket",
        style=discord.ButtonStyle.danger,
        emoji="🔒",
        custom_id="ticket:close"
    )
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        await interaction.response.send_message("🔒 กำลังปิด Ticket...")
        await asyncio.sleep(3)
        try:
            await channel.delete(reason=f"ปิด Ticket โดย {interaction.user.name}")
        except discord.Forbidden:
            await interaction.followup.send("❌ บอทไม่มีสิทธิ์ลบช่อง", ephemeral=True)


# ─── Commands ────────────────────────────────────────────────────────────────

@tree.command(name="postverify", description="(แอดมิน) โพสต์ปุ่มยืนยันตัวตนในช่องที่กำหนด")
async def postverify_command(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return

    channel_id = VERIFY_CHANNEL_ID if VERIFY_CHANNEL_ID != 0 else interaction.channel_id
    channel = client.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ ไม่พบช่องยืนยันตัวตน กรุณาตรวจสอบ VERIFY_CHANNEL_ID", ephemeral=True)
        return

    embed = discord.Embed(
        title=VERIFY_EMBED_TITLE,
        description=VERIFY_EMBED_DESC,
        color=discord.Color.green(),
    )
    await channel.send(embed=embed, view=VerifyView())
    await interaction.response.send_message("✅ โพสต์ปุ่มยืนยันตัวตนสำเร็จ!", ephemeral=True)


@tree.command(name="postticket", description="(แอดมิน) โพสต์ปุ่มเปิด Ticket ในช่องที่กำหนด")
async def postticket_command(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    channel_id = TICKET_CHANNEL_ID if TICKET_CHANNEL_ID != 0 else interaction.channel_id
    channel = client.get_channel(channel_id)
    if not channel:
        await interaction.response.send_message("❌ ไม่พบช่อง Ticket กรุณาตรวจสอบ TICKET_CHANNEL_ID", ephemeral=True)
        return
    embed = discord.Embed(
        title=TICKET_EMBED_TITLE,
        description=TICKET_EMBED_DESC,
        color=discord.Color.blue(),
    )
    await channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ โพสต์ปุ่ม Ticket สำเร็จ!", ephemeral=True)


@tree.command(name="closeticket", description="(แอดมิน) ปิดช่อง Ticket นี้")
async def closeticket_command(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ คุณไม่มีสิทธิ์ใช้คำสั่งนี้", ephemeral=True)
        return
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ คำสั่งนี้ใช้ได้เฉพาะในช่อง Ticket เท่านั้น", ephemeral=True)
        return
    await interaction.response.send_message("🔒 กำลังปิด Ticket...")
    await asyncio.sleep(3)
    await interaction.channel.delete(reason=f"ปิด Ticket โดย {interaction.user.name}")


# ─── Events ──────────────────────────────────────────────────────────────────

@client.event
async def on_ready():
    client.add_view(VerifyView())
    client.add_view(TicketView())
    client.add_view(CloseTicketView())
    for guild in client.guilds:
        await tree.sync(guild=guild)
    await tree.sync()
    print(f"✅ Logged in as {client.user} (ID: {client.user.id})")
    print("✅ Verify + Ticket bot is ready!")
    print("📋 Commands: /postverify /postticket /closeticket")

    if not ADMIN_IDS:
        print("⚠️  ADMIN_IDS is empty!")
    else:
        print("👑 Admin list:")
        for admin_id in ADMIN_IDS:
            user = client.get_user(admin_id)
            print(f"   - {user.name if user else 'Unknown'} (ID: {admin_id})")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not BOT_TOKEN.strip():
        print("=" * 60)
        print("❌ ไม่พบ BOT_TOKEN")
        print("กรุณาใส่ค่าในตัวแปร BOT_TOKEN ในส่วนตั้งค่าด้านบนของไฟล์นี้")
        print("=" * 60)
        return
    client.run(BOT_TOKEN)


if __name__ == "__main__":
    main()
