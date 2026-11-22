import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button, Modal, TextInput
import asyncio
import aiohttp
import re
import os
import json
import random
from datetime import datetime, timedelta

# ========== SETTING UTAMA ==========
BANNER_MIPI = os.getenv("BANNER_MIPI", "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/56a25f63-21b9-56b4-851c-d5d1c6b25943.jpeg")
TOKEN = os.getenv("TOKEN")
QRIS_URL = "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/IMG_6533.jpeg"
BANNER_TICKET_URL = "https://raw.githubusercontent.com/1world97/MIPI-WORLD/main/56a25f63-21b9-56b4-851c-d5d1c6b25943.jpeg"
DANA_NOMOR = "0895-2642-4213"
DANA_NAMA = "Rafi Store"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ========== DATABASE ==========
def load_json(nama, default):
    if os.path.exists(nama):
        try:
            with open(nama, "r") as f: return json.load(f)
        except: return default
    return default
def save_json(nama, data):
    with open(nama, "w") as f: json.dump(data, f, indent=2)

HARGA_VISEND = load_json("harga_visend.json", {"500":75000,"1000":150000,"2000":300000,"3000":450000,"4000":600000,"5000":750000,"100_ecer":16000,"200_ecer":32000,"300_ecer":48000,"400_ecer":64000})
ORDERS = load_json("orders.json", {})
SALDO = load_json("saldo.json", {})
REKBER_HISTORY = load_json("rekber_history.json", [])
VOUCH_DATA = load_json("vouch.json", []) # List vouch
GIVEAWAYS = {}

def format_rupiah(n): return f"Rp {int(n):,}".replace(",", ".")
def simpan_harga(): save_json("harga_visend.json", HARGA_VISEND)
def tambah_order(user_id, robux, rupiah):
    u=str(user_id)
    if u not in ORDERS: ORDERS[u]={"total_order":0,"total_robux":0,"total_rupiah":0}
    ORDERS[u]["total_order"]+=1; ORDERS[u]["total_robux"]+=int(robux or 0); ORDERS[u]["total_rupiah"]+=int(rupiah or 0)
    save_json("orders.json", ORDERS)

# ========== ⭐ VOUCH & TESTIMONI - FUNGSI UTAMA ==========
async def kirim_vouch_testimoni(guild, buyer: discord.Member, produk: str, jumlah_robux: str, bukti_url: str, admin: discord.Member, pesan_buyer: str = ""):
    # Simpan ke database
    VOUCH_DATA.append({"buyer": str(buyer), "buyer_id": buyer.id, "produk": produk, "robux": jumlah_robux, "bukti": bukti_url, "tanggal": datetime.now().strftime("%d %B %Y %H:%M"), "admin": str(admin)})
    save_json("vouch.json", VOUCH_DATA)
    # Auto tambah ke Top Pembeli juga!
    try:
        angka = int(re.findall(r"\d+", jumlah_robux)[0]) if re.findall(r"\d+", jumlah_robux) else 0
        tambah_order(buyer.id, angka, 0)
    except: pass

    # Embed Testimoni - Yang ada gambarnya!
    e_testi = discord.Embed(title="⭐ TESTIMONI - ORDER BERHASIL! ⭐", description=f"**Pembeli:** {buyer.mention}\n**Produk:** {produk}\n**Jumlah:** **{jumlah_robux}**\n**Status:** ✅ **ROBUX UDAH MASUK!**\n**Admin:** {admin.mention}\n**Tanggal:** {datetime.now().strftime('%d %B %Y')}\n\n💬 *{pesan_buyer or 'Makasih udah order di MIPI STORE! Aman, Cepat, Terpercaya! 🎀'}*", color=discord.Color.from_rgb(255,158,187))
    if bukti_url: e_testi.set_image(url=bukti_url)
    e_testi.set_footer(text=f"MIPI WORLD • Testimoni #{len(VOUCH_DATA)} | Order di MIPI STORE, Dijamin Aman!")
    e_testi.set_thumbnail(url=buyer.display_avatar.url)

    # Embed Vouch - Versi pendek buat channel Vouch
    e_vouch = discord.Embed(title="✅ VOUCH - MIPI STORE TERPERCAYA!", description=f"**{buyer.mention}** udah order **{produk} - {jumlah_robux}**\n\n✅ **SUCCESS! Robux udah masuk!**\n⭐ Rating: ⭐⭐⭐⭐⭐ (5/5)\n🛒 Order lagi? Klik #open-ticket-dll!", color=discord.Color.green())
    if bukti_url: e_vouch.set_image(url=bukti_url)
    e_vouch.set_footer(text=f"Vouch #{len(VOUCH_DATA)} | MIPI WORLD")

    # Kirim ke 2 channel sekaligus!
    testi_ch = discord.utils.get(guild.text_channels, name="⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂")
    vouch_ch = discord.utils.get(guild.text_channels, name="💬┃𝖵𝗈𝗎𝖼𝗁")
    if testi_ch: await testi_ch.send(embed=e_testi)
    if vouch_ch: await vouch_ch.send(embed=e_vouch)
    return len(VOUCH_DATA)

