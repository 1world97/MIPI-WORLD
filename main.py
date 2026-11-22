import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button, Modal, TextInput
import asyncio, aiohttp, re, os, json, random, time
from datetime import datetime, timedelta
from collections import defaultdict, deque

# ========== SETTING ==========
BANNER_MIPI = os.getenv("BANNER_MIPI", "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/56a25f63-21b9-56b4-851c-d5d1c6b25943.jpeg")
TOKEN = os.getenv("TOKEN")
QRIS_URL = "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/IMG_6533.jpeg"
BANNER_TICKET_URL = BANNER_MIPI
DANA_NOMOR = "0895-2642-4213"
DANA_NAMA = "Rafi Store"

# --- EMOJI GERAK / NITRO ---
# Cara pake: setelah kamu /addemoji nama:fire link:gif, Discord kasih ID nya.
# Ganti ID di bawah pake ID emoji kamu biar embed nya ikut gerak!
# Contoh asli: "<a:fire:123456789012345678>" - yang <a: = ANIMATED, yang <: = DIAM
EMOJI_FIRE = "<a:fire:123456789012345678>"  # <-- Ganti pake ID emoji gif kamu!
EMOJI_CROWN = "👑" # Kalo belum ada emoji gerak, pake unicode dulu, tetep jalan!
EMOJI_ROBUX = "💰"
EMOJI_CHECK = "✅"
# Tips: Kalo mau cepet, pake emoji bawaan Discord yang gerak di HP: 🔥 ✨ 🎉 💎 ⚡ itu di HP keliatan gerak kalo pake Nitro!

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== DATABASE ==========
def load_json(n, d):
    if os.path.exists(n):
        try:
            with open(n, "r") as f: return json.load(f)
        except: return d
    return d
def save_json(n, d):
    with open(n, "w") as f: json.dump(d, f, indent=2)

HARGA_VISEND = load_json("harga_visend.json", {"500":75000,"1000":150000,"2000":300000,"3000":450000,"4000":600000,"5000":750000,"100_ecer":16000,"200_ecer":32000,"300_ecer":48000,"400_ecer":64000})
HARGA_NITRO = load_json("harga_nitro.json", {"nitro_basic_1bulan":55000,"nitro_full_1bulan":125000,"nitro_basic_1tahun":550000,"nitro_full_1tahun":1250000,"boost_1x":35000,"boost_3x":95000})
ORDERS = load_json("orders.json", {})
SALDO = load_json("saldo.json", {})
REKBER_HISTORY = load_json("rekber_history.json", [])
VOUCH_DATA = load_json("vouch.json", [])
CONFIG = load_json("config_mipi.json", {"toko_buka": True, "jam_buka": "08:00", "jam_tutup": "23:00", "antispam": True, "antispam_timeout": 60, "leaderboard_msg_id": None, "leaderboard_channel_id": None, "status_msg_id": None, "emoji_session": None, "afk_channel_id": None})
GIVEAWAYS = {}
# Antispam
SPAM_TRACK = defaultdict(lambda: deque(maxlen=10))
AFK_VC = None

def format_rupiah(n): return f"Rp {int(n):,}".replace(",", ".")
def tambah_order(uid, robux, rupiah):
    u=str(uid)
    if u not in ORDERS: ORDERS[u]={"total_order":0,"total_robux":0,"total_rupiah":0}
    ORDERS[u]["total_order"]+=1; ORDERS[u]["total_robux"]+=int(robux or 0); ORDERS[u]["total_rupiah"]+=int(rupiah or 0)
    save_json("orders.json", ORDERS)
def save_config(): save_json("config_mipi.json", CONFIG)

# ========== HELPER TICKET + VOUCH ==========
async def kirim_vouch_testimoni(guild, buyer, produk, jumlah, bukti_url, admin, pesan=""):
    VOUCH_DATA.append({"buyer":str(buyer),"buyer_id":buyer.id,"produk":produk,"robux":jumlah,"bukti":bukti_url,"tanggal":datetime.now().strftime("%d %B %Y %H:%M"),"admin":str(admin)})
    save_json("vouch.json", VOUCH_DATA)
    try:
        angka=int(re.findall(r"\d+", jumlah)[0]) if re.findall(r"\d+", jumlah) else 0
        tambah_order(buyer.id, angka, 0)
    except: pass
    e1=discord.Embed(title=f"⭐ TESTIMONI - ORDER BERHASIL! {EMOJI_FIRE}", description=f"**Pembeli:** {buyer.mention}\n**Produk:** {produk}\n**Jumlah:** **{jumlah}**\n**Status:** ✅ **ROBUX UDAH MASUK!**\n**Admin:** {admin.mention}\n\n💬 *{pesan or 'Makasih udah order di MIPI STORE! Aman, Cepat, Terpercaya! 🎀'}*", color=discord.Color.from_rgb(255,158,187))
    if bukti_url: e1.set_image(url=bukti_url)
    e1.set_footer(text=f"MIPI WORLD • Testimoni #{len(VOUCH_DATA)}")
    e1.set_thumbnail(url=buyer.display_avatar.url)
    e2=discord.Embed(title="✅ VOUCH - MIPI STORE TERPERCAYA!", description=f"**{buyer.mention}** udah order **{produk} - {jumlah}**\n\n✅ **SUCCESS!**\n⭐ Rating: ⭐⭐⭐⭐⭐", color=discord.Color.green())
    if bukti_url: e2.set_image(url=bukti_url)
    testi_ch=discord.utils.get(guild.text_channels, name="⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂")
    vouch_ch=discord.utils.get(guild.text_channels, name="💬┃𝖵𝗈𝗎𝖼𝗁")
    if testi_ch: await testi_ch.send(embed=e1)
    if vouch_ch: await vouch_ch.send(embed=e2)
    return len(VOUCH_DATA)

class TestimoniModal(Modal, title="Buat Testimoni - Robux Masuk!"):
    buyer_tag = TextInput(label="Tag Pembeli (@Username)", placeholder="@Username Pembeli", required=True)
    produk = TextInput(label="Produk Yang Dibeli", placeholder="Visend / Vilog / 8 Bit", default="Visend", required=True)
    jumlah = TextInput(label="Jumlah Robux Yang Masuk", placeholder="Contoh: 500 Robux", required=True)
    link_bukti = TextInput(label="Link Foto Bukti Robux Masuk", placeholder="Paste link foto / kosongin", required=False, style=discord.TextStyle.paragraph)
    pesan = TextInput(label="Pesan Buyer (Opsional)", placeholder="Makasih kak!", required=False, style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction):
        buyer=interaction.user
        nama=self.buyer_tag.value.replace("@","").replace("<","").replace(">","").replace("!","").strip()
        if nama.isdigit(): buyer=interaction.guild.get_member(int(nama)) or buyer
        else:
            for m in interaction.guild.members:
                if nama.lower() in m.name.lower() or nama.lower() in m.display_name.lower(): buyer=m; break
        nomor=await kirim_vouch_testimoni(interaction.guild, buyer, self.produk.value, self.jumlah.value, self.link_bukti.value.strip(), interaction.user, self.pesan.value)
        await interaction.response.send_message(f"✅ **TESTIMONI #{nomor} BERHASIL!** Udah ke-post ke Testimoni + Vouch + Top Pembeli!", ephemeral=True)

class TicketActionView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⭐ Jadikan Testimoni", style=discord.ButtonStyle.green, emoji="⭐", custom_id="jadi_testimoni")
    async def jadi(self, i, b): await i.response.send_modal(TestimoniModal())
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, i, b):
        await i.response.send_message("Ticket ditutup 5 detik..."); await asyncio.sleep(5); await i.channel.delete()
class CloseTicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⭐ Jadikan Testimoni", style=discord.ButtonStyle.green, emoji="⭐", custom_id="jadi_testimoni")
    async def jadi(self, i, b): await i.response.send_modal(TestimoniModal())
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, i, b):
        await i.response.send_message("Ticket ditutup 5 detik..."); await asyncio.sleep(5); await i.channel.delete()

async def kirim_ticket_dari_form(interaction, jenis, judul, data_form):
    if not CONFIG.get("toko_buka", True):
        await interaction.response.send_message("❌ **TOKO LAGI TUTUP!** Coba lagi jam operasional ya! Cek `/status info`", ephemeral=True); return None
    guild=interaction.guild
    cat=discord.utils.get(guild.categories, name="⎯⎯⎯• Mipi Store") or discord.utils.get(guild.categories, name="⎯⎯⎯• Ticket & Order")
    overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
    ch=await guild.create_text_channel(f"🎫┃{jenis}-{interaction.user.name}", category=cat, overwrites=overwrites)
    e1=discord.Embed(title=f"🎫 TICKET {judul} - MIPI WORLD {EMOJI_FIRE}", description=f"Halo {interaction.user.mention}!\nTicket udah dibuat! Format udah terisi otomatis!", color=discord.Color.from_rgb(88,101,242)); e1.set_image(url=BANNER_TICKET_URL)
    await ch.send(embed=e1)
    isi=""
    for k,v in data_form.items():
        if "SANDI" in k.upper() or "PASSWORD" in k.upper(): isi+=f"**{k}:** ||{v}||\n"
        else: isi+=f"**{k}:** {v}\n"
    if jenis=="visend":
        for key,harga in HARGA_VISEND.items():
            if key.replace("_ecer","") in data_form.get("Paket yang dipilih",""): isi+=f"\n**💰 Total Bayar:** **{format_rupiah(harga)}**\n"; break
    await ch.send(embed=discord.Embed(title="📝 FORMAT ORDER - UDAH TERISI!", description=isi, color=discord.Color.green()))
    try:
        sc=discord.utils.get(guild.text_channels, name="📦┃𝖮𝗋𝖽𝖾𝗋・𝖲𝗍𝖺𝗍𝗎𝗌")
        if sc: await sc.send(embed=discord.Embed(title="📦 ORDER BARU!", description=f"**Pembeli:** {interaction.user.mention}\n**Produk:** {judul}\n**Paket:** {data_form.get('Paket yang dipilih','-')}\n**Ticket:** {ch.mention}\n**Status:** ⏳ Diproses", color=discord.Color.orange()))
    except: pass
    e3=discord.Embed(title="💰 PEMBAYARAN - QRIS / DANA", description=f"**1. QRIS**\nNama: Rafi Store\nNMID: ID1026603621750\n\n**2. DANA**\nNomor: **{DANA_NOMOR}**\nAtas Nama: {DANA_NAMA}", color=discord.Color.from_rgb(255,193,7)); e3.set_image(url=QRIS_URL)
    await ch.send(embed=e3)
    await ch.send("⭐ **Staff:** Kalo Robux udah masuk, klik **⭐ Jadikan Testimoni** di bawah!", view=TicketActionView())
    return ch

