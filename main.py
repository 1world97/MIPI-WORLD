import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
import asyncio
import aiohttp
import re
import os
from datetime import datetime, timedelta

# ========== SETTING UTAMA ==========
BANNER_MIPI = os.getenv("BANNER_MIPI", "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/56a25f63-21b9-56b4-851c-d5d1c6b25943.jpeg")
TOKEN = os.getenv("TOKEN")
QRIS_URL = "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/IMG_6533.jpeg"
BANNER_TICKET_URL = "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/56a25f63-21b9-56b4-851c-d5d1c6b25943.jpeg"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== 1. SETUP FINAL - ROLE + CHANNEL + KATEGORI ==========
@bot.tree.command(name="setup", description="Setup MIPI WORLD FINAL - Role + Channel + Kategori")
@app_commands.checks.has_permissions(administrator=True)
async def setup_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    everyone = guild.default_role

    def cari_role(nama):
        return discord.utils.get(guild.roles, name=nama)

    roles_data = [
        ("👑┃Owner", discord.Color.red(), True),
        ("🛡️┃Admin", discord.Color.orange(), True),
        ("🎧┃Staff", discord.Color.gold(), True),
        ("🛠️┃Moderator", discord.Color.blue(), True),
        ("✅┃Member", discord.Color.green(), True),
        ("🛒┃Buyer", discord.Color.purple(), True),
        ("👤┃Unverified", discord.Color.dark_grey(), False),
    ]
    created_roles = {}
    for nama, warna, pisah in roles_data:
        r = cari_role(nama)
        if not r:
            r = await guild.create_role(name=nama, colour=warna, hoist=pisah, mentionable=True, reason="Setup MIPI WORLD")
        created_roles[nama] = r

    owner_role = created_roles["👑┃Owner"]
    admin_role = created_roles["🛡️┃Admin"]
    staff_role = created_roles["🎧┃Staff"]
    mod_role = created_roles["🛠️┃Moderator"]
    member_role = created_roles["✅┃Member"]

    try:
        await interaction.user.add_roles(owner_role)
    except: pass

    public = {everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    public_readonly = {everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False)}
    verify_only = {everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True), member_role: discord.PermissionOverwrite(view_channel=False)}
    member_only = {everyone: discord.PermissionOverwrite(view_channel=False), member_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), mod_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    staff_only = {everyone: discord.PermissionOverwrite(view_channel=False), staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), owner_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}

    cat1 = await guild.create_category("⎯⎯⎯• Public Area")
    await guild.create_text_channel("👋┃𝖶𝖾𝗅𝖼𝗈𝗆𝖾", category=cat1, overwrites=public_readonly)
    await guild.create_text_channel("📜┃𝖱𝗎𝗅𝖾𝗌", category=cat1, overwrites=public_readonly)
    await guild.create_text_channel("✅┃𝖵𝖾𝗋𝗂𝖿𝗂𝗄𝖺𝗌𝗂", category=cat1, overwrites=verify_only)
    await guild.create_text_channel("📢┃𝖯𝖾𝗇𝗀𝗎𝗆𝗎𝗆𝖺𝗇", category=cat1, overwrites=public_readonly)
    await guild.create_text_channel("💬┃𝖢𝗁𝖺𝗍・𝖯𝗎𝖻𝗅𝗂𝗄", category=cat1, overwrites=public)

    cat2 = await guild.create_category("⎯⎯⎯• Mipi Store")
    await guild.create_text_channel("🛒┃𝖮𝗋𝖽𝖾𝗋・𝖱𝗈𝖻𝗎𝗑", category=cat2, overwrites=public_readonly)
    await guild.create_text_channel("🏆┃𝖳𝗈𝗉・𝖯𝖾𝗆𝖻𝖾𝗅𝗂", category=cat2, overwrites=public_readonly)
    await guild.create_text_channel("💳┃𝖢𝖾𝗄・𝖲𝖺𝗅𝖽𝗈", category=cat2, overwrites=public)
    await guild.create_text_channel("📦┃𝖮𝗋𝖽𝖾𝗋・𝖲𝗍𝖺𝗍𝗎𝗌", category=cat2, overwrites=public_readonly)
    await guild.create_text_channel("💬┃𝖵𝗈𝗎𝖼𝗁", category=cat2, overwrites=public)
    await guild.create_text_channel("⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂", category=cat2, overwrites=public)

    cat3 = await guild.create_category("⎯⎯⎯• Member Area")
    await guild.create_text_channel("💭┃𝖢𝗁𝖺𝗍・𝖬𝖾𝗆𝖻𝖾𝗋", category=cat3, overwrites=member_only)
    await guild.create_text_channel("📸┃𝖦𝖺𝗅𝗅𝖾𝗋𝗒・𝖱𝗈𝖻𝗅𝗈𝗑", category=cat3, overwrites=member_only)
    await guild.create_text_channel("🎮┃𝖬𝖺𝖻𝖺𝗋・𝖱𝗈𝖻𝗅𝗈𝗑", category=cat3, overwrites=member_only)
    await guild.create_text_channel("🎁┃𝖦𝗂𝗏𝖾𝖺𝗐𝖺𝗒", category=cat3, overwrites=member_only)
    await guild.create_text_channel("🔍┃𝖢𝖾𝗄・𝖠𝗏𝖺𝗍𝖺𝗋", category=cat3, overwrites=member_only)
    await guild.create_text_channel("💰┃𝖢𝖾𝗄・𝖱𝖻𝗑", category=cat3, overwrites=member_only)

    cat4 = await guild.create_category("⎯⎯⎯• Rekber Area")
    await guild.create_text_channel("🤝┃𝖱𝖾𝗄𝖻𝖾𝗋・𝖯𝖺𝗇𝖾𝗅", category=cat4, overwrites=public_readonly)
    await guild.create_text_channel("📜┃𝖧𝗂𝗌𝗍𝗈𝗋𝗒・𝖱𝖾𝗄𝖻𝖾𝗋", category=cat4, overwrites=public_readonly)

    cat5 = await guild.create_category("⎯⎯⎯• Voice Public")
    await guild.create_text_channel("✨〢𝖲etting・𝖵oice", category=cat5, overwrites=public)
    await guild.create_voice_channel("🔈〢Voice・𝖯𝗎𝖻𝗅𝗂𝗄", category=cat5, overwrites=public)
    await guild.create_voice_channel("💤┃𝖠𝖿𝗄", category=cat5, overwrites=public)

    cat6 = await guild.create_category("⎯⎯⎯• Voice Member")
    await guild.create_voice_channel("🔈〢Voice・𝖬𝖾𝗆𝖻𝖾𝗋", category=cat6, overwrites=member_only)
    await guild.create_voice_channel("💤┃𝖠𝖿𝗄", category=cat6, overwrites=member_only)

    cat7 = await guild.create_category("⎯⎯⎯• Staff Only")
    await guild.create_text_channel("🔕┃𝖱𝗎𝖺𝗇𝗀・𝖲𝗍𝖺𝖿", category=cat7, overwrites=staff_only)
    await guild.create_voice_channel("☏〢Staff・Voice", category=cat7, overwrites=staff_only)

    await interaction.followup.send("✅ Setup MIPI WORLD FINAL Berhasil!\n\n**Role:** 👑 Owner | 🛡️ Admin | 🎧 Staff | 🛠️ Moderator | ✅ Member | 🛒 Buyer\n**Channel:** Public Area • Mipi Store • Member Area • Rekber Area • Voice Public • Voice Member • Staff Only\n\nKamu otomatis jadi 👑 Owner!", ephemeral=True)