# Modal pas klik "Jadikan Testimoni" di dalam Ticket
class TestimoniModal(Modal, title="Buat Testimoni - Robux Masuk!"):
    buyer_tag = TextInput(label="Tag Pembeli (@Username)", placeholder="@Username Pembeli", required=True)
    produk = TextInput(label="Produk Yang Dibeli", placeholder="Contoh: Visend / Vilog / 8 Bit", default="Visend", required=True)
    jumlah = TextInput(label="Jumlah Robux Yang Masuk", placeholder="Contoh: 500 Robux", required=True)
    link_bukti = TextInput(label="Link Foto Bukti Robux Masuk", placeholder="Paste link foto / ketik - kalo pake foto di bawah", required=False, style=discord.TextStyle.paragraph)
    pesan = TextInput(label="Pesan / Testimoni Buyer (Opsional)", placeholder="Contoh: Makasih kak, fast respon banget!", required=False, style=discord.TextStyle.paragraph)
    async def on_submit(self, interaction):
        # Cari buyer dari tag
        buyer = interaction.user
        try:
            # Coba cari member dari mention / nama
            nama = self.buyer_tag.value.replace("@","").replace("<","").replace(">","").replace("!","").strip()
            if nama.isdigit():
                buyer = interaction.guild.get_member(int(nama)) or buyer
            else:
                for m in interaction.guild.members:
                    if nama.lower() in m.name.lower() or nama.lower() in m.display_name.lower():
                        buyer = m; break
        except: pass
        bukti = self.link_bukti.value.strip() if self.link_bukti.value else ""
        # Kalo ada foto yang dilampirkan di pesan terakhir ticket, kita ambil? Untuk sekarang pake link
        nomor = await kirim_vouch_testimoni(interaction.guild, buyer, self.produk.value, self.jumlah.value, bukti, interaction.user, self.pesan.value)
        await interaction.response.send_message(f"✅ **TESTIMONI #{nomor} BERHASIL DIPOST!**\n\nUdah ke-post otomatis ke:\n⭐ #⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂\n💬 #💬┃𝖵𝗈𝗎𝖼𝗁\n\nBuyer juga otomatis masuk Top Pembeli! 🏆", ephemeral=True)

# View di dalam Ticket - Ada 2 tombol: Testimoni + Close
class TicketActionView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⭐ Jadikan Testimoni", style=discord.ButtonStyle.green, emoji="⭐", custom_id="jadi_testimoni")
    async def jadi_testi(self, interaction, button):
        await interaction.response.send_modal(TestimoniModal())
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction, button):
        await interaction.response.send_message("Ticket akan ditutup dalam 5 detik..."); await asyncio.sleep(5); await interaction.channel.delete()

# Biar tombol testimoni ga mati kalo bot restart
class CloseTicketView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="⭐ Jadikan Testimoni", style=discord.ButtonStyle.green, emoji="⭐", custom_id="jadi_testimoni")
    async def jadi_testi(self, interaction, button):
        await interaction.response.send_modal(TestimoniModal())
    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close(self, interaction, button):
        await interaction.response.send_message("Ticket ditutup dalam 5 detik..."); await asyncio.sleep(5); await interaction.channel.delete()

# ========== HELPER TICKET ==========
async def kirim_ticket_dari_form(interaction, jenis, judul, data_form):
    guild = interaction.guild
    cat = discord.utils.get(guild.categories, name="⎯⎯⎯• Mipi Store") or discord.utils.get(guild.categories, name="⎯⎯⎯• Ticket & Order")
    overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
    ch = await guild.create_text_channel(f"🎫┃{jenis}-{interaction.user.name}", category=cat, overwrites=overwrites)
    embed1 = discord.Embed(title=f"🎫  TICKET {judul} - MIPI WORLD", description=f"Halo {interaction.user.mention}!\n\nTicket kamu udah dibuat! Format udah terisi otomatis!", color=discord.Color.from_rgb(88,101,242))
    embed1.set_image(url=BANNER_TICKET_URL)
    await ch.send(embed=embed1)
    isi = ""
    for k,v in data_form.items():
        if "SANDI" in k.upper() or "PASSWORD" in k.upper(): isi += f"**{k}:** ||{v}||\n"
        else: isi += f"**{k}:** {v}\n"
    if jenis=="visend":
        for key,harga in HARGA_VISEND.items():
            if key.replace("_ecer","") in data_form.get("Paket yang dipilih",""):
                isi += f"\n**💰 Total Bayar:** **{format_rupiah(harga)}**\n"; break
    embed_form = discord.Embed(title="📝  FORMAT ORDER - UDAH TERISI!", description=isi, color=discord.Color.green())
    embed_form.set_footer(text=f"Order dari {interaction.user} | {datetime.now().strftime('%d %B %Y %H:%M')}")
    await ch.send(embed=embed_form)
    try:
        status_ch = discord.utils.get(guild.text_channels, name="📦┃𝖮𝗋𝖽𝖾𝗋・𝖲𝗍𝖺𝗍𝗎𝗌")
        if status_ch:
            e = discord.Embed(title="📦 ORDER BARU!", description=f"**Pembeli:** {interaction.user.mention}\n**Produk:** {judul}\n**Paket:** {data_form.get('Paket yang dipilih','-')}\n**Ticket:** {ch.mention}\n**Status:** ⏳ Diproses", color=discord.Color.orange())
            await status_ch.send(embed=e)
    except: pass
    embed3 = discord.Embed(title="💰  PEMBAYARAN - QRIS / DANA", description=f"**1. QRIS**\nNama: Rafi Store\nNMID: ID1026603621750\n\n**2. DANA**\nNomor: **{DANA_NOMOR}**\nAtas Nama: {DANA_NAMA}\n\n⚠️ Bayar sesuai nominal & kirim bukti di sini!", color=discord.Color.from_rgb(255,193,7))
    embed3.set_image(url=QRIS_URL)
    embed3.set_footer(text="MIPI WORLD • QRIS / DANA")
    await ch.send(embed=embed3)
    # Pesan Testimoni - Ingetin staff!
    await ch.send("⭐ **Staff:** Kalo Robux udah masuk, jangan lupa klik tombol **⭐ Jadikan Testimoni** di bawah, terus SS foto Robux masuk nya, langsung ke-post ke Testimoni + Vouch otomatis!", view=TicketActionView())
    return ch