# ========== MODAL TICKET ==========
class VilogModal(Modal, title="Pesanan Robux Vilog"):
    username=TextInput(label="Username Roblox", placeholder="UsernameRoblox", required=True)
    katasandi=TextInput(label="Kata Sandi Roblox", placeholder="Password (Rahasia!)", required=True)
    paket=TextInput(label="Paket yang dipilih", placeholder="Contoh: 1000 Robux", required=True)
    pembayaran=TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, i):
        d={"Nickname Roblox":i.user.display_name,"Username":self.username.value,"Kata Sandi":self.katasandi.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(i,"vilog","ROBUX VILOG",d)
        if ch: await i.response.send_message(f"✅ Ticket Vilog: {ch.mention}", ephemeral=True)
class VisendModal(Modal, title="Pesanan Robux Visend"):
    nickname=TextInput(label="Nickname Roblox", placeholder="Nickname kamu", required=True)
    username=TextInput(label="Username", placeholder="UsernameRoblox", required=True)
    paket=TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True)
    pembayaran=TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, i):
        d={"Nickname Roblox":self.nickname.value,"Username":self.username.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(i,"visend","VISEND",d)
        if ch: await i.response.send_message(f"✅ Ticket Visend: {ch.mention}", ephemeral=True)
class Bit8Modal(Modal, title="Pesanan Acc 8 Bit"):
    username=TextInput(label="Username Roblox", placeholder="UsernameRoblox kamu", required=True)
    paket=TextInput(label="Paket yang dipilih", placeholder="Contoh: Acc 8 Bit", required=True)
    pembayaran=TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, i):
        d={"Username":self.username.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(i,"8bit","ACC 8 BIT",d)
        if ch: await i.response.send_message(f"✅ Ticket 8 Bit: {ch.mention}", ephemeral=True)
class PlusModal(Modal, title="Pesanan Roblox Plus"):
    username=TextInput(label="Username Roblox", placeholder="UsernameRoblox", required=True)
    katasandi=TextInput(label="Kata Sandi Roblox", placeholder="Password (Rahasia!)", required=True)
    paket=TextInput(label="Paket Plus", placeholder="Contoh: 1 Bulan", required=True)
    pembayaran=TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, i):
        d={"Username":self.username.value,"Kata Sandi":self.katasandi.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(i,"plus","ROBLOX PLUS",d)
        if ch: await i.response.send_message(f"✅ Ticket Plus: {ch.mention}", ephemeral=True)
class AkunModal(Modal, title="Pesanan Beli Akun"):
    akun_dicari=TextInput(label="Akun Yang Dicari", placeholder="Contoh: Akun R6", required=True, style=discord.TextStyle.paragraph)
    budget=TextInput(label="Budget Kamu", placeholder="Contoh: Rp 200.000", required=True)
    username=TextInput(label="Username Roblox Kamu", placeholder="UsernameRoblox", required=True)
    pembayaran=TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, i):
        d={"Akun Yang Dicari":self.akun_dicari.value,"Budget":self.budget.value,"Username Pembeli":self.username.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(i,"akun","BELI AKUN",d)
        if ch: await i.response.send_message(f"✅ Ticket Beli Akun: {ch.mention}", ephemeral=True)

# ========== 1. SETUP + GIVERROLE + VERIFY ==========
@bot.tree.command(name="setup", description="Setup MIPI WORLD FINAL")
@app_commands.checks.has_permissions(administrator=True)
async def setup_slash(interaction):
    await interaction.response.defer(ephemeral=True)
    guild=interaction.guild; everyone=guild.default_role
    def cari(n): return discord.utils.get(guild.roles, name=n)
    roles_data=[("👑┃Owner",discord.Color.red(),True),("🛡️┃Admin",discord.Color.orange(),True),("🎧┃Staff",discord.Color.gold(),True),("🛠️┃Moderator",discord.Color.blue(),True),("✅┃Member",discord.Color.green(),True),("🛒┃Buyer",discord.Color.purple(),True),("👤┃Unverified",discord.Color.dark_grey(),False)]
    cr={}
    for nama,w,p in roles_data:
        r=cari(nama) or await guild.create_role(name=nama, colour=w, hoist=p, mentionable=True); cr[nama]=r
    try: await interaction.user.add_roles(cr["👑┃Owner"])
    except: pass
    public={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    pr={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False)}
    vo={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True), cr["✅┃Member"]: discord.PermissionOverwrite(view_channel=False)}
    mo={everyone: discord.PermissionOverwrite(view_channel=False), cr["✅┃Member"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🎧┃Staff"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🛡️┃Admin"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🛠️┃Moderator"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    so={everyone: discord.PermissionOverwrite(view_channel=False), cr["🎧┃Staff"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🛡️┃Admin"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["👑┃Owner"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    c1=await guild.create_category("⎯⎯⎯• Public Area")
    for n in ["👋┃𝖶𝖾𝗅𝖼𝗈𝗆𝖾","📜┃𝖱𝗎𝗅𝖾𝗌","📢┃𝖯𝖾𝗇𝗀𝗎𝗆𝗎𝗆𝖺𝗇"]: await guild.create_text_channel(n, category=c1, overwrites=pr)
    await guild.create_text_channel("✅┃𝖵𝖾𝗋𝗂𝖿𝗂𝗄𝖺𝗌𝗂", category=c1, overwrites=vo)
    await guild.create_text_channel("💬┃𝖢𝗁𝖺𝗍・𝖯𝗎𝖻𝗅𝗂𝗄", category=c1, overwrites=public)
    c2=await guild.create_category("⎯⎯⎯• Mipi Store")
    for n in ["🛒┃𝖮𝗋𝖽𝖾𝗋・𝖱𝗈𝖻𝗎𝗑","🏆┃𝖳𝗈𝗉・𝖯𝖾𝗆𝖻𝖾𝗅𝗂","📦┃𝖮𝗋𝖽𝖾𝗋・𝖲𝗍𝖺𝗍𝗎𝗌","💬┃𝖵𝗈𝗎𝖼𝗁","⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂"]: await guild.create_text_channel(n, category=c2, overwrites=pr)
    await guild.create_text_channel("💳┃𝖢𝖾𝗄・𝖲𝖺𝗅𝖽𝗈", category=c2, overwrites=public)
    c3=await guild.create_category("⎯⎯⎯• Member Area")
    for n in ["💭┃𝖢𝗁𝖺𝗍・𝖬𝖾𝗆𝖻𝖾𝗋","📸┃𝖦𝖺𝗅𝗅𝖾𝗋𝗒・𝖱𝗈𝖻𝗅𝗈𝗑","🎮┃𝖬𝖺𝖻𝖺𝗋・𝖱𝗈𝖻𝗅𝗈𝗑","🎁┃𝖦𝗂𝗏𝖾𝖺𝗐𝖺𝗒","🔍┃𝖢𝖾𝗄・𝖠𝗏𝖺𝗍𝖺𝗋","💰┃𝖢𝖾𝗄・𝖱𝖻𝗑"]: await guild.create_text_channel(n, category=c3, overwrites=mo)
    c4=await guild.create_category("⎯⎯⎯• Rekber Area")
    await guild.create_text_channel("🤝┃𝖱𝖾𝗄𝖻𝖾𝗋・𝖯𝖺𝗇𝖾𝗅", category=c4, overwrites=pr)
    await guild.create_text_channel("📜┃𝖧𝗂𝗌𝗍𝗈𝗋𝗒・𝖱𝖾𝗄𝖻𝖾𝗋", category=c4, overwrites=pr)
    c5=await guild.create_category("⎯⎯⎯• Voice Public")
    await guild.create_text_channel("✨〢𝖲etting・𝖵oice", category=c5, overwrites=public)
    await guild.create_voice_channel("🔈〢Voice・𝖯𝗎𝖻𝗅𝗂𝗄", category=c5, overwrites=public)
    await guild.create_voice_channel("💤┃𝖠𝖿𝗄", category=c5, overwrites=public)
    c6=await guild.create_category("⎯⎯⎯• Voice Member")
    await guild.create_voice_channel("🔈〢Voice・𝖬𝖾𝗆𝖻𝖾𝗋", category=c6, overwrites=mo)
    await guild.create_voice_channel("💤┃𝖠𝖿𝗄", category=c6, overwrites=mo)
    c7=await guild.create_category("⎯⎯⎯• Staff Only")
    await guild.create_text_channel("🔕┃𝖱𝗎𝖺𝗇𝗀・𝖲𝗍𝖺𝖿", category=c7, overwrites=so)
    await guild.create_voice_channel("☏〢Staff・Voice", category=c7, overwrites=so)
    await interaction.followup.send("✅ Setup Berhasil!", ephemeral=True)
@bot.tree.command(name="giverole", description="Kasih role ke seseorang")
@app_commands.checks.has_permissions(administrator=True)
async def giverole_slash(interaction, user: discord.Member, role: discord.Role):
    await user.add_roles(role); await interaction.response.send_message(f"✅ {user.mention} dikasih {role.mention}!")
class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="✅ Verifikasi", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, i, b):
        mr=discord.utils.get(i.guild.roles, name="✅┃Member") or await i.guild.create_role(name="✅┃Member", colour=discord.Color.green())
        await i.user.add_roles(mr); await i.response.send_message("✅ Terverifikasi! Selamat datang di MIPI WORLD!", ephemeral=True)
@bot.tree.command(name="verif", description="Kirim panel verifikasi")
@app_commands.checks.has_permissions(administrator=True)
async def verif_slash(interaction):
    e=discord.Embed(title="✅ VERIFIKASI MEMBER", description="Klik tombol di bawah!", color=discord.Color.green()); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e, view=VerifyView())

# ========== 2. TICKET PANEL ==========
class VisendSelect(Select):
    def __init__(self):
        opts=[discord.SelectOption(label=f"{k.replace('_ecer',' Eceran')} Robux - {format_rupiah(v)}", emoji="⚡", value=k) for k,v in HARGA_VISEND.items()]
        super().__init__(placeholder="⚡ Pilih Jumlah Visend!", options=opts, custom_id="visend_select")
    async def callback(self, i):
        k=self.values[0]; harga=HARGA_VISEND[k]
        e=discord.Embed(title="⚡ VISEND DIPILIH!", description=f"**Kamu pilih:** {k.replace('_ecer',' Eceran')} Robux\n**Harga:** **{format_rupiah(harga)}**\n\nTransfer ke QRIS / DANA **{DANA_NOMOR}**!", color=discord.Color.from_rgb(255,193,7)); e.set_image(url=QRIS_URL)
        await i.response.send_message(embed=e)
class VisendView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(VisendSelect())
class TicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="Robux Vilog", style=discord.ButtonStyle.blurple, custom_id="ticket_vilog", emoji="🎫")
    async def vilog(self, i, b): await i.response.send_modal(VilogModal())
    @discord.ui.button(label="Acc 8 Bit", style=discord.ButtonStyle.green, custom_id="ticket_8bit", emoji="🌟")
    async def bit8(self, i, b): await i.response.send_modal(Bit8Modal())
    @discord.ui.button(label="Roblox Plus", style=discord.ButtonStyle.grey, custom_id="ticket_plus", emoji="✨")
    async def plus(self, i, b): await i.response.send_modal(PlusModal())
    @discord.ui.button(label="BELI AKUN", style=discord.ButtonStyle.grey, custom_id="ticket_akun", emoji="🛒")
    async def akun(self, i, b): await i.response.send_modal(AkunModal())
    @discord.ui.button(label="VISEND / FAST SEND", style=discord.ButtonStyle.red, custom_id="ticket_visend", emoji="⚡")
    async def visend(self, i, b): await i.response.send_modal(VisendModal())
@bot.tree.command(name="ticket", description="Kirim panel ticket 5 in 1")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_slash(interaction):
    e=discord.Embed(title="🎀 WELCOME TO MIPI STORE 🎀", description="Mau order apa? Klik tombol!\n\n🎫 Vilog | 🌟 8 Bit | ✨ Plus | 🛒 Beli Akun | ⚡ Visend\n\nPembayaran: QRIS / DANA", color=discord.Color.from_rgb(255,158,187)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e, view=TicketView())