# ========== 2. GIVERROLE ==========
@bot.tree.command(name="giverole", description="Kasih role ke seseorang")
@app_commands.describe(user="Tag orangnya", role="Pilih role nya")
@app_commands.checks.has_permissions(administrator=True)
async def giverole_slash(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await user.add_roles(role)
    await interaction.response.send_message(f"✅ {user.mention} udah dikasih role {role.mention}!")

# ========== 3. VERIFY ==========
class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="✅ Verifikasi", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction: discord.Interaction, button: Button):
        member_role = discord.utils.get(interaction.guild.roles, name="✅┃Member")
        unverif_role = discord.utils.get(interaction.guild.roles, name="👤┃Unverified")
        if not member_role:
            member_role = await interaction.guild.create_role(name="✅┃Member", colour=discord.Color.green())
        await interaction.user.add_roles(member_role)
        if unverif_role:
            try: await interaction.user.remove_roles(unverif_role)
            except: pass
        await interaction.response.send_message("✅ Kamu berhasil terverifikasi! Selamat datang di MIPI WORLD!\nKamu sekarang bisa akses Member Area!", ephemeral=True)

@bot.tree.command(name="verif", description="Kirim panel verifikasi")
@app_commands.checks.has_permissions(administrator=True)
async def verif_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="✅  VERIFIKASI MEMBER", description="Klik tombol di bawah untuk verifikasi & buka akses semua channel!\n\n**MIPI WORLD • Aman • Cepat • Terpercaya**", color=discord.Color.green())
    embed.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=embed, view=VerifyView())