# ========== MODAL TICKET ==========
class VilogModal(Modal, title="Pesanan Robux Vilog"):
    username = TextInput(label="Username Roblox", placeholder="UsernameRoblox", required=True)
    katasandi = TextInput(label="Kata Sandi Roblox", placeholder="Password (Rahasia!)", required=True)
    paket = TextInput(label="Paket yang dipilih", placeholder="Contoh: 1000 Robux", required=True)
    pembayaran = TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, interaction):
        data={"Nickname Roblox":interaction.user.display_name,"Username":self.username.value,"Kata Sandi":self.katasandi.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(interaction,"vilog","ROBUX VILOG",data)
        await interaction.response.send_message(f"✅ Ticket Vilog: {ch.mention}", ephemeral=True)
class VisendModal(Modal, title="Pesanan Robux Visend"):
    nickname = TextInput(label="Nickname Roblox", placeholder="Nickname kamu", required=True)
    username = TextInput(label="Username", placeholder="UsernameRoblox", required=True)
    paket = TextInput(label="Paket yang dipilih", placeholder="Contoh: 500 Robux", required=True)
    pembayaran = TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, interaction):
        data={"Nickname Roblox":self.nickname.value,"Username":self.username.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(interaction,"visend","VISEND",data)
        await interaction.response.send_message(f"✅ Ticket Visend: {ch.mention}", ephemeral=True)
class Bit8Modal(Modal, title="Pesanan Acc 8 Bit"):
    username = TextInput(label="Username Roblox", placeholder="UsernameRoblox kamu", required=True)
    paket = TextInput(label="Paket yang dipilih", placeholder="Contoh: Acc 8 Bit", required=True)
    pembayaran = TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, interaction):
        data={"Username":self.username.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(interaction,"8bit","ACC 8 BIT",data)
        await interaction.response.send_message(f"✅ Ticket 8 Bit: {ch.mention}", ephemeral=True)
class PlusModal(Modal, title="Pesanan Roblox Plus"):
    username = TextInput(label="Username Roblox", placeholder="UsernameRoblox", required=True)
    katasandi = TextInput(label="Kata Sandi Roblox", placeholder="Password (Rahasia!)", required=True)
    paket = TextInput(label="Paket Plus yang dipilih", placeholder="Contoh: 1 Bulan", required=True)
    pembayaran = TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, interaction):
        data={"Username":self.username.value,"Kata Sandi":self.katasandi.value,"Paket yang dipilih":self.paket.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(interaction,"plus","ROBLOX PLUS",data)
        await interaction.response.send_message(f"✅ Ticket Plus: {ch.mention}", ephemeral=True)
class AkunModal(Modal, title="Pesanan Beli Akun"):
    akun_dicari = TextInput(label="Akun Yang Dicari", placeholder="Contoh: Akun R6", required=True, style=discord.TextStyle.paragraph)
    budget = TextInput(label="Budget Kamu", placeholder="Contoh: Rp 200.000", required=True)
    username = TextInput(label="Username Roblox Kamu", placeholder="UsernameRoblox", required=True)
    pembayaran = TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, interaction):
        data={"Akun Yang Dicari":self.akun_dicari.value,"Budget":self.budget.value,"Username Pembeli":self.username.value,"Metode Pembayaran":self.pembayaran.value}
        ch=await kirim_ticket_dari_form(interaction,"akun","BELI AKUN",data)
        await interaction.response.send_message(f"✅ Ticket Beli Akun: {ch.mention}", ephemeral=True)