@bot.tree.command(name="ticketpanel", description="Kirim panel ticket ke channel (Admin only) - kaya 1ST MARKET")
@app_commands.checks.has_permissions(administrator=True)
async def ticketpanel_cmd(interaction):
    e=discord.Embed(title="🎀 WELCOME TO MIPI STORE 🎀", description="HALLO KAKK! Selamat datang di Mipi Store!\n\nMau order apa? Klik tombol di bawah!\n\n🎫 **Robux Vilog** - Via Login\n🌟 **Acc 8 Bit** - Cuma Username + Paket!\n✨ **Roblox Plus**\n🛒 **Beli Akun**\n⚡ **Visend / Fast Send** - Cuma Username + Nickname!\n\nPembayaran: QRIS / DANA **0895-2642-4213**\nAdmin fast respon!", color=discord.Color.from_rgb(255,158,187)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e, view=TicketView())

# ========== 3. PRICELIST + PRICELISTNITRO + EDITPRICELIST ==========
class PricelistSelect(Select):
    def __init__(self):
        super().__init__(placeholder="Pilih Kategori", options=[discord.SelectOption(label="Robux Send", emoji="📤"), discord.SelectOption(label="Robux Vilog", emoji="📦"), discord.SelectOption(label="Roblox Pluss", emoji="⭐")], custom_id="pricelist_select")
    async def callback(self, i):
        p=self.values[0]
        if p=="Robux Send": e=discord.Embed(title="📤 ROBUX SEND", description="• 100 R$ : Rp 16.000\n• 500 R$ : Rp 75.000\n• 1000 R$ : Rp 150.000", color=discord.Color.from_rgb(88,101,242))
        elif p=="Robux Vilog": e=discord.Embed(title="📦 ROBUX VILOG", description="• 500 R$ : Rp 77.500\n• 1000 R$ : Rp 155.000\n• 2000 R$ : Rp 310.000\n• 5000 R$ : Rp 775.000", color=discord.Color.from_rgb(88,101,242))
        else: e=discord.Embed(title="⭐ ROBLOX PLUSS", description="• 1 Bulan : Rp 120.000\n• 3 Bulan : Rp 255.000\n• 12 Bulan : Rp 995.000", color=discord.Color.from_rgb(88,101,242))
        await i.response.send_message(embed=e, ephemeral=True)
class PricelistView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(PricelistSelect())
@bot.tree.command(name="pricelist", description="Tampilkan daftar harga produk resmi MIPI WORLD")
@app_commands.checks.has_permissions(administrator=True)
async def pricelist_slash(interaction):
    e=discord.Embed(title="📋 DAFTAR HARGA - MIPI WORLD", description="Pilih kategori di bawah!", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e, view=PricelistView())
@bot.tree.command(name="pricelistnitro", description="Tampilkan daftar harga produk Nitro & Discord Boost")
async def pricelistnitro_cmd(interaction):
    teks="\n".join([f"• **{k.replace('_',' ').title()}** : {format_rupiah(v)}" for k,v in HARGA_NITRO.items()])
    e=discord.Embed(title="💎 PRICELIST NITRO & BOOST - MIPI WORLD", description=teks+"\n\n**Pembayaran:** QRIS / DANA **0895-2642-4213**\nOrder di #open-ticket-dll!", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)
@bot.tree.command(name="editpricelist", description="Studio ubah nominal harga produk Robux")
@app_commands.checks.has_permissions(administrator=True)
async def editpricelist_cmd(interaction, jumlah: str, harga_baru: int):
    # Bisa edit Visend + Nitro sekaligus, kaya 1ST MARKET!
    if jumlah in HARGA_VISEND:
        lama=HARGA_VISEND[jumlah]; HARGA_VISEND[jumlah]=harga_baru; save_json("harga_visend.json", HARGA_VISEND)
        await interaction.response.send_message(f"✅ **Visend {jumlah} Robux:** {format_rupiah(lama)} ➜ **{format_rupiah(harga_baru)}**")
    elif jumlah in HARGA_NITRO:
        lama=HARGA_NITRO[jumlah]; HARGA_NITRO[jumlah]=harga_baru; save_json("harga_nitro.json", HARGA_NITRO)
        await interaction.response.send_message(f"✅ **Nitro {jumlah}:** {format_rupiah(lama)} ➜ **{format_rupiah(harga_baru)}**")
    else:
        await interaction.response.send_message(f"❌ Ga ada! Visend: {', '.join(HARGA_VISEND.keys())}\nNitro: {', '.join(HARGA_NITRO.keys())}", ephemeral=True)
@bot.tree.command(name="sethargavisend", description="Ganti harga Visend dari DC! Permanen!")
@app_commands.checks.has_permissions(administrator=True)
async def setharga_visend(interaction, jumlah: str, harga_baru: int):
    if jumlah not in HARGA_VISEND: await interaction.response.send_message(f"❌ Ga ada! {', '.join(HARGA_VISEND.keys())}", ephemeral=True); return
    lama=HARGA_VISEND[jumlah]; HARGA_VISEND[jumlah]=harga_baru; save_json("harga_visend.json", HARGA_VISEND)
    await interaction.response.send_message(f"✅ **{jumlah} Robux:** {format_rupiah(lama)} ➜ **{format_rupiah(harga_baru)}**")
@bot.tree.command(name="cekhargavisend", description="Lihat harga Visend")
async def cekharga_visend(interaction):
    daftar="\n".join([f"• **{k.replace('_ecer',' Eceran')} Robux** : {format_rupiah(v)}" for k,v in HARGA_VISEND.items()])
    await interaction.response.send_message(embed=discord.Embed(title="⚡ HARGA VISEND", description=daftar, color=discord.Color.from_rgb(255,193,7)), ephemeral=True)

# ========== 4. PAY ==========
class PayView(View):
    def __init__(self, nominal=0, catatan=""): super().__init__(timeout=None); self.nominal=nominal; self.catatan=catatan
    @discord.ui.button(label="✅ Saya Sudah Bayar", style=discord.ButtonStyle.green, emoji="💰", custom_id="sudah_bayar")
    async def sudah(self, i, b): await i.response.send_message(f"✅ **{i.user.mention} mengaku sudah bayar!**\n**Nominal:** {format_rupiah(self.nominal) if self.nominal else '-'}\n**Catatan:** {self.catatan}\n\nStaff tolong dicek! 📸", ephemeral=False)
    @discord.ui.button(label="📸 Kirim Bukti TF", style=discord.ButtonStyle.blurple, emoji="📸", custom_id="kirim_bukti")
    async def bukti(self, i, b): await i.response.send_message(f"{i.user.mention} silakan kirim foto bukti transfer di sini ya!", ephemeral=True)
@bot.tree.command(name="pay", description="Kirim instruksi pembayaran QRIS & rekening DANA")
@app_commands.describe(nominal="Nominal, contoh: 75000", catatan="Catatan, contoh: 500 Robux Visend", user="Tag buyer (opsional)")
async def pay_cmd(interaction, nominal: int = None, catatan: str = None, user: discord.Member = None):
    target=user or interaction.user; nominal_text=format_rupiah(nominal) if nominal else "Sesuai nominal order kamu"
    e=discord.Embed(title="💰 PEMBAYARAN - MIPI WORLD", description=f"Halo {target.mention}!\n\n**💳 Total:** # **{nominal_text}**\n**📝 Catatan:** {catatan or '-'}", color=discord.Color.from_rgb(255,193,7))
    e.add_field(name="📱 1. QRIS", value="Nama: Rafi Store\nNMID: ID1026603621750", inline=False)
    e.add_field(name="💙 2. DANA", value=f"Nomor: **{DANA_NOMOR}**\nAtas Nama: {DANA_NAMA}", inline=False)
    e.add_field(name="⚠️ CARA BAYAR:", value="1. Pilih QRIS / DANA\n2. Transfer sesuai nominal\n3. Screenshot bukti\n4. Kirim bukti + klik ✅ Saya Sudah Bayar", inline=False)
    e.set_image(url=QRIS_URL); e.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=e, view=PayView(nominal or 0, catatan or "-"))