# ========== 4. TICKET - AUTO QRIS ==========
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🎫 Buka Ticket Order", style=discord.ButtonStyle.blurple, custom_id="ticket_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        cat = discord.utils.get(guild.categories, name="⎯⎯⎯• Mipi Store")
        if not cat:
            cat = discord.utils.get(guild.categories, name="🛒┃𝖬𝗂𝗉𝗂 𝖲𝗍𝗈𝗋𝖾")
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }
        ch = await guild.create_text_channel(f"🎫┃{interaction.user.name}", category=cat, overwrites=overwrites)
        embed1 = discord.Embed(title="🎫  TICKET ORDER - MIPI WORLD", description=f"Halo {interaction.user.mention}!\n\nSelamat datang di ticket order MIPI WORLD!\nSilakan isi format order di bawah & langsung scan QRIS untuk pembayaran!", color=discord.Color.from_rgb(88,101,242))
        embed1.set_image(url=BANNER_TICKET_URL)
        await ch.send(embed=embed1)
        embed2 = discord.Embed(title="📝  FORMAT ORDER", description="**• Nama Roblox:**\n**• Produk:** (Send / Vilog / Pluss)\n**• Nominal:**\n**• Bukti TF:** (Kirim foto bukti transfer di sini)\n\nAdmin akan segera merespon!", color=discord.Color.green())
        await ch.send(embed=embed2)
        embed3 = discord.Embed(title="💰  PEMBAYARAN - QRIS MIPI WORLD", description="Silakan scan QR di bawah untuk bayar!\n\n**Nama:** Rafi Store\n**NMID:** ID1026603621750\n\n⚠️ **PENTING:**\n• Bayar sesuai nominal order\n• Kirim bukti TF di ticket ini\n• Jangan kirim bukti TF palsu!", color=discord.Color.from_rgb(255, 193, 7))
        embed3.set_image(url=QRIS_URL)
        embed3.set_footer(text="MIPI WORLD • QRIS Otomatis | Rafi Store")
        await ch.send(embed=embed3, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket kamu udah dibuat: {ch.mention}\nQRIS udah dikirim otomatis di dalam ticket!", ephemeral=True)

class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

@bot.tree.command(name="ticket", description="Kirim panel ticket order")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_slash(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒  ORDER ROBUX - MIPI WORLD", description="Mau order Robux? Klik tombol di bawah!\n\n📤 Robux Send\n📦 Robux Vilog\n⭐ Roblox Pluss\n\nAdmin fast respon!", color=discord.Color.from_rgb(88,101,242))
    embed.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=embed, view=TicketView())

# ========== 5. PRICELIST ==========
class PricelistSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Robux Send", description="Lihat rincian daftar harga Robux Send", emoji="📤"),
            discord.SelectOption(label="Robux Vilog", description="Lihat rincian daftar harga Robux Vilog", emoji="📦"),
            discord.SelectOption(label="Roblox Pluss", description="Lihat rincian daftar harga Roblox Pluss", emoji="⭐"),
        ]
        super().__init__(placeholder="Pilih Kategori Produk (Robux / Pluss)", min_values=1, max_values=1, options=options, custom_id="pricelist_select")
    async def callback(self, interaction: discord.Interaction):
        p = self.values[0]
        if p == "Robux Send":
            e = discord.Embed(title="📤  DAFTAR HARGA • ROBUX SEND", color=discord.Color.from_rgb(88,101,242))
            e.add_field(name="📤 Rincian Daftar Harga:", value="• 100 R$ : Rp 16.000\n• 500 R$ : Rp 75.000\n• 1000 R$ : Rp 150.000\n• dst.", inline=False)
        elif p == "Robux Vilog":
            e = discord.Embed(title="📦  DAFTAR HARGA • ROBUX VILOG", color=discord.Color.from_rgb(88,101,242))
            e.add_field(name="📦 Rincian Daftar Harga:", value="• 500 R$ : Rp 77.500\n• 1000 R$ : Rp 155.000\n• 2000 R$ : Rp 310.000\n• 5000 R$ : Rp 775.000\n• dst.", inline=False)
        else:
            e = discord.Embed(title="⭐  DAFTAR HARGA • ROBLOX PLUSS", color=discord.Color.from_rgb(88,101,242))
            e.add_field(name="⭐ Rincian Daftar Harga:", value="• 1 Bulan : Rp 120.000\n• 3 Bulan : Rp 255.000\n• 12 Bulan : Rp 995.000\n\n**Plus+ Robux:**\n• Plus+ 500 Robux : Rp 230.000\n• Plus+ 1000 Robux : Rp 310.000\n• Plus+ 2000 Robux : Rp 465.000", inline=False)
        e.set_footer(text="MIPI WORLD")
        await interaction.response.send_message(embed=e, ephemeral=True)

