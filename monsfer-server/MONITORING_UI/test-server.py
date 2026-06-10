import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track
import time
import random

console = Console()

# Konfigurasi Target
TARGET_URL = "http://127.0.0.1:5002"  # Diset ke port 5002 sesuai instruksi
LOGIN_URL = f"{TARGET_URL}/login"
API_SPECTRUM_URL = f"{TARGET_URL}/api/spectrum"
MONITORING_URL = f"{TARGET_URL}/monitoring"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def show_banner():
    console.print(Panel.fit("🛡️ FLASK WEB APP SECURITY SCANNER", border_style="blue"))

def test_requests_access():
    console.rule("[bold blue]Tes dengan Requests")
    try:
        response = requests.get(MONITORING_URL, headers=HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "No Title"
            console.print(f"[+] Page Title: {title}")
            console.print("[yellow]⚠️ Akses berhasil via Requests → Rentan Scraping[/]")
        else:
            console.print(f"[-] Status Code: {response.status_code}")
            console.print("[green]✅ Tidak bisa diakses via Requests → Aman[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

def test_selenium_browser():
    console.rule("[bold blue]Tes dengan Selenium (Headless Chrome)")
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(HEADERS["User-Agent"])
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(MONITORING_URL)
        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else "No Title"
        console.print(f"[+] Page Title: {title}")
        console.print("[yellow]⚠️ Akses berhasil via Selenium → Bisa discrape![/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
    finally:
        if driver:
            driver.quit()
            console.print("[*] Browser closed.")

def test_playwright_browser():
    console.rule("[bold blue]Tes dengan Playwright (Chromium Headless)")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(MONITORING_URL)
            time.sleep(2)
            title = page.title()
            content = page.content()
            console.print(f"[+] Page Title: {title}")
            if "spectrum" in content.lower():
                console.print("[yellow]⚠️ Akses berhasil via Playwright → Bisa discrape![/]")
            else:
                console.print("[green]✅ Tidak bisa diakses via Playwright → Aman[/]")
            browser.close()
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")

def check_user_agent_filter():
    console.rule("[bold blue]Pengecekan Filter User-Agent")
    bad_ua = "curl/7.68.0"
    try:
        response = requests.get(MONITORING_URL, headers={"User-Agent": bad_ua})
        if response.status_code == 200:
            console.print("❌ [red]Akses diterima dari curl/user-agent palsu → Rentan[/]")
        else:
            console.print("✅ [green]Hanya browser yang diizinkan → Aman[/]")
    except Exception as e:
        console.print(f"[!] Error: {e}", style="bold red")

def check_javascript_render():
    console.rule("[bold blue]Pengecekan Perlunya JavaScript")
    response = requests.get(MONITORING_URL)
    if "DOMContentLoaded" in response.text or "window.onload" in response.text:
        console.print("[green]✅ Halaman bergantung pada JavaScript → Lebih aman dari scraping dasar[/]")
    else:
        console.print("[yellow]⚠️  Halaman bisa discrape tanpa JS → Perlu proteksi tambahan[/]")

def directory_fuzzing():
    paths = [
        "/admin", "/login", "/dashboard", "/api", "/debug",
        "/config", "/backup", "/logs", "/.git", "/.env"
    ]
    console.rule("[bold blue]Directory Fuzzing")
    found = []
    for path in track(paths, description="Scanning..."):
        try:
            r = requests.get(f"{TARGET_URL}{path}")
            if r.status_code == 200:
                found.append(path)
                console.print(f"🟢 [green]{path} => {r.status_code}[/]")
            else:
                console.print(f"🔴 {path} => {r.status_code}")
        except:
            console.print(f"⚠️  Tidak dapat mengakses {path}")
    if len(found) > 0:
        console.print("\n[!] Path aktif ditemukan:")
        for p in found:
            console.print(f" - {p}")

def test_sql_injection():
    payloads = ["' OR 1=1--", '" OR 1=1--', "admin' --"]
    vulnerable = False
    console.rule("[bold blue]SQL Injection Test")
    for payload in payloads:
        data = {"username": payload, "password": "test"}
        try:
            response = requests.post(LOGIN_URL, data=data, allow_redirects=False)
            if response.status_code in [200, 302]:
                console.print(f"⚠️ [yellow]Potensi kerentanan SQLi dengan payload: {payload}[/]")
                vulnerable = True
        except:
            continue
    if not vulnerable:
        console.print("✅ [green]Tidak ditemukan kerentanan SQL Injection dasar.[/]")

def test_xss():
    payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]
    found = False
    console.rule("[bold blue]XSS Test")
    for payload in payloads:
        params = {"q": payload}
        try:
            response = requests.get(f"{TARGET_URL}/search", params=params)
            if payload in response.text:
                console.print(f"⚠️ [yellow]Reflected XSS mungkin ada dengan payload: {payload}[/]")
                found = True
        except:
            continue
    if not found:
        console.print("✅ [green]Tidak ditemukan refleksi XSS dasar.[/]")

def brute_force_login():
    usernames = ["admin", "user", "test"]
    passwords = ["admin", "admin123", "123456", "password"]
    console.rule("[bold blue]Brute Force Login Test")
    for user in usernames:
        for pwd in passwords:
            data = {"username": user, "password": pwd}
            try:
                response = requests.post(LOGIN_URL, data=data, allow_redirects=False)
                if response.status_code in [200, 302]:
                    console.print(f"🔓 [green]Login berhasil! Username: {user}, Password: {pwd}[/]")
                    return
                else:
                    console.print(f"[-] Coba: {user}:{pwd}")
            except Exception as e:
                console.print(f"[!] Error pada {user}:{pwd} => {e}", style="bold red")
    console.print("❌ Tidak ada kombinasi username/password yang berhasil.")

def main_menu():
    show_banner()
    table = Table(title="Security Scanner Menu")
    table.add_column("No.")
    table.add_row("1", "Test dengan Requests")
    table.add_row("2", "Test dengan Selenium")
    table.add_row("3", "Test dengan Playwright")
    table.add_row("4", "Check User-Agent Filter")
    table.add_row("5", "Check Perlunya JavaScript")
    table.add_row("6", "Directory Fuzzing")
    table.add_row("7", "Test SQL Injection")
    table.add_row("8", "Test XSS")
    table.add_row("9", "Brute Force Login")
    table.add_row("10", "Jalankan Semua Tes")
    console.print(table)

def main():
    main_menu()
    choice = input("Pilih tes yang ingin dijalankan (1-10): ")

    match choice:
        case "1":
            test_requests_access()
        case "2":
            test_selenium_browser()
        case "3":
            test_playwright_browser()
        case "4":
            check_user_agent_filter()
        case "5":
            check_javascript_render()
        case "6":
            directory_fuzzing()
        case "7":
            test_sql_injection()
        case "8":
            test_xss()
        case "9":
            brute_force_login()
        case "10":
            test_requests_access()
            test_selenium_browser()
            test_playwright_browser()
            check_user_agent_filter()
            check_javascript_render()
            directory_fuzzing()
            test_sql_injection()
            test_xss()
            brute_force_login()
        case _:
            console.print("[-] Pilihan tidak valid.", style="bold red")

if __name__ == "__main__":
    main()