@bot.tree.command(name="paypanel", description="Kirim panel Pay permanen")
@app_commands.checks.has_permissions(administrator=True)
async def paypanel_cmd(interaction):
    e=discord.Embed(title="💰 CARA BAYAR", description=f"QRIS / DANA **{DANA_NOMOR}** a.n Rafi Store", color=discord.Color.from_rgb(255,193,7)); e.set_image(url=QRIS_URL)
    await interaction.response.send_message(embed=e)

# ========== 5. RULES + ANNOUNCEMENT + OPERATIONAL + STATUS ==========
@bot.tree.command(name="rules", description="Tampilkan aturan dan ketentuan transaksi MIPI WORLD")
async def rules_cmd(interaction):
    e=discord.Embed(title="📜 RULES - MIPI WORLD", description="**1.** Order hanya di ticket resmi, jangan DM sembarangan!\n**2.** Bayar dulu baru diproses, kirim bukti TF asli!\n**3.** No Refund kalo Robux udah masuk / akun udah dikasih!\n**4.** Dilarang spam, toxic, dan scam! Auto ban!\n**5.** Kalo ada yang ngaku Staff di DM, cek role nya dulu!\n**6.** Garansi: Kalo order gagal karena kami, 100% refund / ganti baru!\n\n**Pembayaran Resmi Hanya:**\nQRIS Rafi Store & DANA **0895-2642-4213**\nSelain itu = PENIPU!", color=discord.Color.red()); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)
class AnnouncementModal(Modal, title="Buat Announcement Baru"):
    judul=TextInput(label="Judul Pengumuman", placeholder="Contoh: PROMO 500 ROBUX!", required=True)
    isi=TextInput(label="Isi Pengumuman", placeholder="Tulis pengumuman...", required=True, style=discord.TextStyle.paragraph)
    ping=TextInput(label="Ping? (everyone / here / kosong)", placeholder="everyone", required=False)
    async def on_submit(self, interaction):
        ch=discord.utils.get(interaction.guild.text_channels, name="📢┃𝖯𝖾𝗇𝗀𝗎𝗆𝗎𝗆𝖺𝗇") or interaction.channel
        e=discord.Embed(title=f"📢 {self.judul.value}", description=self.isi.value, color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI); e.set_footer(text=f"Dari {interaction.user.display_name} | {datetime.now().strftime('%d %B %Y')}")
        ping_txt=""
        if self.ping.value.lower()=="everyone": ping_txt="@everyone"
        elif self.ping.value.lower()=="here": ping_txt="@here"
        await ch.send(content=ping_txt, embed=e)
        await interaction.response.send_message(f"✅ Announcement terkirim ke {ch.mention}!", ephemeral=True)
@bot.tree.command(name="announcement", description="Buka panel studio pengumuman toko resmi MIPI WORLD")
@app_commands.checks.has_permissions(administrator=True)
async def announcement_cmd(interaction):
    await interaction.response.send_modal(AnnouncementModal())
@bot.tree.command(name="operational", description="Kirim panel jam operasional toko & support")
async def operational_cmd(interaction):
    status="🟢 **BUKA**" if CONFIG.get("toko_buka") else "🔴 **TUTUP**"
    e=discord.Embed(title="🕐 JAM OPERASIONAL - MIPI WORLD", description=f"**Status Sekarang:** {status}\n\n**Jam Buka:** {CONFIG.get('jam_buka')} - {CONFIG.get('jam_tutup')} WIB\n**Support:** Fast Respon 08:00 - 23:00 WIB\n**Order di luar jam:** Tetep bisa order, diproses besok pagi!\n\n**Pembayaran:** QRIS / DANA 24 Jam!", color=discord.Color.green()); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)
@bot.tree.command(name="statusopen", description="Ubah status toko menjadi BUKA (OPEN)")
@app_commands.checks.has_permissions(administrator=True)
async def statusopen_cmd(interaction):
    CONFIG["toko_buka"]=True; save_config()
    await interaction.response.send_message("🟢 **TOKO DIBUKA!** Semua ticket bisa order lagi! @everyone")
    try: await bot.change_presence(activity=discord.Game(name="🟢 MIPI STORE OPEN | /ticket"))
    except: pass
@bot.tree.command(name="statusclose", description="Ubah status toko menjadi TUTUP (CLOSE)")
@app_commands.checks.has_permissions(administrator=True)
async def statusclose_cmd(interaction, alasan: str = "Istirahat dulu!"):
    CONFIG["toko_buka"]=False; save_config()
    await interaction.response.send_message(f"🔴 **TOKO DITUTUP!**\n**Alasan:** {alasan}\nTicket sementara ditutup, buka lagi besok ya! 🙏")
    try: await bot.change_presence(activity=discord.Game(name="🔴 MIPI STORE CLOSE"))
    except: pass
@bot.tree.command(name="statusinfo", description="Lihat info jadwal otomatis toko saat ini")
async def statusinfo_cmd(interaction):
    status="🟢 BUKA" if CONFIG.get("toko_buka") else "🔴 TUTUP"
    e=discord.Embed(title="📊 STATUS TOKO", description=f"**Status:** {status}\n**Jam:** {CONFIG.get('jam_buka')} - {CONFIG.get('jam_tutup')} WIB\n**Antispam:** {'ON' if CONFIG.get('antispam') else 'OFF'} (Timeout {CONFIG.get('antispam_timeout')} detik)\n**Total Order:** {sum([v['total_order'] for v in ORDERS.values()])}x\n**Total Vouch:** {len(VOUCH_DATA)}", color=discord.Color.from_rgb(88,101,242))
    await interaction.response.send_message(embed=e, ephemeral=True)
@bot.tree.command(name="statusstore", description="Kirim panel status toko live (Components)")
@app_commands.checks.has_permissions(administrator=True)
async def statusstore_cmd(interaction):
    status="🟢 **TOKO BUKA - ORDER GAS!**" if CONFIG.get("toko_buka") else "🔴 **TOKO TUTUP - ISTIRAHAT!**"
    e=discord.Embed(title="🏪 STATUS TOKO - MIPI WORLD", description=f"{status}\n\nJam: {CONFIG.get('jam_buka')} - {CONFIG.get('jam_tutup')} WIB\n\nKlik `/statusinfo` buat detail!", color=discord.Color.green() if CONFIG.get("toko_buka") else discord.Color.red()); e.set_image(url=BANNER_MIPI)
    msg=await interaction.response.send_message(embed=e)
    CONFIG["status_msg_id"]=msg.message_id if hasattr(msg,'message_id') else None; save_config()

# ========== 6. LEADERBOARD (TOP PEMBELI) ==========
def buat_embed_top(guild):
    if not ORDERS: return discord.Embed(title="🏆 TOP PEMBELI - MIPI WORLD", description="Belum ada yang order! Jadilah yang pertama! 🎀", color=discord.Color.gold())
    sorted_top=sorted(ORDERS.items(), key=lambda x: x[1]["total_rupiah"], reverse=True)[:10]
    teks=""; medal=["🥇","🥈","🥉","4.","5.","6.","7.","8.","9.","10."]
    for i,(uid,data) in enumerate(sorted_top):
        m=guild.get_member(int(uid)); nama=m.mention if m else f"<@{uid}>"
        teks+=f"{medal[i]} {nama} - **{data['total_order']}x** | {data['total_robux']} Robux | {format_rupiah(data['total_rupiah'])}\n"
    e=discord.Embed(title="🏆 TOP SPENDER - MIPI WORLD", description=teks, color=discord.Color.gold()); e.set_image(url=BANNER_MIPI); e.set_footer(text="Live Leaderboard - Auto update tiap ada order!")
    return e