class PricelistView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PricelistSelect())

@bot.tree.command(name="pricelist", description="Kirim panel pricelist MIPI WORLD")
@app_commands.checks.has_permissions(administrator=True)
async def pricelist_slash(interaction: discord.Interaction):
    e = discord.Embed(title="📋  DAFTAR HARGA\nROBUX • MIPI WORLD", description="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\nSilakan pilih kategori produk pada menu dropdown di bawah:\n\n⊙ Robux Send\n⊙ Robux Vilog\n⊙ Roblox Pluss\n\n• Harga sewaktu-waktu dapat berubah mengikuti rate pasar.", color=discord.Color.from_rgb(88,101,242))
    e.set_image(url=BANNER_MIPI)
    e.set_footer(text="MIPI WORLD • Aman • Cepat • Terpercaya")
    await interaction.response.send_message(embed=e, view=PricelistView())

# ========== 6. WELCOME ==========
@bot.event
async def on_member_join(member):
    ch = discord.utils.get(member.guild.text_channels, name="👋┃𝖶𝖾𝗅𝖼𝗈𝗆𝖾")
    if not ch: return
    e = discord.Embed(title="👋  WELCOME", description=f"{member.mention}", color=discord.Color.from_rgb(88,101,242))
    e.set_image(url=BANNER_MIPI)
    await ch.send(embed=e)

# ========== 7. CEK AVATAR LENGKAP ==========
async def get_roblox_id(username: str):
    async with aiohttp.ClientSession() as session:
        async with session.post("https://users.roblox.com/v1/usernames/users", json={"usernames": [username]}) as r:
            data = await r.json()
            if not data.get("data"): return None
            return data["data"][0]["id"]

async def get_asset_names(asset_ids: list):
    if not asset_ids: return {}
    hasil = {}
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(asset_ids), 50):
            chunk = asset_ids[i:i+50]
            params = "&".join([f"AssetIds={x}" for x in chunk])
            async with session.get(f"https://catalog.roblox.com/v1/assets?{params}") as r:
                if r.status == 200:
                    data = await r.json()
                    for item in data.get("data", []):
                        hasil[item["id"]] = item["name"]
    return hasil