# ========== 1. SETUP ==========
@bot.tree.command(name="setup", description="Setup MIPI WORLD FINAL")
@app_commands.checks.has_permissions(administrator=True)
async def setup_slash(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild=interaction.guild; everyone=guild.default_role
    def cari_role(n): return discord.utils.get(guild.roles, name=n)
    roles_data=[("👑┃Owner",discord.Color.red(),True),("🛡️┃Admin",discord.Color.orange(),True),("🎧┃Staff",discord.Color.gold(),True),("🛠️┃Moderator",discord.Color.blue(),True),("✅┃Member",discord.Color.green(),True),("🛒┃Buyer",discord.Color.purple(),True),("👤┃Unverified",discord.Color.dark_grey(),False)]
    cr={}
    for nama,warna,pisah in roles_data:
        r=cari_role(nama) or await guild.create_role(name=nama, colour=warna, hoist=pisah, mentionable=True)
        cr[nama]=r
    try: await interaction.user.add_roles(cr["👑┃Owner"])
    except: pass
    public={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    public_readonly={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=False)}
    verify_only={everyone: discord.PermissionOverwrite(view_channel=True, send_messages=True), cr["✅┃Member"]: discord.PermissionOverwrite(view_channel=False)}
    member_only={everyone: discord.PermissionOverwrite(view_channel=False), cr["✅┃Member"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🎧┃Staff"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🛡️┃Admin"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🛠️┃Moderator"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    staff_only={everyone: discord.PermissionOverwrite(view_channel=False), cr["🎧┃Staff"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["🛡️┃Admin"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True), cr["👑┃Owner"]: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True, speak=True)}
    cat1=await guild.create_category("⎯⎯⎯• Public Area")
    for n in ["👋┃𝖶𝖾𝗅𝖼𝗈𝗆𝖾","📜┃𝖱𝗎𝗅𝖾𝗌","📢┃𝖯𝖾𝗇𝗀𝗎𝗆𝗎𝗆𝖺𝗇"]: await guild.create_text_channel(n, category=cat1, overwrites=public_readonly)
    await guild.create_text_channel("✅┃𝖵𝖾𝗋𝗂𝖿𝗂𝗄𝖺𝗌𝗂", category=cat1, overwrites=verify_only)
    await guild.create_text_channel("💬┃𝖢𝗁𝖺𝗍・𝖯𝗎𝖻𝗅𝗂𝗄", category=cat1, overwrites=public)
    cat2=await guild.create_category("⎯⎯⎯• Mipi Store")
    for n in ["🛒┃𝖮𝗋𝖽𝖾𝗋・𝖱𝗈𝖻𝗎𝗑","🏆┃𝖳𝗈𝗉・𝖯𝖾𝗆𝖻𝖾𝗅𝗂","📦┃𝖮𝗋𝖽𝖾𝗋・𝖲𝗍𝖺𝗍𝗎𝗌","💬┃𝖵𝗈𝗎𝖼𝗁","⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂"]:
        await guild.create_text_channel(n, category=cat2, overwrites=public_readonly)
    await guild.create_text_channel("💳┃𝖢𝖾𝗄・𝖲𝖺𝗅𝖽𝗈", category=cat2, overwrites=public)
    cat3=await guild.create_category("⎯⎯⎯• Member Area")
    for n in ["💭┃𝖢𝗁𝖺𝗍・𝖬𝖾𝗆𝖻𝖾𝗋","📸┃𝖦𝖺𝗅𝗅𝖾𝗋𝗒・𝖱𝗈𝖻𝗅𝗈𝗑","🎮┃𝖬𝖺𝖻𝖺𝗋・𝖱𝗈𝖻𝗅𝗈𝗑","🎁┃𝖦𝗂𝗏𝖾𝖺𝗐𝖺𝗒","🔍┃𝖢𝖾𝗄・𝖠𝗏𝖺𝗍𝖺𝗋","💰┃𝖢𝖾𝗄・𝖱𝖻𝗑"]:
        await guild.create_text_channel(n, category=cat3, overwrites=member_only)
    cat4=await guild.create_category("⎯⎯⎯• Rekber Area")
    await guild.create_text_channel("🤝┃𝖱𝖾𝗄𝖻𝖾𝗋・𝖯𝖺𝗇𝖾𝗅", category=cat4, overwrites=public_readonly)
    await guild.create_text_channel("📜┃𝖧𝗂𝗌𝗍𝗈𝗋𝗒・𝖱𝖾𝗄𝖻𝖾𝗋", category=cat4, overwrites=public_readonly)
    cat5=await guild.create_category("⎯⎯⎯• Voice Public")
    await guild.create_text_channel("✨〢𝖲etting・𝖵oice", category=cat5, overwrites=public)
    await guild.create_voice_channel("🔈〢Voice・𝖯𝗎𝖻𝗅𝗂𝗄", category=cat5, overwrites=public)
    await guild.create_voice_channel("💤┃𝖠𝖿𝗄", category=cat5, overwrites=public)
    cat6=await guild.create_category("⎯⎯⎯• Voice Member")
    await guild.create_voice_channel("🔈〢Voice・𝖬𝖾𝗆𝖻𝖾𝗋", category=cat6, overwrites=member_only)
    await guild.create_voice_channel("💤┃𝖠𝖿𝗄", category=cat6, overwrites=member_only)
    cat7=await guild.create_category("⎯⎯⎯• Staff Only")
    await guild.create_text_channel("🔕┃𝖱𝗎𝖺𝗇𝗀・𝖲𝗍𝖺𝖿", category=cat7, overwrites=staff_only)
    await guild.create_voice_channel("☏〢Staff・Voice", category=cat7, overwrites=staff_only)
    await interaction.followup.send("✅ Setup Berhasil!", ephemeral=True)

# ========== 2. GIVERROLE + VERIFY ==========
@bot.tree.command(name="giverole", description="Kasih role")
@app_commands.checks.has_permissions(administrator=True)
async def giverole_slash(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
    await user.add_roles(role)
    await interaction.response.send_message(f"✅ {user.mention} dikasih {role.mention}!")
class VerifyView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="✅ Verifikasi", style=discord.ButtonStyle.green, custom_id="verify_btn")
    async def verify(self, interaction, button):
        mr=discord.utils.get(interaction.guild.roles, name="✅┃Member")
        if not mr: mr=await interaction.guild.create_role(name="✅┃Member", colour=discord.Color.green())
        await interaction.user.add_roles(mr)
        await interaction.response.send_message("✅ Terverifikasi! Selamat datang di MIPI WORLD!", ephemeral=True)
@bot.tree.command(name="verif", description="Kirim panel verifikasi")
@app_commands.checks.has_permissions(administrator=True)
async def verif_slash(interaction):
    e=discord.Embed(title="✅ VERIFIKASI MEMBER", description="Klik tombol di bawah untuk verifikasi!", color=discord.Color.green()); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e, view=VerifyView())

# ========== 3. TICKET 5 IN 1 ==========
class VisendSelect(Select):
    def __init__(self):
        opts=[discord.SelectOption(label=f"{k.replace('_ecer',' Eceran')} Robux - {format_rupiah(v)}", emoji="⚡", value=k) for k,v in HARGA_VISEND.items()]
        super().__init__(placeholder="⚡ Pilih Jumlah Visend!", options=opts, custom_id="visend_select")
    async def callback(self, interaction):
        k=self.values[0]; harga=HARGA_VISEND[k]
        e=discord.Embed(title="⚡ VISEND DIPILIH!", description=f"**Kamu pilih:** {k.replace('_ecer',' Eceran')} Robux\n**Harga:** **{format_rupiah(harga)}**\n\nTransfer ke QRIS / DANA **{DANA_NOMOR}**, kirim bukti di sini!", color=discord.Color.from_rgb(255,193,7)); e.set_image(url=QRIS_URL)
        await interaction.response.send_message(embed=e)
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
@bot.tree.command(name="sethargavisend", description="Ganti harga Visend dari DC!")
@app_commands.checks.has_permissions(administrator=True)
async def setharga_visend(interaction, jumlah: str, harga_baru: int):
    if jumlah not in HARGA_VISEND: await interaction.response.send_message(f"❌ Ga ada! Yang ada: {', '.join(HARGA_VISEND.keys())}", ephemeral=True); return
    lama=HARGA_VISEND[jumlah]; HARGA_VISEND[jumlah]=harga_baru; simpan_harga()
    await interaction.response.send_message(f"✅ **{jumlah} Robux:** {format_rupiah(lama)} ➜ **{format_rupiah(harga_baru)}**")
@bot.tree.command(name="cekhargavisend", description="Lihat harga Visend")
async def cekharga_visend(interaction):
    daftar="\n".join([f"• **{k.replace('_ecer',' Eceran')} Robux** : {format_rupiah(v)}" for k,v in HARGA_VISEND.items()])
    await interaction.response.send_message(embed=discord.Embed(title="⚡ HARGA VISEND", description=daftar, color=discord.Color.from_rgb(255,193,7)), ephemeral=True)

# ========== 4. PRICELIST ==========
class PricelistSelect(Select):
    def __init__(self):
        super().__init__(placeholder="Pilih Kategori", options=[discord.SelectOption(label="Robux Send", emoji="📤"), discord.SelectOption(label="Robux Vilog", emoji="📦"), discord.SelectOption(label="Roblox Pluss", emoji="⭐")], custom_id="pricelist_select")
    async def callback(self, interaction):
        p=self.values[0]
        if p=="Robux Send": e=discord.Embed(title="📤 ROBUX SEND", description="• 100 R$ : Rp 16.000\n• 500 R$ : Rp 75.000\n• 1000 R$ : Rp 150.000", color=discord.Color.from_rgb(88,101,242))
        elif p=="Robux Vilog": e=discord.Embed(title="📦 ROBUX VILOG", description="• 500 R$ : Rp 77.500\n• 1000 R$ : Rp 155.000\n• 2000 R$ : Rp 310.000\n• 5000 R$ : Rp 775.000", color=discord.Color.from_rgb(88,101,242))
        else: e=discord.Embed(title="⭐ ROBLOX PLUSS", description="• 1 Bulan : Rp 120.000\n• 3 Bulan : Rp 255.000\n• 12 Bulan : Rp 995.000", color=discord.Color.from_rgb(88,101,242))
        await interaction.response.send_message(embed=e, ephemeral=True)
class PricelistView(View):
    def __init__(self): super().__init__(timeout=None); self.add_item(PricelistSelect())
@bot.tree.command(name="pricelist", description="Kirim panel pricelist")
@app_commands.checks.has_permissions(administrator=True)
async def pricelist_slash(interaction):
    e=discord.Embed(title="📋 DAFTAR HARGA - MIPI WORLD", description="Pilih kategori di bawah!", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e, view=PricelistView())

# ========== 5. WELCOME ==========
@bot.event
async def on_member_join(member):
    ch=discord.utils.get(member.guild.text_channels, name="👋┃𝖶𝖾𝗅𝖼𝗈𝗆𝖾")
    if not ch: return
    e=discord.Embed(title="👋 WELCOME", description=f"{member.mention}", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI)
    await ch.send(embed=e)

# ========== 6. CEK AVATAR + CEK RBX ==========
async def get_roblox_id(username):
    async with aiohttp.ClientSession() as s:
        async with s.post("https://users.roblox.com/v1/usernames/users", json={"usernames":[username]}) as r:
            d=await r.json()
            return d["data"][0]["id"] if d.get("data") else None
@bot.tree.command(name="cekavatar", description="Cek avatar Roblox")
async def cekavatar_cmd(interaction, username: str):
    await interaction.response.defer()
    uid=await get_roblox_id(username)
    if not uid: await interaction.followup.send(f"❌ `{username}` ga ketemu!"); return
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://users.roblox.com/v1/users/{uid}") as r: profil=await r.json()
        async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar?userIds={uid}&size=720x720&format=Png&isCircular=false") as r: full=(await r.json())["data"][0]["imageUrl"]
        async with s.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false") as r: head=(await r.json())["data"][0]["imageUrl"]
    e=discord.Embed(title=f"🖼️ AVATAR • {profil['name']}", description=f"Display: {profil['displayName']} | ID: `{uid}`", color=discord.Color.from_rgb(88,101,242))
    e.set_image(url=full); e.set_thumbnail(url=head)
    await interaction.followup.send(embed=e)
@bot.tree.command(name="cekrbx", description="Cek Robux seseorang")
async def cekrbx_cmd(interaction, username: str):
    await interaction.response.defer()
    uid=await get_roblox_id(username)
    if not uid: await interaction.followup.send(f"❌ `{username}` ga ketemu!"); return
    async with aiohttp.ClientSession() as s:
        async with s.get(f"https://economy.roblox.com/v1/users/{uid}/currency") as r: cur=await r.json() if r.status==200 else {"robux":0}
    e=discord.Embed(title=f"💰 CEK RBX • {username}", description=f"**Robux Saat Ini:** **{cur.get('robux',0)} Robux**", color=discord.Color.gold())
    await interaction.followup.send(embed=e)
@bot.tree.command(name="panelcekavatar", description="Kirim panel Cek Avatar")
@app_commands.checks.has_permissions(administrator=True)
async def panelcekavatar(interaction):
    e=discord.Embed(title="🔍 CEK AVATAR", description="Ketik `/cekavatar username:UsernameRoblox`", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)
@bot.tree.command(name="panelcekrbx", description="Kirim panel Cek Rbx")
@app_commands.checks.has_permissions(administrator=True)
async def panelcekrbx(interaction):
    e=discord.Embed(title="💰 CEK RBX", description="Ketik `/cekrbx username:UsernameRoblox`", color=discord.Color.gold()); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)

# ========== 7. CEK GAMEPASS & PENDING ==========
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
    e=discord.Embed(title=f"🎟️ GAMEPASS • {d['name']}", description=f"**Harga:** {d.get('price') or 'GRATIS'} Robux\n**Status:** {'✅ ON SALE' if d.get('isForSale') else '❌ OFF SALE'}", color=discord.Color.from_rgb(88,101,242))
    await interaction.followup.send(embed=e)
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
    e=discord.Embed(title=f"⏳ PENDING • {d['name']}", description=f"**Harga:** {harga} Robux\n**Masuk (70%):** {diterima} Robux\n**Cair:** {cair.strftime('%d %B %Y')} - {cair2.strftime('%d %B %Y')}", color=discord.Color.orange())
    await interaction.followup.send(embed=e)

# ========== 8. TOP PEMBELI ==========
class TopPembeliView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔄 Refresh Top Pembeli", style=discord.ButtonStyle.green, emoji="🏆", custom_id="refresh_top")
    async def refresh(self, interaction, button): await interaction.response.send_message(embed=buat_embed_top(interaction.guild), ephemeral=False)
def buat_embed_top(guild):
    if not ORDERS: return discord.Embed(title="🏆 TOP PEMBELI", description="Belum ada yang order!", color=discord.Color.gold())
    sorted_top=sorted(ORDERS.items(), key=lambda x: x[1]["total_rupiah"], reverse=True)[:10]
    teks=""; medal=["🥇","🥈","🥉","4.","5.","6.","7.","8.","9.","10."]
    for i,(uid,data) in enumerate(sorted_top):
        m=guild.get_member(int(uid)); nama=m.mention if m else f"<@{uid}>"
        teks+=f"{medal[i]} {nama} - **{data['total_order']}x** | {data['total_robux']} Robux | {format_rupiah(data['total_rupiah'])}\n"
    e=discord.Embed(title="🏆 TOP PEMBELI - MIPI WORLD", description=teks, color=discord.Color.gold()); e.set_image(url=BANNER_MIPI); return e
@bot.tree.command(name="toppembeli", description="Lihat Top Pembeli")
async def toppembeli_cmd(interaction): await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=TopPembeliView())
@bot.tree.command(name="paneltoppembeli", description="Kirim panel Top Pembeli")
@app_commands.checks.has_permissions(administrator=True)
async def paneltoppembeli(interaction): await interaction.response.send_message(embed=buat_embed_top(interaction.guild), view=TopPembeliView())
@bot.tree.command(name="tambahorder", description="Staff: Tambah order")
@app_commands.checks.has_permissions(administrator=True)
async def tambahorder_cmd(interaction, user: discord.Member, robux: int, rupiah: int):
    tambah_order(user.id, robux, rupiah); await interaction.response.send_message(f"✅ {user.mention} +{robux} Robux | {format_rupiah(rupiah)}")

