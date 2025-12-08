import os
import time
import shutil
import subprocess
from typing import List
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import psutil  # pip install psutil

# ======== Config ========
API_TOKEN = "XXXXXXXXXXXXXXXXXXXXXXXXX"
ALLOWED_USER_ID = XXXXXXXXXXX
ALLOWED_SERVICES = ["prometheus", "alertmanager", "grafana", "node_exporter"]

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ======== Access control ========
def check_access(user_id: int) -> bool:
    return user_id == ALLOWED_USER_ID

def is_allowed_service(name: str) -> bool:
    return name in ALLOWED_SERVICES

def run_docker(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)

# ======== Keyboards ========
def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Server", callback_data="menu_server"),
        InlineKeyboardButton("Containers", callback_data="menu_containers"),
    )
    return kb

def server_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("CPU", callback_data="srv_cpu"),
        InlineKeyboardButton("Memory", callback_data="srv_mem"),
        InlineKeyboardButton("Disk", callback_data="srv_disk"),
        InlineKeyboardButton("Swap", callback_data="srv_swap"),
        InlineKeyboardButton("Uptime", callback_data="srv_uptime"),
        InlineKeyboardButton("Summary", callback_data="srv_status"),
        InlineKeyboardButton("Back", callback_data="menu_main"),
    )
    return kb

def containers_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    for svc in ALLOWED_SERVICES:
        kb.add(InlineKeyboardButton(f"{svc}", callback_data=f"svc_select:{svc}"))
    kb.add(InlineKeyboardButton("Back", callback_data="menu_main"))
    return kb

def service_actions_menu(svc: str):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Start", callback_data=f"svc_start:{svc}"),
        InlineKeyboardButton("Stop", callback_data=f"svc_stop:{svc}"),
        InlineKeyboardButton("Restart", callback_data=f"svc_restart:{svc}"),
        InlineKeyboardButton("Logs", callback_data=f"svc_logs:{svc}"),
        InlineKeyboardButton("Back to list", callback_data="menu_containers"),
    )
    return kb

# ======== Server metrics ========
def fmt_bytes(num: float) -> str:
    for unit in ["B", "KiB", "MiB", "GiB", "TiB"]:
        if num < 1024.0:
            return f"{num:.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} PiB"

def get_cpu_info() -> str:
    cpu_percent = psutil.cpu_percent(interval=0.8)
    load1, load5, load15 = psutil.getloadavg()
    cores = psutil.cpu_count()
    return (
        f"CPU: {cpu_percent:.1f}%\n"
        f"Load avg: {load1:.2f} {load5:.2f} {load15:.2f}\n"
        f"Cores: {cores}"
    )

def get_mem_info() -> str:
    vm = psutil.virtual_memory()
    return (
        f"Memory: used {fmt_bytes(vm.used)} / total {fmt_bytes(vm.total)} "
        f"({vm.percent:.1f}%)\n"
        f"Available: {fmt_bytes(vm.available)}"
    )

def get_swap_info() -> str:
    sw = psutil.swap_memory()
    return f"Swap: used {fmt_bytes(sw.used)} / total {fmt_bytes(sw.total)} ({sw.percent:.1f}%)"

def get_disk_info() -> str:
    du = shutil.disk_usage("/")
    used = du.total - du.free
    percent = (used / du.total) * 100 if du.total else 0
    return (
        f"Disk (/): used {fmt_bytes(used)} / total {fmt_bytes(du.total)} "
        f"({percent:.1f}%)\n"
        f"Free: {fmt_bytes(du.free)}"
    )

def get_uptime() -> str:
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.read().split()[0])
    except Exception:
        seconds = time.time() - psutil.boot_time()
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"Uptime: {days}d {hours}h {minutes}m"

def full_status() -> str:
    return "\n".join([get_cpu_info(), get_mem_info(), get_swap_info(), get_disk_info(), get_uptime()])

# ======== Containers status ========
def list_containers_status() -> str:
    r = run_docker(["docker", "ps", "--format", "{{.Names}} {{.Status}}"])
    if r.returncode != 0:
        return f"docker ps error: {r.stderr.strip()}"
    lines = r.stdout.strip().splitlines()
    if not lines:
        return "No running containers."
    return "Containers:\n" + "\n".join(lines)

def container_status(name: str) -> str:
    r = run_docker(["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}} {{.Status}}"])
    if r.returncode != 0:
        return f"{name}: docker ps error: {r.stderr.strip()}"
    out = r.stdout.strip() or f"{name}: not found"
    return out

# ======== Handlers ========
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    if not check_access(message.from_user.id):
        return await message.reply("Access denied")
    text = (
        "Hi! I'm a production DevOps bot.\n\n"
        "Menus:\n"
        "- Server: CPU, Memory, Disk, Swap, Uptime, Summary\n"
        "- Containers: select and run Start, Stop, Restart, Logs\n\n"
        "Use the buttons below."
    )
    await message.answer(text, reply_markup=main_menu())

@dp.callback_query_handler(lambda c: c.data == "menu_main")
async def menu_main(cb: types.CallbackQuery):
    if not check_access(cb.from_user.id):
        return await cb.message.answer("Access denied")
    await cb.message.edit_text("Main menu:", reply_markup=main_menu())
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data == "menu_server")
async def menu_srv(cb: types.CallbackQuery):
    if not check_access(cb.from_user.id):
        return await cb.message.answer("Access denied")
    await cb.message.edit_text("Server menu:", reply_markup=server_menu())
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data == "menu_containers")
async def menu_ct(cb: types.CallbackQuery):
    if not check_access(cb.from_user.id):
        return await cb.message.answer("Access denied")
    status = list_containers_status()
    await cb.message.edit_text(f"{status}\n\nSelect a container:", reply_markup=containers_menu())
    await cb.answer()

# ----- Server metrics -----
@dp.callback_query_handler(lambda c: c.data.startswith("srv_"))
async def srv_metrics(cb: types.CallbackQuery):
    if not check_access(cb.from_user.id):
        return await cb.message.answer("Access denied")

    mapping = {
        "srv_cpu": get_cpu_info,
        "srv_mem": get_mem_info,
        "srv_disk": get_disk_info,
        "srv_swap": get_swap_info,
        "srv_uptime": get_uptime,
        "srv_status": full_status,
    }
    func = mapping.get(cb.data)
    if func is None:
        await cb.answer("Unknown metric")
        return
    try:
        text = func()
        await cb.message.edit_text(text, reply_markup=server_menu())
    except Exception as e:
        await cb.message.edit_text(f"Error: {e}", reply_markup=server_menu())
    await cb.answer()

# ----- Containers: select service -----
@dp.callback_query_handler(lambda c: c.data.startswith("svc_select:"))
async def svc_select(cb: types.CallbackQuery):
    if not check_access(cb.from_user.id):
        return await cb.message.answer("Access denied")
    svc = cb.data.split(":", 1)[1]
    if not is_allowed_service(svc):
        await cb.answer("Service not allowed", show_alert=True)
        return
    st = container_status(svc)
    await cb.message.edit_text(f"{st}\n\nAction for {svc}:", reply_markup=service_actions_menu(svc))
    await cb.answer()

# ----- Containers: actions -----
@dp.callback_query_handler(lambda c: c.data.startswith(("svc_start:",