@bot.tree.command(name="cekavatar", description="Cek avatar Roblox lengkap sampe baju & aksesoris")
@app_commands.describe(username="Username Roblox, contoh: Builderman")
async def cekavatar_lengkap(interaction: discord.Interaction, username: str):
    await interaction.response.defer()
    user_id = await get_roblox_id(username)
    if not user_id:
        await interaction.followup.send(f"❌ Username `{username}` ga ketemu!")
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as r:
            profil = await r.json()
        async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=720x720&format=Png&isCircular=false") as r:
            full_img = (await r.json())["data"][0]["imageUrl"]
        async with session.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false") as r:
            head_img = (await r.json())["data"][0]["imageUrl"]
        async with session.get(f"https://avatar.roblox.com/v1/users/{user_id}/currently-wearing") as r:
            wearing = await r.json()
        async with session.get(f"https://avatar.roblox.com/v1/users/{user_id}/avatar") as r:
            avatar_detail = await r.json()
    asset_ids = [x["id"] for x in wearing.get("assetIds", [])]
    names = await get_asset_names(asset_ids)
    kategori = {}
    for item in wearing.get("assetIds", []):
        tipe = item["assetType"]["name"]
        nama_item = names.get(item["id"], f"ID {item['id']}")
        if tipe not in kategori:
            kategori[tipe] = []
        kategori[tipe].append(f"• [{nama_item}](https://www.roblox.com/catalog/{item['id']}/)")
    def ambil(nama_kategori, emoji):
        if nama_kategori in kategori:
            return f"{emoji} **{nama_kategori}:**\n" + "\n".join(kategori[nama_kategori]) + "\n\n"
        return ""
    deskripsi_lengkap = ""
    deskripsi_lengkap += ambil("HairAccessory", "💇")
    deskripsi_lengkap += ambil("Hat", "🎩")
    deskripsi_lengkap += ambil("Face", "😀")
    deskripsi_lengkap += ambil("Head", "🗣️")
    deskripsi_lengkap += ambil("Shirt", "👕")
    deskripsi_lengkap += ambil("Pants", "👖")
    deskripsi_lengkap += ambil("TShirt", "👚")
    deskripsi_lengkap += ambil("ShirtAccessory", "🧥")
    deskripsi_lengkap += ambil("PantsAccessory", "👖")
    deskripsi_lengkap += ambil("JacketAccessory", "🧥")
    deskripsi_lengkap += ambil("SweaterAccessory", "🧶")
    deskripsi_lengkap += ambil("ShortsAccessory", "🩳")
    deskripsi_lengkap += ambil("DressSkirtAccessory", "👗")
    deskripsi_lengkap += ambil("BackAccessory", "🎒")
    deskripsi_lengkap += ambil("FrontAccessory", "🎀")
    deskripsi_lengkap += ambil("NeckAccessory", "📿")
    deskripsi_lengkap += ambil("ShoulderAccessory", "🎒")
    deskripsi_lengkap += ambil("WaistAccessory", "🔗")
    deskripsi_lengkap += ambil("FaceAccessory", "👓")
    deskripsi_lengkap += ambil("Gear", "⚔️")
    sudah = ["HairAccessory","Hat","Face","Head","Shirt","Pants","TShirt","ShirtAccessory","PantsAccessory","JacketAccessory","SweaterAccessory","ShortsAccessory","DressSkirtAccessory","BackAccessory","FrontAccessory","NeckAccessory","ShoulderAccessory","WaistAccessory","FaceAccessory","Gear"]
    lainnya = ""
    for k, v in kategori.items():
        if k not in sudah:
            lainnya += f"✨ **{k}:**\n" + "\n".join(v) + "\n\n"
    deskripsi_lengkap += lainnya
    if not deskripsi_lengkap:
        deskripsi_lengkap = "Avatar ini ga pake item / Avatar default (Noob)"
    embed = discord.Embed(title=f"🖼️  AVATAR LENGKAP • {profil['name']}", description=f"**Display:** {profil['displayName']} | **ID:** `{user_id}`\n**Total Item Dipake:** {len(asset_ids)} item", color=discord.Color.from_rgb(88,101,242))
    embed.add_field(name="👕👖 BAJU & AKSESORIS YANG DIPAKE:", value=deskripsi_lengkap[:1020], inline=False)
    embed.add_field(name="🎨 Warna Badan", value=f"Kepala: {avatar_detail.get('headColorId')} | Torso: {avatar_detail.get('torsoColorId')} | Lengan: {avatar_detail.get('rightArmColorId')} | Kaki: {avatar_detail.get('leftLegColorId')}", inline=False)
    embed.add_field(name="🔗 Link Profil", value=f"[Klik Disini](https://www.roblox.com/users/{user_id}/profile)", inline=False)
    embed.set_image(url=full_img)
    embed.set_thumbnail(url=head_img)
    embed.set_footer(text="MIPI WORLD • Cek Avatar Lengkap | Klik nama item buat liat di Catalog")
    await interaction.followup.send(embed=embed)

# ========== 8. CEK GAMEPASS & CEK PENDING ==========
def ambil_id_gamepass(input_teks: str):
    angka = re.findall(r"\d+", input_teks)
    return angka[0] if angka else None

