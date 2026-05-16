#!/usr/bin/env python3
# ==========================================
#   📡 IPTV GOD MODE v5 - Paraguay Edition
#   👨‍💻 Desarrollador: IMHOTEP
# ==========================================

import sys
import asyncio
import aiohttp
import time
import re
import json

# 🇵🇾 COLORES
RED = "\033[91m"
WHITE = "\033[97m"
BLUE = "\033[94m"
RESET = "\033[0m"

OUTPUT_M3U = "god_lista.m3u"
OUTPUT_JSON = "god_lista.json"
OUTPUT_TXT = "archivos.txt"

# ------------------------------------------
# 🎨 BANNER PARAGUAY
# ------------------------------------------
def banner():
    print(f"""{RED}
██████╗  █████╗ ███╗   ██╗
██╔══██╗██╔══██╗████╗  ██║
██████╔╝███████║██╔██╗ ██║
██╔═══╝ ██╔══██║██║╚██╗██║
██║     ██║  ██║██║ ╚████║
╚═╝     ╚═╝  ╚═╝╚═╝  ╚═══╝
{WHITE}
        📡 IPTV GOD MODE v5
{BLUE}
     🇵🇾 IMHOTEP - PARAGUAY EDITION
════════════════════════════════════
{RESET}
""")

# ------------------------------------------
# 📊 BARRA DE PROGRESO 🇵🇾
# ------------------------------------------
def progress(done, total):
    percent = int((done / total) * 100)
    size = 30
    filled = int(size * done / total)

    r = int(filled / 3)
    w = int(filled / 3)
    b = filled - r - w

    bar = RED + "█" * r + WHITE + "█" * w + BLUE + "█" * b
    bar += "-" * (size - filled)

    print(f"\r{bar} {percent}% ({done}/{total})", end="")

# ------------------------------------------
# 📥 PARSER M3U
# ------------------------------------------
def load():
    print(WHITE + "\n📥 Pega lista IPTV (M3U o URLs)" + RESET)
    print("Ctrl+D / Ctrl+Z + Enter\n")

    data = sys.stdin.read()

    channels = []
    current = {"name": None, "group": "General"}

    for line in data.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF"):
            try:
                name = line.split(",", 1)[1]
                group_match = re.search(r'group-title="(.*?)"', line)
                group = group_match.group(1) if group_match else "General"

                current = {"name": name, "group": group}
            except:
                current = {"name": "Canal", "group": "General"}

        elif line.startswith("http"):
            channels.append({
                "name": current["name"] or line,
                "group": current["group"],
                "url": line
            })
            current = {"name": None, "group": "General"}

    # eliminar duplicados
    seen = set()
    unique = []
    for c in channels:
        if c["url"] not in seen:
            seen.add(c["url"])
            unique.append(c)

    return unique

# ------------------------------------------
# 🧠 CALIDAD
# ------------------------------------------
def detect_quality(url):
    url = url.lower()

    if "2160" in url or "4k" in url:
        return "4K"
    elif "1080" in url:
        return "1080p"
    elif "720" in url:
        return "720p"
    return "SD"

# ------------------------------------------
# 🔎 CHECK STREAM
# ------------------------------------------
async def check(session, channel):
    url = channel["url"]
    start = time.time()

    try:
        async with session.get(url, timeout=6) as res:
            latency = round(time.time() - start, 2)

            if res.status != 200:
                return None

            ctype = res.headers.get("Content-Type", "").lower()

            if not any(x in ctype for x in ["video", "mpegurl", "octet-stream"]):
                return None

            chunk = await res.content.read(1024)
            if not chunk:
                return None

            quality = detect_quality(url)

            score = 100 - (latency * 10)

            if quality == "4K":
                score += 15
            elif quality == "1080p":
                score += 10
            elif quality == "720p":
                score += 5

            return {
                "name": channel["name"],
                "group": channel["group"],
                "url": url,
                "latency": latency,
                "quality": quality,
                "score": round(score, 2)
            }

    except:
        return None

# ------------------------------------------
# 🚀 SCAN
# ------------------------------------------
async def scan():
    channels = load()

    if not channels:
        print(RED + "❌ No se detectaron canales" + RESET)
        return

    total = len(channels)
    print(BLUE + f"\n🔎 Escaneando {total} canales...\n" + RESET)

    connector = aiohttp.TCPConnector(limit=50)

    done = 0
    results = []

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [check(session, c) for c in channels]

        for coro in asyncio.as_completed(tasks):
            result = await coro
            results.append(result)

            done += 1
            progress(done, total)

    print("\n")

    working = [r for r in results if r]

    print(WHITE + f"\n✔ Activos: {len(working)} / {total}" + RESET)

    working.sort(key=lambda x: x["score"], reverse=True)

    print(BLUE + "\n📺 TOP STREAMS:\n" + RESET)

    for c in working[:15]:
        print(
            RED + f"[{c['quality']}]" + " " +
            WHITE + c['name'] + " " +
            BLUE + f"({c['latency']}s) ⭐{c['score']}" +
            RESET
        )

    # 💾 M3U
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for c in working:
            f.write(f'#EXTINF:-1 group-title="{c["group"]}",{c["name"]}\n')
            f.write(c["url"] + "\n")

    # 💾 JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(working, f, indent=2, ensure_ascii=False)

    # 💾 TXT
    with open(OUTPUT_TXT, "w", encoding="utf-8") as f:
        f.write("=== IPTV SCAN RESULT ===\n")
        f.write("Edición Paraguay 🇵🇾\n")
        f.write("Desarrollador: IMHOTEP\n\n")

        for i, c in enumerate(working, 1):
            f.write(f"{i}. {c['name']}\n")
            f.write(f"   Grupo: {c['group']}\n")
            f.write(f"   Calidad: {c['quality']}\n")
            f.write(f"   Latencia: {c['latency']}s\n")
            f.write(f"   Score: {c['score']}\n")
            f.write(f"   URL: {c['url']}\n\n")

    print(BLUE + "\n💾 Exportado:" + RESET)
    print(WHITE + f" - {OUTPUT_M3U}")
    print(WHITE + f" - {OUTPUT_JSON}")
    print(WHITE + f" - {OUTPUT_TXT}" + RESET)

# ------------------------------------------
# 🎯 MAIN
# ------------------------------------------
if __name__ == "__main__":
    banner()
    print(BLUE + "🚀 IPTV GOD MODE ACTIVADO\n" + RESET)
    asyncio.run(scan())