# ========== 9. CEK SALDO ==========
@bot.tree.command(name="ceksaldo", description="Cek saldo")
async def ceksaldo_cmd(interaction, user: discord.Member = None):
    target=user or interaction.user; saldo=SALDO.get(str(target.id),0); order=ORDERS.get(str(target.id), {"total_order":0,"total_robux":0,"total_rupiah":0})
    e=discord.Embed(title=f"💳 SALDO • {target.display_name}", description=f"**Saldo:** **{format_rupiah(saldo)}**\n**Total Order:** {order['total_order']}x\n**Total Robux:** {order['total_robux']} Robux", color=discord.Color.green()); e.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=e, ephemeral=(user is None))
@bot.tree.command(name="tambahsaldo", description="Staff: Tambah saldo")
@app_commands.checks.has_permissions(administrator=True)
async def tambahsaldo_cmd(interaction, user: discord.Member, jumlah: int):
    SALDO[str(user.id)]=SALDO.get(str(user.id),0)+jumlah; save_json("saldo.json", SALDO)
    await interaction.response.send_message(f"✅ Saldo {user.mention} +{format_rupiah(jumlah)}")
@bot.tree.command(name="panelceksaldo", description="Kirim panel Cek Saldo")
@app_commands.checks.has_permissions(administrator=True)
async def panelceksaldo(interaction):
    e=discord.Embed(title="💳 CEK SALDO", description="Ketik `/ceksaldo`", color=discord.Color.green()); e.set_image(url=BANNER_MIPI); await interaction.response.send_message(embed=e)