@bot.tree.command(name="cekgamepass", description="Cek detail & harga Gamepass Roblox")
@app_commands.describe(gamepass="Link atau ID Gamepass, contoh: 12345678 atau link roblox.com/game-pass/...")
async def cekgamepass_slash(interaction: discord.Interaction, gamepass: str):
    await interaction.response.defer()
    gp_id = ambil_id_gamepass(gamepass)
    if not gp_id:
        await interaction.followup.send("❌ ID Gamepass ga ketemu! Kirim link atau ID nya, contoh: `12345678`")
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://apis.roblox.com/game-passes/v1/game-passes/{gp_id}") as r:
            if r.status != 200:
                await interaction.followup.send(f"❌ Gamepass ID `{gp_id}` ga ketemu / udah dihapus!")
                return
            data = await r.json()
        async with session.get(f"https://thumbnails.roblox.com/v1/game-passes?gamePassIds={gp_id}&size=512x512&format=Png&isCircular=false") as r:
            thumb = await r.json()
            img = thumb["data"][0]["imageUrl"] if thumb["data"] else None
    price = data.get("price")
    harga_teks = f"{price} Robux" if price is not None else "GRATIS / OFF SALE"
    status = "✅ ON SALE" if data.get("isForSale") else "❌ OFF SALE / TIDAK DIJUAL"
    embed = discord.Embed(title=f"🎟️  GAMEPASS • {data['name']}", color=discord.Color.from_rgb(88,101,242))
    embed.add_field(name="🆔 Gamepass ID", value=f"`{data['id']}`", inline=True)
    embed.add_field(name="💰 Harga", value=f"**{harga_teks}**", inline=True)
    embed.add_field(name="📦 Status", value=status, inline=True)
    embed.add_field(name="👤 Creator", value=f"{data['creator']['name']} ({data['creator']['type']})", inline=True)
    embed.add_field(name="📅 Dibuat", value=data['created'][:10], inline=True)
    embed.add_field(name="🔗 Link", value=f"[Klik Disini](https://www.roblox.com/game-pass/{data['id']})", inline=False)
    embed.add_field(name="📝 Deskripsi", value=(data['description'] or "Tidak ada deskripsi")[:500], inline=False)
    if img:
        embed.set_thumbnail(url=img)
    embed.set_footer(text="MIPI WORLD • Cek Gamepass | Pastikan harga sama dengan orderan!")
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="cekpending", description="Cek estimasi Robux Pending dari Gamepass")
@app_commands.describe(gamepass="Link / ID Gamepass yang baru dibeli", tanggal_beli="Kapan dibelinya? Contoh: 2026-11-20 atau hari ini")
async def cekpending_slash(interaction: discord.Interaction, gamepass: str, tanggal_beli: str = None):
    await interaction.response.defer()
    gp_id = ambil_id_gamepass(gamepass)
    if not gp_id:
        await interaction.followup.send("❌ ID Gamepass ga ketemu!")
        return
    try:
        if not tanggal_beli or tanggal_beli.lower() in ["hari ini", "today", "sekarang"]:
            tgl = datetime.now()
        else:
            tgl = datetime.strptime(tanggal_beli, "%Y-%m-%d")
    except:
        await interaction.followup.send("❌ Format tanggal salah! Pake `YYYY-MM-DD`, contoh: `2026-11-20` atau ketik `hari ini`")
        return
    cair_3hari = tgl + timedelta(days=3)
    cair_7hari = tgl + timedelta(days=7)
    sisa_hari = (cair_3hari - datetime.now()).days
    sisa_teks = f"Kurang lebih **{max(0, sisa_hari)} hari lagi**" if sisa_hari > 0 else "✅ **UDAH BISA CAIR / CEK DI PENDING ROBUX!**"
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://apis.roblox.com/game-passes/v1/game-passes/{gp_id}") as r:
            if r.status != 200:
                await interaction.followup.send(f"❌ Gamepass ID `{gp_id}` ga ketemu!")
                return
            data = await r.json()
    harga = data.get("price") or 0
    diterima = int(harga * 0.7)
    embed = discord.Embed(title=f"⏳  CEK PENDING • {data['name']}", color=discord.Color.orange())
    embed.add_field(name="🆔 Gamepass ID", value=f"`{data['id']}`", inline=True)
    embed.add_field(name="💰 Harga Gamepass", value=f"{harga} Robux", inline=True)
    embed.add_field(name="💸 Yang Masuk (70%)", value=f"**{diterima} Robux** (Roblox potong 30%)", inline=False)
    embed.add_field(name="📅 Tanggal Beli", value=tgl.strftime("%d %B %Y"), inline=True)
    embed.add_field(name="⏰ Estimasi Cair", value=f"**{cair_3hari.strftime('%d %B %Y')}** - {cair_7hari.strftime('%d %B %Y')}", inline=True)
    embed.add_field(name="📊 Status", value=sisa_teks, inline=False)
    embed.add_field(name="🔗 Cek Manual", value="Cek di Roblox > [Pending Robux](https://www.roblox.com/transactions) > Pilih **Pending Robux**", inline=False)
    embed.set_footer(text="MIPI WORLD • Cek Pending | Robux Pending biasanya cair 3-7 hari")
    await interaction.followup.send(embed=embed)

# ========== 9. ON READY ==========
@bot.event
async def on_ready():
    print(f"{bot.user} Online!")
    bot.add_view(VerifyView())
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    bot.add_view(PricelistView())
    try:
        synced = await bot.tree.sync()
        print(f"Sync {len(synced)} command!")
    except Exception as ex:
        print(ex)

bot.run(TOKEN)