class LeaderboardView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.green, emoji="🏆", custom_id="refresh_leaderboard")
    async def refresh(self, i, b): await i.response.send_message(embed=buat_embed_top(i.guild), ephemeral=True)
@bot.tree.command(name="leaderboardpanel", description="Kirim panel leaderboard live ke channel (Admin)")
@app_commands.checks.has_permissions(administrator=True)
async def leaderboardpanel_cmd(interaction):
    msg=await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=LeaderboardView())
    CONFIG["leaderboard_channel_id"]=interaction.channel.id; save_config()
@bot.tree.command(name="leaderboardrefresh", description="Perbarui pesan live panel leaderboard sekarang")
@app_commands.checks.has_permissions(administrator=True)
async def leaderboardrefresh_cmd(interaction):
    await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=LeaderboardView())
@bot.tree.command(name="leaderboardview", description="Lihat peringkat Top Spender pelanggan saat ini")
async def leaderboardview_cmd(interaction):
    await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=LeaderboardView())
@bot.tree.command(name="toppembeli", description="Lihat Top Pembeli")
async def toppembeli_cmd(interaction): await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=LeaderboardView())
@bot.tree.command(name="paneltoppembeli", description="Kirim panel Top Pembeli")
@app_commands.checks.has_permissions(administrator=True)
async def paneltoppembeli(interaction): await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=LeaderboardView())
@bot.tree.command(name="tambahorder", description="Staff: Tambah order ke Top Pembeli")
@app_commands.checks.has_permissions(administrator=True)
async def tambahorder_cmd(interaction, user: discord.Member, robux: int, rupiah: int):
    tambah_order(user.id, robux, rupiah); await interaction.response.send_message(f"✅ {user.mention} +{robux} Robux | {format_rupiah(rupiah)}")

# ========== 7. ADDEMOJI + CLOSEEMOJI - EMOJI GERAK NITRO! ==========
# Sesi penambahan emoji: /addemoji -> bot nunggu kamu kirim gambar/gif, terus /closeemoji buat tutup sesi!
@bot.tree.command(name="addemoji", description="Cari dan pasang custom emoji ke server (bisa GIF gerak / Nitro!)")
@app_commands.describe(nama="Nama emoji, contoh: fire", link="Link gambar / GIF langsung, kosongin kalo mau upload manual", animated="True kalo GIF gerak, False kalo gambar diam")
@app_commands.checks.has_permissions(administrator=True)
async def addemoji_cmd(interaction, nama: str, link: str = None, animated: bool = False):
    # Cara 1: Pake link langsung
    if link:
        await interaction.response.defer(ephemeral=True)
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(link) as r:
                    if r.status!=200: await interaction.followup.send("❌ Link gambar ga bisa diakses!"); return
                    data=await r.read()
            emoji=await interaction.guild.create_custom_emoji(name=nama, image=data, reason=f"Add emoji by {interaction.user}")
            tipe="**ANIMATED / GERAK** <a:gerak:123>" if animated or link.endswith(".gif") else "**DIAM**"
            await interaction.followup.send(f"✅ **Emoji berhasil ditambah!**\n\n**Nama:** `{nama}`\n**Tipe:** {tipe}\n**Emoji:** {emoji}\n**Cara pake:** Ketik `:{nama}:` di chat!\n\n> 💡 Kalo GIF, otomatis jadi emoji gerak! Member Nitro bisa pake di semua server!")
            return
        except Exception as e:
            await interaction.followup.send(f"❌ Gagal: {e}\nPastikan bot punya izin Manage Emojis & file < 256KB (kalo GIF < 512KB)!")
            return
    # Cara 2: Mode sesi - bot nunggu kamu upload gambar
    CONFIG["emoji_session"]=str(interaction.user.id); save_config()
    await interaction.response.send_message(f"📤 **SESI ADDEMOJI DIBUKA!**\n\nKamu mau nambah emoji apa?\n\n**Cara:**\n1. Kirim gambar / GIF nya di channel ini (drag & drop aja!)\n2. Bot langsung tanya nama nya!\n3. Ketik `/closeemoji` kalo udah selesai!\n\n> 💡 Kirim file `.gif` biar jadi emoji gerak / Nitro!", ephemeral=True)
@bot.tree.command(name="closeemoji", description="Tutup sesi penambahan emoji dan bersihkan sesi")
@app_commands.checks.has_permissions(administrator=True)
async def closeemoji_cmd(interaction):
    CONFIG["emoji_session"]=None; save_config()
    await interaction.response.send_message("✅ **Sesi Add Emoji DITUTUP!**\nSemua emoji yang udah ditambah udah tersimpan di server! 🎉", ephemeral=True)
@bot.event
async def on_message(message):
    if message.author.bot: return
    # --- ADDEMOJI SESI: Kalo ada yang kirim gambar pas sesi aktif ---
    if CONFIG.get("emoji_session")==str(message.author.id) and message.attachments:
        try:
            att=message.attachments[0]
            data=await att.read()
            nama=att.filename.split(".")[0].lower().replace(" ","_")[:32]
            emoji=await message.guild.create_custom_emoji(name=nama, image=data, reason=f"Add emoji sesi by {message.author}")
            is_gif=att.filename.lower().endswith(".gif")
            await message.reply(f"✅ **Emoji ditambah!** {emoji} `:{nama}:`\nTipe: {'**GERAK / ANIMATED** 🔥' if is_gif else '**DIAM**'}\nKirim gambar lagi buat nambah, atau `/closeemoji` buat selesai!")
        except Exception as e:
            await message.reply(f"❌ Gagal tambah emoji: {e}")
        return
    # --- ANTISPAM ---
    if CONFIG.get("antispam") and not message.author.guild_permissions.administrator:
        now=time.time()
        key=message.author.id
        SPAM_TRACK[key].append(now)
        # Hapus yang udah > 10 detik
        while SPAM_TRACK[key] and now - SPAM_TRACK[key][0] > 10:
            SPAM_TRACK[key].popleft()
        if len(SPAM_TRACK[key]) >= 6: # 6 pesan dalam 10 detik = spam!
            try:
                await message.delete()
                await message.author.timeout(timedelta(seconds=CONFIG.get("antispam_timeout",60)), reason="Antispam MIPI WORLD")
                await message.channel.send(f"⚠️ {message.author.mention} kena **timeout {CONFIG.get('antispam_timeout')} detik** karena spam! Jangan spam ya!", delete_after=10)
                SPAM_TRACK[key].clear()
            except: pass
            return
    # --- TESTIMONI OTOMATIS: !testimoni ---
    if message.channel.name.startswith("🎫") and message.attachments and message.content.lower().startswith("!testimoni"):
        foto=message.attachments[0].url
        buyer=message.mentions[0] if message.mentions else message.author
        parts=message.content.split()
        jumlah=" ".join(parts[2:4]) if len(parts)>=4 else "500 Robux"
        nomor=await kirim_vouch_testimoni(message.guild, buyer, "Visend", jumlah, foto, message.author, "Robux udah masuk! Makasih udah order! 🎀")
        await message.reply(f"✅ **Otomatis jadi Testimoni #{nomor}!** Udah ke-post ke Testimoni + Vouch!")
    await bot.process_commands(message)

# ========== 8. ANTISPAM COMMANDS ==========
@bot.tree.command(name="antispamstatus", description="Lihat status & parameter proteksi Anti-Spam")
async def antispamstatus_cmd(interaction):
    e=discord.Embed(title="🛡️ ANTI-SPAM STATUS", description=f"**Status:** {'🟢 AKTIF' if CONFIG.get('antispam') else '🔴 NONAKTIF'}\n**Timeout:** {CONFIG.get('antispam_timeout')} detik\n**Trigger:** 6 pesan dalam 10 detik = Auto Timeout\n**Yang kebal:** Admin / Owner", color=discord.Color.green() if CONFIG.get("antispam") else discord.Color.red())
    await interaction.response.send_message(embed=e, ephemeral=True)