# ========== 10. ORDER STATUS ==========
@bot.tree.command(name="cekorder", description="Cek status order")
async def cekorder_cmd(interaction):
    order=ORDERS.get(str(interaction.user.id))
    if not order: await interaction.response.send_message("❌ Belum pernah order!", ephemeral=True); return
    e=discord.Embed(title=f"📦 ORDER STATUS • {interaction.user.display_name}", description=f"**Total Order:** {order['total_order']}x\n**Total Robux:** {order['total_robux']} Robux\n**Total Belanja:** {format_rupiah(order['total_rupiah'])}", color=discord.Color.from_rgb(88,101,242))
    await interaction.response.send_message(embed=e, ephemeral=True)
@bot.tree.command(name="panelorderstatus", description="Kirim panel Order Status")
@app_commands.checks.has_permissions(administrator=True)
async def panelorderstatus(interaction):
    e=discord.Embed(title="📦 ORDER STATUS", description="Order baru auto muncul di sini!\nKetik `/cekorder` buat cek order kamu!", color=discord.Color.from_rgb(88,101,242)); e.set_image(url=BANNER_MIPI); await interaction.response.send_message(embed=e)
@bot.tree.command(name="updatestatus", description="Staff: Update status order")
@app_commands.checks.has_permissions(administrator=True)
async def updatestatus_cmd(interaction, user: discord.Member, status: str, keterangan: str = ""):
    await interaction.response.send_message(embed=discord.Embed(title=f"📦 UPDATE - {user.display_name}", description=f"**Pembeli:** {user.mention}\n**Status:** **{status}**\n**Ket:** {keterangan or '-'}", color=discord.Color.green()))