@bot.tree.command(name="antispamtimeout", description="Atur durasi sanksi timeout otomatis")
@app_commands.checks.has_permissions(administrator=True)
async def antispamtimeout_cmd(interaction, detik: int):
    CONFIG["antispam_timeout"]=detik; save_config()
    await interaction.response.send_message(f"✅ **Timeout Antispam diubah jadi {detik} detik!**")
@bot.tree.command(name="antispamtoggle", description="Aktifkan atau nonaktifkan sistem Anti-Spam")
@app_commands.checks.has_permissions(administrator=True)
async def antispamtoggle_cmd(interaction):
    CONFIG["antispam"]=not CONFIG.get("antispam", True); save_config()
    await interaction.response.send_message(f"✅ **Antispam sekarang:** {'🟢 AKTIF' if CONFIG['antispam'] else '🔴 NONAKTIF'}")
@bot.tree.command(name="antispamuntimeout", description="Cabut sanksi timeout member jika false positive")
@app_commands.checks.has_permissions(administrator=True)
async def antispamuntimeout_cmd(interaction, user: discord.Member):
    try:
        await user.timeout(None, reason="Untimeout by Admin")
        await interaction.response.send_message(f"✅ **{user.mention} timeout nya udah dicabut!**")
    except Exception as e:
        await interaction.response.send_message(f"❌ Gagal: {e}")

# ========== 9. AFK - BOT STANDBY DI VOICE 24 JAM ==========
@bot.tree.command(name="afk", description="Kontrol dan atur bot standby AFK Voice 24 Jam")
@app_commands.describe(aksi="join / leave", channel="Pilih Voice Channel AFK")
@app_commands.checks.has_permissions(administrator=True)
async def afk_cmd(interaction, aksi: str, channel: discord.VoiceChannel = None):
    global AFK_VC
    if aksi.lower()=="join":
        vc_channel=channel or discord.utils.get(interaction.guild.voice_channels, name="💤┃𝖠𝖿𝗄") or discord.utils.get(interaction.guild.voice_channels, name="🔈〢Voice・𝖯𝗎𝖻𝗅𝗂𝗄")
        if not vc_channel: await interaction.response.send_message("❌ Voice Channel AFK ga ketemu!"); return
        try:
            if interaction.guild.voice_client: await interaction.guild.voice_client.disconnect()
            AFK_VC=await vc_channel.connect()
            CONFIG["afk_channel_id"]=vc_channel.id; save_config()
            await interaction.response.send_message(f"✅ **Bot AFK standby di {vc_channel.mention}!**\nBot bakal stay 24 Jam di sini, biar server keliatan rame & member betah! 🎧\nKetik `/afk aksi:leave` buat keluarin bot!")
            # Loop biar bot ga ke-disconnect: cek tiap 60 detik, kalo ke-disconnect, join lagi!
            async def afk_loop():
                while True:
                    await asyncio.sleep(60)
                    try:
                        if not interaction.guild.voice_client or not interaction.guild.voice_client.is_connected():
                            await vc_channel.connect()
                    except: pass
            bot.loop.create_task(afk_loop())
        except Exception as e:
            await interaction.response.send_message(f"❌ Gagal join VC: {e}")
    elif aksi.lower()=="leave":
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.disconnect()
            CONFIG["afk_channel_id"]=None; save_config()
            await interaction.response.send_message("✅ **Bot udah keluar dari AFK Voice!**")
        else:
            await interaction.response.send_message("Bot lagi ga di VC!")
    else:
        await interaction.response.send_message("Pake `aksi:join` atau `aksi:leave` ya!")

# ========== 10. CEK AVATAR + CEK RBX + GAMEPASS ==========
async def get_roblox_id(username):
    async with aiohttp.ClientSession() as s:
        async with s.post("https://users.roblox.com/v1/usernames/users", json={"usernames":[username]}) as r:
            d=await r.json(); return d["data"][0]["id"] if d.get("data") else None
@bot.tree.command(name="cekavatar", description="Cek avatar Roblox lengkap")
async def cekavatar_cmd(interaction, username: str):
    await interaction.response.defer()
    uid=await get_roblox_id(username)
    if not uid: await interaction.followup.send(f"❌ `{username}` ga ketemu!"); return
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://users.roblox.com/v1/users/{uid}") as r: profil=await r.json()
        async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=720x720&format=Png&isCircular=false") as r: full=(await r.json())["data"][0]["imageUrl"]
        async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false") as r: head=(await r.json())["data"][0]["imageUrl"]
    e=discord.Embed(title=f"🖼️ AVATAR • {profil['name']}", description=f"Display: {profil['displayName']} | ID: `{uid}`", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=full); e.set_thumbnail(url=head)
    await interaction.followup.send(embed=e)
@bot.tree.command(name="cekrbx", description="Cek Robux seseorang")
async def cekrbx_cmd(interaction, username: str):
    await interaction.response.defer()
    uid=await get_roblox_id(username)
    if not uid: await interaction.followup.send(f"❌ `{username}` ga ketemu!"); return
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://economy.roblox.com/v1/users/{uid}/currency") as r: cur=await r.json() if r.status==200 else {"robux":0}
    await interaction.followup.send(embed=discord.Embed(title=f"💰 CEK RBX • {username}", description=f"**Robux:** **{cur.get('robux',0)} Robux**", color=discord.Color.gold()))
@bot.tree.command(name="panelcekavatar", description="Kirim panel Cek Avatar")
@app_commands.checks.has_permissions(administrator=True)
async def panelcekavatar(interaction):
    await interaction.response.send_message(embed=discord.Embed(title="🔍 CEK AVATAR", description="Ketik `/cekavatar username:UsernameRoblox`", color=discord.Color.from_rgb(88,101,242)))
@bot.tree.command(name="panelcekrbx", description="Kirim panel Cek Rbx")
@app_commands.checks.has_permissions(administrator=True)
async def panelcekrbx(interaction):
    await interaction.response.send_message(embed=discord.Embed(title="💰 CEK RBX", description="Ketik `/cekrbx username:UsernameRoblox`", color=discord.Color.gold()))
def ambil_id_gamepass(t):
    a=re.findall(r"\d+", t); return a[0] if a else None
@bot.tree.command(name="cekgamepass", description="Cek Gamepass")
async def cekgamepass_cmd(interaction, gamepass: str):
    await interaction.response.defer()
    gid=ambil_id_gamepass(gamepass)
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://apis.roblox.com/game-passes/v1/game-passes/{gid}") as r:
            if r.status!=200: await interaction.followup.send("❌ Gamepass ga ketemu!"); return
            d=await r.json()
    await interaction.followup.send(embed=discord.Embed(title=f"🎟️ GAMEPASS • {d['name']}", description=f"**Harga:** {d.get('price') or 'GRATIS'} Robux\n**Status:** {'✅ ON SALE' if d.get('isForSale') else '❌ OFF SALE'}", color=discord.Color.from_rgb(88,101,242)))
@bot.tree.command(name="cekpending", description="Cek estimasi Pending")
async def cekpending_cmd(interaction, gamepass: str, tanggal_beli: str = None):
    await interaction.response.defer()
    gid=ambil_id_gamepass(gamepass)
    try: tgl=datetime.now() if not tanggal_beli or tanggal_beli.lower() in ["hari ini","today"] else datetime.strptime(tanggal_beli, "%Y-%m-%d")
    except: await interaction.followup.send("❌ Format: YYYY-MM-DD"); return
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://apis.roblox.com/game-passes/v1/game-passes/{gid}") as r:
            if r.status!=200: await interaction.followup.send("❌ Gamepass ga ketemu!"); return
            d=await r.json()
    harga=d.get("price") or 0; diterima=int(harga*0.7); cair=tgl+timedelta(days=3); cair2=tgl+timedelta(days=7)
    await interaction.followup.send(embed=discord.Embed(title=f"⏳ PENDING • {d['name']}", description=f"**Harga:** {harga} Robux\n**Masuk (70%):** {diterima} Robux\n**Cair:** {cair.strftime('%d %B %Y')} - {cair2.strftime('%d %B %Y')}", color=discord.Color.orange()))