# ========== 11. REKBER ==========
class RekberModal(Modal, title="Buat Rekber Baru"):
    penjual = TextInput(label="Username Penjual (@Tag)", placeholder="@Penjual", required=True)
    pembeli = TextInput(label="Username Pembeli (@Tag)", placeholder="@Pembeli", required=True)
    barang = TextInput(label="Barang Yang Direkberkan", placeholder="Contoh: Akun R6", required=True, style=discord.TextStyle.paragraph)
    harga = TextInput(label="Harga Rekber", placeholder="Contoh: Rp 200.000", required=True)
    pembayaran = TextInput(label="Metode Pembayaran", placeholder="QRIS / DANA", default="QRIS", required=True)
    async def on_submit(self, interaction):
        guild=interaction.guild; cat=discord.utils.get(guild.categories, name="⎯⎯⎯• Rekber Area")
        overwrites={guild.default_role: discord.PermissionOverwrite(view_channel=False), interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True), guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        ch=await guild.create_text_channel(f"🤝┃rekber-{interaction.user.name}", category=cat, overwrites=overwrites)
        e=discord.Embed(title="🤝 REKBER DIMULAI!", description=f"**Penjual:** {self.penjual.value}\n**Pembeli:** {self.pembeli.value}\n**Barang:** {self.barang.value}\n**Harga:** {self.harga.value}\n**Pembayaran:** {self.pembayaran.value}\n**Admin:** {interaction.user.mention}\n\n1. Pembeli TF ke Admin (QRIS / DANA {DANA_NOMOR})\n2. Penjual kirim barang ke Admin\n3. Admin cek & teruskan\n4. Selesai ✅", color=discord.Color.green())
        await ch.send(embed=e, view=RekberSelesaiView(penjual=self.penjual.value, pembeli=self.pembeli.value, barang=self.barang.value, harga=self.harga.value))
        await interaction.response.send_message(f"✅ Rekber: {ch.mention}", ephemeral=True)
class RekberSelesaiView(View):
    def __init__(self, penjual="", pembeli="", barang="", harga=""):
        super().__init__(timeout=None); self.penjual=penjual; self.pembeli=pembeli; self.barang=barang; self.harga=harga
    @discord.ui.button(label="✅ Rekber Selesai", style=discord.ButtonStyle.green, custom_id="rekber_selesai")
    async def selesai(self, interaction, button):
        REKBER_HISTORY.append({"penjual":self.penjual,"pembeli":self.pembeli,"barang":self.barang,"harga":self.harga,"tanggal":datetime.now().strftime("%d %B %Y %H:%M"),"admin":str(interaction.user)}); save_json("rekber_history.json", REKBER_HISTORY)
        hist_ch=discord.utils.get(interaction.guild.text_channels, name="📜┃𝖧𝗂𝗌𝗍𝗈𝗋𝗒・𝖱𝖾𝗄𝖻𝖾𝗋")
        if hist_ch: await hist_ch.send(embed=discord.Embed(title="✅ REKBER SELESAI!", description=f"**Penjual:** {self.penjual}\n**Pembeli:** {self.pembeli}\n**Barang:** {self.barang}\n**Harga:** {self.harga}\n**Admin:** {interaction.user.mention}", color=discord.Color.green()))
        await interaction.response.send_message("✅ Rekber SELESAI & masuk History! Tutup 10 detik..."); await asyncio.sleep(10); await interaction.channel.delete()
class RekberPanelView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🤝 Buat Rekber Baru", style=discord.ButtonStyle.green, custom_id="buat_rekber", emoji="🤝")
    async def buat(self, interaction, button): await interaction.response.send_modal(RekberModal())
@bot.tree.command(name="rekberpanel", description="Kirim panel Rekber")
@app_commands.checks.has_permissions(administrator=True)
async def rekberpanel_cmd(interaction):
    e=discord.Embed(title="🤝 REKBER PANEL", description="Transaksi aman pake Rekber!\nKlik tombol di bawah!", color=discord.Color.green()); e.set_image(url=BANNER_MIPI); await interaction.response.send_message(embed=e, view=RekberPanelView())
@bot.tree.command(name="historyrekber", description="Lihat History Rekber")
async def historyrekber_cmd(interaction):
    if not REKBER_HISTORY: await interaction.response.send_message("Belum ada history!", ephemeral=True); return
    teks="".join([f"✅ **{h['barang']}** - {h['harga']} | {h['penjual']} ➜ {h['pembeli']} | {h['tanggal']}\n" for h in REKBER_HISTORY[-10:]])
    await interaction.response.send_message(embed=discord.Embed(title="📜 HISTORY REKBER", description=teks, color=discord.Color.green()))
@bot.tree.command(name="panelhistoryrekber", description="Kirim panel History Rekber")
@app_commands.checks.has_permissions(administrator=True)
async def panelhistoryrekber(interaction):
    e=discord.Embed(title="📜 HISTORY REKBER", description="Rekber selesai auto masuk sini!\nKetik `/historyrekber`", color=discord.Color.green()); e.set_image(url=BANNER_MIPI); await interaction.response.send_message(embed=e)

# ========== 12. GIVEAWAY ==========
class GiveawayView(View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🎁 Ikut Giveaway!", style=discord.ButtonStyle.green, emoji="🎁", custom_id="join_giveaway")
    async def join(self, interaction, button):
        mid=str(interaction.message.id)
        if mid not in GIVEAWAYS: await interaction.response.send_message("❌ Giveaway udah berakhir!", ephemeral=True); return
        if interaction.user.id in GIVEAWAYS[mid]["peserta"]: await interaction.response.send_message("❌ Udah ikut!", ephemeral=True); return
        GIVEAWAYS[mid]["peserta"].append(interaction.user.id)
        await interaction.response.send_message(f"✅ Ikut Giveaway **{GIVEAWAYS[mid]['hadiah']}**!", ephemeral=True)
@bot.tree.command(name="giveaway", description="Staff: Buat Giveaway!")
@app_commands.checks.has_permissions(administrator=True)
async def giveaway_cmd(interaction, hadiah: str, menit: int, pemenang: int = 1):
    await interaction.response.defer()
    berakhir=datetime.now()+timedelta(minutes=menit)
    e=discord.Embed(title="🎁 GIVEAWAY - MIPI WORLD!", description=f"**Hadiah:** **{hadiah}**\n**Pemenang:** {pemenang} orang\n**Berakhir:** <t:{int(berakhir.timestamp())}:R>\n\nKlik tombol buat ikut!", color=discord.Color.from_rgb(255,158,187)); e.set_image(url=BANNER_MIPI)
    await interaction.followup.send(embed=e, view=GiveawayView())
    msg_id=None
    async for m in interaction.channel.history(limit=1): msg_id=m.id
    GIVEAWAYS[str(msg_id)]={"hadiah":hadiah,"berakhir":berakhir,"peserta":[],"pemenang":pemenang}
    await asyncio.sleep(menit*60)
    data=GIVEAWAYS.pop(str(msg_id), None)
    if not data or not data["peserta"]: await interaction.channel.send(f"❌ Giveaway **{hadiah}** berakhir, ga ada yang ikut!"); return
    winners=random.sample(data["peserta"], min(pemenang, len(data["peserta"])))
    teks=" ".join([f"<@{w}>" for w in winners])
    await interaction.channel.send(f"🎉 **GIVEAWAY SELESAI!**\n\n**Hadiah:** {hadiah}\n**Pemenang:** {teks}\n\nChat Admin buat klaim! 🎁")
@bot.tree.command(name="panelgiveaway", description="Kirim panel Giveaway")
@app_commands.checks.has_permissions(administrator=True)
async def panelgiveaway(interaction):
    e=discord.Embed(title="🎁 GIVEAWAY", description="Giveaway aktif muncul di sini!\nStaff: `/giveaway hadiah:100 Robux menit:60 pemenang:1`", color=discord.Color.from_rgb(255,158,187)); e.set_image(url=BANNER_MIPI); await interaction.response.send_message(embed=e)

# ========== 13. ⭐ VOUCH & TESTIMONI - COMMAND TAMBAHAN ==========
@bot.tree.command(name="vouch", description="Staff: Buat Vouch manual pake foto yang udah diupload (reply ke foto / paste link)")
@app_commands.checks.has_permissions(administrator=True)
async def vouch_cmd(interaction, buyer: discord.Member, produk: str, jumlah_robux: str, link_bukti: str = "", pesan: str = ""):
    nomor = await kirim_vouch_testimoni(interaction.guild, buyer, produk, jumlah_robux, link_bukti, interaction.user, pesan)
    await interaction.response.send_message(f"✅ **Vouch #{nomor} berhasil!**\nUdah ke-post ke #⭐┃𝖳𝖾𝗌𝗍𝗂𝗆𝗈𝗇𝗂 + #💬┃𝖵𝗈𝗎𝖼𝗁 + Buyer masuk Top Pembeli!")

@bot.tree.command(name="testimoni", description="Staff: Buat Testimoni dari foto - sama kaya vouch tapi format Testimoni")
@app_commands.checks.has_permissions(administrator=True)
async def testimoni_cmd(interaction, buyer: discord.Member, produk: str, jumlah_robux: str, link_bukti: str = "", pesan: str = ""):
    nomor = await kirim_vouch_testimoni(interaction.guild, buyer, produk, jumlah_robux, link_bukti, interaction.user, pesan or "Makasih udah order di MIPI STORE! 🎀")
    await interaction.response.send_message(f"✅ **Testimoni #{nomor} berhasil!**\nUdah ke-post ke Testimoni + Vouch!")

@bot.tree.command(name="panelvouch", description="Kirim panel Vouch")
@app_commands.checks.has_permissions(administrator=True)
async def panelvouch(interaction):
    total = len(VOUCH_DATA)
    e=discord.Embed(title="✅ VOUCH - MIPI STORE TERPERCAYA!", description=f"Total Vouch Sukses: **{total}**\n\nSemua order yang berhasil bakal muncul di sini otomatis!\n\nMau order juga? Klik #open-ticket-dll!\n\n⭐⭐⭐⭐⭐ 5/5 - Aman, Cepat, Terpercaya!", color=discord.Color.green()); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="paneltestimoni", description="Kirim panel Testimoni")
@app_commands.checks.has_permissions(administrator=True)
async def paneltestimoni(interaction):
    total = len(VOUCH_DATA)
    e=discord.Embed(title="⭐ TESTIMONI - MIPI WORLD ⭐", description=f"Total Testimoni: **{total}**\n\nSemua bukti Robux masuk bakal muncul di sini!\n\nMau jadi testimoni berikutnya? Order di #open-ticket-dll! 🎀", color=discord.Color.from_rgb(255,158,187)); e.set_image(url=BANNER_MIPI)
    await interaction.response.send_message(embed=e)

# AUTO: Kalo ada yang kirim foto di ticket + ketik !testimoni, langsung jadi testimoni!
@bot.event
async def on_message(message):
    if message.author.bot: return
    # Cek kalo di channel ticket & ada foto + ketik !testimoni
    if message.channel.name.startswith("🎫") and message.attachments and message.content.lower().startswith("!testimoni"):
        # Ambil foto pertama
        foto = message.attachments[0].url
        # Format: !testimoni @buyer 500 Robux Visend
        parts = message.content.split()
        # Cari buyer dari mention
        buyer = message.mentions[0] if message.mentions else message.author
        produk = "Visend"
        jumlah = "500 Robux"
        if len(parts) >= 3:
            jumlah = " ".join(parts[2:4]) if len(parts) >= 4 else parts[2]
        nomor = await kirim_vouch_testimoni(message.guild, buyer, produk, jumlah, foto, message.author, "Robux udah masuk! Makasih udah order! 🎀")
        await message.reply(f"✅ **Otomatis jadi Testimoni #{nomor}!**\nUdah ke-post ke Testimoni + Vouch!")
    await bot.process_commands(message)

# ========== 14. ON READY ==========
@bot.event
async def on_ready():
    print(f"{bot.user} Online!")
    bot.add_view(VerifyView()); bot.add_view(TicketView()); bot.add_view(VisendView()); bot.add_view(CloseTicketView()); bot.add_view(TicketActionView()); bot.add_view(PricelistView()); bot.add_view(TopPembeliView()); bot.add_view(RekberPanelView()); bot.add_view(GiveawayView()); bot.add_view(RekberSelesaiView())
    try:
        synced=await bot.tree.sync(); print(f"Sync {len(synced)} command!")
    except Exception as ex: print(ex)

bot.run(TOKEN)