# ========== 11. CEK SALDO + ORDER STATUS + REKBER + GIVEAWAY + VOUCH ==========
@bot.tree.command(name="ceksaldo", description="Cek saldo kamu / orang lain")
async def ceksaldo_cmd(interaction, user: discord.Member = None):
    target=user or interaction.user; saldo=SALDO.get(str(target.id),0); order=ORDERS.get(str(target.id), {"total_order":0,"total_robux":0,"total_rupiah":0})
    e=discord.Embed(title=f"💳 SALDO • {target.display_name}", description=f"**Saldo:** **{format_rupiah(saldo)}**\n**Total Order:** {order['total_order']}x\n**Total Robux:** {order['total_robux']} Robux", color=discord.Color.green()); e.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=e, ephemeral=(user is None))
@bot.tree.command(name="tambahsaldo", description="Staff: Tambah saldo buyer")
@app_commands.checks.has_permissions(administrator=True)
async def tambahsaldo_cmd(interaction, user: discord.Member, jumlah: int):
    SALDO[str(user.id)]=SALDO.get(str(user.id),0)+jumlah; save_json("saldo.json", SALDO)
    await interaction.response.send_message(f"✅ Saldo {user.mention} +{format_rupiah(jumlah)}")
@bot.tree.command(name="panelceksaldo", description="Kirim panel Cek Saldo")
@app_commands.checks.has_permissions(administrator=True)
async def panelceksaldo(interaction):
    await interaction.response.send_message(embed=discord.Embed(title="💳 CEK SALDO", description="Ketik `/ceksaldo`", color=discord.Color.green()))
@bot.tree.command(name="cekorder", description="Cek status order kamu")
async def cekorder_cmd(interaction):
    order=ORDERS.get(str(interaction.user.id))
    if not order: await interaction.response.send_message("❌ Belum pernah order!", ephemeral=True); return
    await interaction.response.send_message(embed=discord.Embed(title=f"📦 ORDER STATUS • {interaction.user.display_name}", description=f"**Total Order:** {order['total_order']}x\n**Total Robux:** {order['total_robux']} Robux\n**Total Belanja:** {format_rupiah(order['total_rupiah'])}", color=discord.Color.from_rgb(88,101,242)), ephemeral=True)
@bot.tree.command(name="panelorderstatus", description="Kirim panel Order Status")
@app_commands.checks.has_permissions(administrator=True)
async def panelorderstatus(interaction):
    await interaction.response.send_message(embed=discord.Embed(title="📦 ORDER STATUS", description="Order baru auto muncul di sini!\nKetik `/cekorder`", color=discord.Color.from_rgb(88,101,242)))
@bot.tree.command(name="updatestatus", description="Staff: Update status order")
@app_commands.checks.has_permissions(administrator=True)
async def updatestatus_cmd(interaction, user: discord.Member, status: str, keterangan: str = ""):
    await interaction.response.send_message(embed=discord.Embed(title=f"📦 UPDATE - {user.display_name}", description=f"**Pembeli:** {user.mention}\n**Status:** **{status}**\n**Ket:** {keterangan or '-'}", color=discord.Color.green()))
# Rekber
class RekberModal(Modal, title="Buat Rekber Baru"):
    penjual=TextInput(label="Username Penjual (@Tag)", placeholder="@Penjual", required=True)
    pembeli=TextInput(label="Username Pembeli (@Tag)", placeholder="@Pembeli", required=True)
    barang=TextInput(label="Barang Yang Direkberkan", placeholder="Contoh: Akun R6", required=True, style=discord.TextStyle.paragraph)
    harga=TextInput(label="Harga Rekber", placeholder="Contoh: Rp 200.000", required=True)
    pembayaran=TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, i):
        guild=i.guild; cat=discord.utils.get(guild.categories, name="⎯⎯⎯• Rekber Area")
        overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch=await guild.create_text_channel(f"🤝┃rekber-{i.user.name}", category=cat, overwrites=overwrites)
        e=discord.Embed(title="🤝 REKBER DIMULAI!", description=f"**Penjual:** {self.penjual.value}\n**Pembeli:** {self.pembeli.value}\n**Barang:** {self.barang.value}\n**Harga:** {self.harga.value}\n**Pembayaran:** {self.pembayaran.value}\n**Admin:** {i.user.mention}\n\n1. Pembeli TF ke Admin (QRIS / DANA {DANA_NOMOR})\n2. Penjual kirim barang ke Admin\n3. Admin cek & teruskan\n4. Selesai ✅", color=discord.Color.green())
        await ch.send(embed=e, view=RekberSelesaiView(penjual=self.penjual.value, pembeli=self.pembeli.value, barang=self.barang.value, harga=self.harga.value))
        await i.response.send_message(f"✅ Rekber: {ch.mention}", ephemeral=True)
class RekberSelesaiView(View):
    def __init__(self, penjual="", pembeli="", barang="", harga=""):
        super().__init__(timeout=None); self.penjual=penjual; self.pembeli=pembeli; self.barang=barang; self.harga=harga
    @discord.ui.button(label="✅ Rekber Selesai", style=discord.ButtonStyle.green, custom_id="rekber_selesai")
    async def selesai(self, i, b):
        REKBER_HISTORY.append({"penjual":self.penjual,"pembeli":self.pembeli,"barang":self.barang,"harga":self.harga,"tanggal":datetime.now().strftime("%d %B %Y %H:%M"),"admin":str(i.user)}); save_json("rekber_history.json", REKBER_HISTORY)
        hist_ch=discord.utils.get(i.guild.text_channels, name="📜┃𝖧𝗂𝗌𝗍𝗈𝗋𝗒・𝖱𝖾𝗄𝖻𝖾𝗋")
        if hist_ch: await hist_ch.send(embed=discord.Embed(title="✅ REKBER SELESAI!", description=f"**Penjual:** {self.penjual}\n**Pembeli:** {self.pembeli}\n**Barang:** {self.barang}\n**Harga:** {self.harga}\n**Admin:** {i.user.mention}", color=discord.Color.green()))
        await i.response.send_message("✅ Rekber SELESAI & masuk History! Tutup 10 detik..."); await asyncio.sleep(10); await i.channel.delete()
class RekberPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🤝 Buat Rekber Baru", style=discord.ButtonStyle.green, custom_id="buat_rekber", emoji="🤝")
    async def buat(self, i, b): await i.response.send_modal(RekberModal())
@bot.tree.command(name="rekberpanel", description="Kirim panel Rekber")
@app_commands.checks.has_permissions(administrator=True)
async def rekberpanel_cmd(interaction):
    e=discord.Embed(title="🤝 REKBER PANEL", description="Transaksi aman pake Rekber!\nKlik tombol di bawah!", color=discord.Color.green()); e.set_image(url=BANNER_MIPI); await interaction.response.send_message(embed=e, view=RekberPanelView())
@bot.tree.command(name="historyrekber", description="Lihat History Rekber")
async def historyrekber_cmd(interaction):
    if not REKBER_HISTORY: await interaction.response.send_message("Belum ada history!", ephemeral=True); return
    teks="".join([f"✅ **{h['barang']}** - {h['harga']} | {h['penjual']} ➜ {h['pembeli']} | {h['tanggal']}\n" for h in REKBER_HISTORY[-10:]])
    await interaction.response.send_message(embed=discord.Embed(title="📜 HISTORY REKBER
