import json
import os
import random
import signal
import threading
import time
from datetime import datetime, timedelta
from tkinter import (
    BooleanVar,
    StringVar,
    Text,
    filedialog,
    messagebox,
    scrolledtext,
)

import ttkbootstrap as ttk
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# --- Konstanta ---
CONFIG_FILE = "config.json"
ERROR_URL_FILE = "failed_urls.txt"
ERROR_DIR = "Error"
USER_AGENT_DEFAULT = "useragent.txt"

# --- XPath Locators ---
XPATHS = {
    "more_button": "//button[@data-e2e='user-more' or @aria-label='Tindakan' or @aria-label='Actions']",
    "report_button": "//div[@role='button' and (@aria-label='Report' or @aria-label='Laporan')]",
    "modal_title": "//h4[@data-e2e='report-title' and (text()='Report' or text()='Laporan')]",
    "report_account_button": "//label[@data-e2e='report-card-reason' and (contains(., 'Report account') or contains(., 'Laporkan akun'))]",
    "something_else_button": "//label[@data-e2e='report-card-reason' and (contains(., 'Something else') or contains(., 'Sesuatu yang lain'))]",
    "submit_button": "//button[text()='Submit' or text()='Kirim']",
    "report_paths": {
        "hate": [
            "//label[@data-e2e='report-card-reason' and (contains(., 'Hate and harassment') or contains(., 'Kebencian dan pelecehan'))]",
            "//label[@data-e2e='report-card-reason' and (contains(., 'Hate speech and hateful behaviors') or contains(., 'Ujaran kebencian dan perilaku kebencian'))]",
        ],
        "misinformation": [
            "//label[@data-e2e='report-card-reason' and (contains(., 'Misinformation') or contains(., 'Keterangan yg salah'))]",
            "//label[@data-e2e='report-card-reason' and (contains(., 'Harmful misinformation') or contains(., 'Misinformasi yang berbahaya'))]",
        ],
        "spam": [
            "//label[@data-e2e='report-card-reason' and (contains(., 'Deceptive behavior and spam') or contains(., 'Perilaku menipu dan spam'))]",
            "//label[@data-e2e='report-card-reason' and (contains(., 'Spam'))]",
        ],
    },
}


class BotGUI(ttk.Window):
    def __init__(self):
        super().__init__(themename="darkly", title="Tiktok Report Bot")
        self.geometry("800x800")
        self.resizable(False, False)

        self.bot_thread = None
        self.stop_event = threading.Event()
        self.webdriver = None

        self.url_var = StringVar()
        self.user_agent_path_var = StringVar(value=USER_AGENT_DEFAULT)
        self.report_mode_var = StringVar(value="Sesuai Jumlah User Agent")
        self.report_count_custom_var = StringVar(value="10")
        self.timeout_var = StringVar(value="15")
        self.sleep_min_var = StringVar(value="5")
        self.sleep_max_var = StringVar(value="10")
        self.captcha_delay_var = StringVar(value="15")

        self.webdriver_options_vars = {
            "--headless=new": BooleanVar(value=False),
            "--no-sandbox": BooleanVar(value=True),
            "--disable-dev-shm-usage": BooleanVar(value=True), "--disable-notifications": BooleanVar(value=True),
            "--disable-extensions": BooleanVar(value=True), "--disable-gpu": BooleanVar(value=True),
            "--enable-webgl": BooleanVar(value=False), "--enable-smooth-scrolling": BooleanVar(value=False),
            "--start-maximized": BooleanVar(value=True),
        }

        self.create_widgets()
        self.load_config()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        signal.signal(signal.SIGINT, self.handle_graceful_shutdown)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill="both", expand=True)

        input_frame = ttk.Labelframe(main_frame, text="Pengaturan Bot", padding=10)
        input_frame.pack(fill="x", pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="URL Postingan:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.url_entry = Text(input_frame, height=4, width=50, font=("Helvetica", 10))
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ttk.Label(input_frame, text="Lokasi User Agent:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.ua_entry = ttk.Entry(input_frame, textvariable=self.user_agent_path_var)
        self.ua_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.ua_browse_button = ttk.Button(input_frame, text="Browse", command=self.browse_file)
        self.ua_browse_button.grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(input_frame, text="Mode Report:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        report_mode_frame = ttk.Frame(input_frame)
        report_mode_frame.grid(row=2, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        self.report_mode_combo = ttk.Combobox(
            report_mode_frame, textvariable=self.report_mode_var,
            values=["Sesuai Jumlah User Agent", "Jumlah Tertentu", "Gunakan User Agent Acak"],
            state="readonly"
        )
        self.report_mode_combo.pack(side="left", fill="x", expand=True)
        self.report_mode_combo.bind("<<ComboboxSelected>>", self.on_report_mode_change)

        self.report_count_spinbox = ttk.Spinbox(
            report_mode_frame, from_=1, to=1000,
            textvariable=self.report_count_custom_var, width=8
        )
        self.report_count_spinbox.pack(side="left", padx=(10, 0))

        ttk.Label(input_frame, text="Wait Timeout (s):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Spinbox(input_frame, from_=5, to=60, textvariable=self.timeout_var).grid(row=3, column=1, columnspan=2, sticky="w", padx=5, pady=5)

        ttk.Label(input_frame, text="Sleep (min-max):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        sleep_frame = ttk.Frame(input_frame)
        sleep_frame.grid(row=4, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        ttk.Spinbox(sleep_frame, from_=1, to=30, textvariable=self.sleep_min_var, width=5).pack(side="left", padx=(0, 5))
        ttk.Label(sleep_frame, text="to").pack(side="left", padx=5)
        ttk.Spinbox(sleep_frame, from_=2, to=60, textvariable=self.sleep_max_var, width=5).pack(side="left")

        ttk.Label(input_frame, text="Jeda Manual Captcha (s):").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        ttk.Spinbox(input_frame, from_=0, to=300, textvariable=self.captcha_delay_var).grid(row=5, column=1, columnspan=2, sticky="w", padx=5, pady=5)
        
        webdriver_frame = ttk.Labelframe(main_frame, text="Pengaturan WebDriver", padding=10)
        webdriver_frame.pack(fill="x", pady=10)
        for i, (option, var) in enumerate(self.webdriver_options_vars.items()):
            row, col = divmod(i, 3)
            ttk.Checkbutton(webdriver_frame, text=option, variable=var).grid(row=row, column=col, sticky="w", padx=5, pady=2)

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        button_frame.columnconfigure((0, 1, 2), weight=1)
        self.start_button = ttk.Button(button_frame, text="Mulai", bootstyle="success", command=self.start_bot)
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5)
        self.stop_button = ttk.Button(button_frame, text="Hentikan", bootstyle="danger", command=self.stop_bot, state="disabled")
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=5)
        ttk.Button(button_frame, text="Reset", bootstyle="info-outline", command=self.reset_gui).grid(row=0, column=2, sticky="ew", padx=5)

        log_frame = ttk.Labelframe(main_frame, text="Log Output", padding=10)
        log_frame.pack(fill="both", expand=True)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap="word", font=("Consolas", 10), state="disabled", height=20)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("INFO", foreground="white")
        self.log_text.tag_config("OK", foreground="#00E676")
        self.log_text.tag_config("WARN", foreground="#FFC107")
        self.log_text.tag_config("ERR", foreground="#FF5252")
        self.log_text.tag_config("SUM", foreground="#40C4FF")

    def on_report_mode_change(self, event=None):
        mode = self.report_mode_var.get()
        if mode == "Jumlah Tertentu":
            self.report_count_spinbox.config(state="normal"); self.ua_entry.config(state="normal"); self.ua_browse_button.config(state="normal")
        elif mode == "Sesuai Jumlah User Agent":
            self.report_count_spinbox.config(state="disabled"); self.ua_entry.config(state="normal"); self.ua_browse_button.config(state="normal")
        elif mode == "Gunakan User Agent Acak":
            self.report_count_spinbox.config(state="normal"); self.ua_entry.config(state="disabled"); self.ua_browse_button.config(state="disabled")

    def log(self, message, level="INFO"):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{datetime.now():%H:%M:%S}] {message}\n", level)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")

    def browse_file(self):
        filepath = filedialog.askopenfilename(title="Pilih File User Agent", filetypes=(("Text files", "*.txt"), ("All files", "*.*")))
        if filepath: self.user_agent_path_var.set(filepath)

    def save_config(self):
        config = {
            "urls": self.url_entry.get("1.0", "end-1c"), "user_agent_path": self.user_agent_path_var.get(),
            "report_mode": self.report_mode_var.get(), "report_count_custom": self.report_count_custom_var.get(),
            "timeout": self.timeout_var.get(), "sleep_min": self.sleep_min_var.get(),
            "sleep_max": self.sleep_max_var.get(), "captcha_delay": self.captcha_delay_var.get(),
            "webdriver_options": {opt: var.get() for opt, var in self.webdriver_options_vars.items()},
        }
        try:
            with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=4)
        except Exception as e: self.log(f"Gagal menyimpan konfigurasi: {e}", "ERR")

    def load_config(self):
        try:
            with open(CONFIG_FILE, "r") as f: config = json.load(f)
            self.url_entry.delete("1.0", "end"); self.url_entry.insert("1.0", config.get("urls", ""))
            self.user_agent_path_var.set(config.get("user_agent_path", USER_AGENT_DEFAULT))
            self.report_mode_var.set(config.get("report_mode", "Sesuai Jumlah User Agent"))
            self.report_count_custom_var.set(config.get("report_count_custom", "10"))
            self.timeout_var.set(config.get("timeout", "15"))
            self.sleep_min_var.set(config.get("sleep_min", "5"))
            self.sleep_max_var.set(config.get("sleep_max", "10"))
            self.captcha_delay_var.set(config.get("captcha_delay", "15"))
            for option, value in config.get("webdriver_options", {}).items():
                if option in self.webdriver_options_vars: self.webdriver_options_vars[option].set(value)
            self.log("Konfigurasi terakhir berhasil dimuat.", "OK")
        except FileNotFoundError: self.log("File konfigurasi tidak ditemukan, menggunakan nilai default.", "INFO")
        except Exception as e: self.log(f"Gagal memuat konfigurasi: {e}", "ERR")
        finally: self.on_report_mode_change()

    def reset_gui(self):
        if messagebox.askyesno("Konfirmasi Reset", "Anda yakin ingin mereset semua input dan log?"):
            self.url_entry.delete("1.0", "end")
            self.user_agent_path_var.set(USER_AGENT_DEFAULT)
            self.report_mode_var.set("Sesuai Jumlah User Agent")
            self.report_count_custom_var.set("10")
            self.timeout_var.set("15"); self.sleep_min_var.set("5"); self.sleep_max_var.set("10")
            self.captcha_delay_var.set("15")
            
            for var in self.webdriver_options_vars.values(): var.set(False)
            defaults = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-notifications", "--disable-extensions", "--disable-gpu", "--start-maximized"]
            for d in defaults: self.webdriver_options_vars[d].set(True)

            self.log_text.configure(state="normal"); self.log_text.delete("1.0", "end"); self.log_text.configure(state="disabled")
            self.log("GUI berhasil direset ke default.", "OK")
            self.on_report_mode_change()

    def start_bot(self):
        captcha_delay = int(self.captcha_delay_var.get())
        if captcha_delay > 0 and self.webdriver_options_vars["--headless=new"].get():
            messagebox.showwarning("Perhatian", "Headless mode akan dinonaktifkan karena Jeda Captcha diaktifkan, agar Anda bisa melihat browser.")
            self.webdriver_options_vars["--headless=new"].set(False)

        urls = [url for url in self.url_entry.get("1.0", "end-1c").strip().splitlines() if url.strip()]
        if not urls:
            messagebox.showerror("Error Validasi", "[✗] URL tidak ditemukan!"); self.log("[✗] URL tidak ditemukan!", "ERR"); return

        if self.report_mode_var.get() != "Gunakan User Agent Acak":
            ua_path = self.user_agent_path_var.get()
            if not os.path.exists(ua_path):
                messagebox.showerror("Error Validasi", f"[✗] File '{ua_path}' tidak ditemukan!"); self.log(f"[✗] File '{ua_path}' tidak ditemukan!", "ERR"); return
            
        self.start_button.config(state="disabled"); self.stop_button.config(state="normal"); self.stop_event.clear()
        self.bot_thread = threading.Thread(target=self.run_bot_logic, daemon=True); self.bot_thread.start()

    def stop_bot(self):
        if messagebox.askyesno("Konfirmasi Hentikan", "Yakin ingin menghentikan bot?"):
            self.stop_event.set(); self.log("🛑 Proses penghentian diminta oleh pengguna...", "WARN"); self.stop_button.config(state="disabled")

    def on_closing(self):
        if self.bot_thread and self.bot_thread.is_alive():
            if messagebox.askyesno("Keluar", "Bot sedang berjalan. Yakin ingin keluar?"):
                self.stop_event.set()
                if self.webdriver:
                    try: self.webdriver.quit()
                    except: pass
                self.save_config(); self.destroy()
        else: self.save_config(); self.destroy()

    def handle_graceful_shutdown(self, signum, frame):
        self.log("🚪 CTRL+C terdeteksi. Menghentikan program...", "WARN")
        self.stop_event.set(); time.sleep(1)
        if self.webdriver:
            try: self.webdriver.quit(); self.log("WebDriver ditutup.", "INFO")
            except Exception as e: self.log(f"Error saat menutup WebDriver: {e}", "ERR")
        self.save_config(); self.destroy()
        
    def _create_driver(self, user_agent):
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        for option, var in self.webdriver_options_vars.items():
            if var.get(): options.add_argument(option)
        try:
            service = ChromeService(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self.log(f"Gagal menginisialisasi WebDriver: {e}", "ERR"); return None
    
    def _js_click(self, driver, element):
        driver.execute_script("arguments[0].click();", element)
        
    def run_bot_logic(self):
        start_time = time.time()
        urls_to_process = [url.strip() for url in self.url_entry.get("1.0", "end-1c").strip().splitlines() if url.strip()]
        
        user_agents = []; ua_generator = None; report_mode = self.report_mode_var.get()
        
        if report_mode == "Gunakan User Agent Acak":
            try: ua_generator = UserAgent()
            except Exception as e: self.log(f"Gagal inisialisasi User Agent Acak: {e}", "ERR"); self.bot_finished(); return
        else:
            try:
                with open(self.user_agent_path_var.get(), 'r', encoding="utf-8") as f: user_agents = [line.strip() for line in f if line.strip()]
                if not user_agents: self.log(f"File user agent kosong!", "ERR"); self.bot_finished(); return
            except Exception as e: self.log(f"Gagal membaca file user agent: {e}", "ERR"); self.bot_finished(); return
        
        if report_mode == "Sesuai Jumlah User Agent": reports_to_do = len(user_agents)
        else:
            try: reports_to_do = int(self.report_count_custom_var.get())
            except ValueError: self.log(f"Jumlah report kustom tidak valid. Default ke 10.", "WARN"); reports_to_do = 10
        
        if not os.path.exists(ERROR_DIR): os.makedirs(ERROR_DIR)
            
        success_count, fail_count = 0, 0
        self.log(f"🤖 Bot dimulai. URL: {len(urls_to_process)}, Target Report: {reports_to_do} ({report_mode})", "INFO")

        for i, url in enumerate(urls_to_process):
            if self.stop_event.is_set(): self.log("Bot dihentikan.", "WARN"); break
            self.log(f"--- Memproses URL {i+1}/{len(urls_to_process)}: {url} ---", "INFO")
            
            reports_per_url = 0
            while reports_per_url < reports_to_do:
                if self.stop_event.is_set(): break
                
                for path_name, path_xpaths in XPATHS["report_paths"].items():
                    if reports_per_url >= reports_to_do or self.stop_event.is_set(): break
                    
                    self.log(f"Melakukan report jalur '{path_name.upper()}' ({reports_per_url + 1}/{reports_to_do})...", "INFO")
                    
                    current_ua = ua_generator.random if ua_generator else random.choice(user_agents)
                    self.webdriver = self._create_driver(current_ua)
                    
                    if not self.webdriver:
                        fail_count += 1; reports_per_url += 1; continue

                    try:
                        self.webdriver.get(url)
                        
                        try:
                            captcha_delay = int(self.captcha_delay_var.get())
                            if captcha_delay > 0:
                                self.log(f"Jeda manual untuk verifikasi CAPTCHA diaktifkan.", "WARN")
                                for i in range(captcha_delay, 0, -1):
                                    if self.stop_event.is_set(): break
                                    self.log(f"Silakan selesaikan CAPTCHA dalam {i} detik...", "WARN")
                                    time.sleep(1)
                                
                                if not self.stop_event.is_set():
                                    self.log(f"Waktu jeda selesai. Me-refresh halaman untuk sinkronisasi...", "OK")
                                    self.webdriver.refresh()
                                    time.sleep(2)
                                    self.log(f"Refresh selesai, melanjutkan bot...", "OK")
                        except ValueError:
                            self.log("Nilai jeda captcha tidak valid, jeda dilewati.", "ERR")

                        wait = WebDriverWait(self.webdriver, int(self.timeout_var.get()))
                        
                        # --- CARA PEMANGGILAN FUNGSI KLIK DIPERBAIKI DI SINI ---
                        more_button = wait.until(EC.presence_of_element_located((By.XPATH, XPATHS["more_button"])))
                        self._js_click(self.webdriver, more_button)
                        time.sleep(random.uniform(1, 3))

                        report_button = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS["report_button"])))
                        self._js_click(self.webdriver, report_button)
                        time.sleep(random.uniform(1, 3))
                        
                        report_account_button = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS["report_account_button"])))
                        self._js_click(self.webdriver, report_account_button)
                        time.sleep(random.uniform(1, 3))

                        something_else_button = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS["something_else_button"])))
                        self._js_click(self.webdriver, something_else_button)
                        time.sleep(random.uniform(1, 3))
                        
                        for step_xpath in path_xpaths:
                           reason_element = wait.until(EC.element_to_be_clickable((By.XPATH, step_xpath)))
                           self._js_click(self.webdriver, reason_element)
                           time.sleep(random.uniform(int(self.sleep_min_var.get()), int(self.sleep_max_var.get())))

                        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, XPATHS["submit_button"])))
                        self._js_click(self.webdriver, submit_button)
                        
                        self.log(f"✅ Laporan '{path_name.upper()}' untuk URL {url} berhasil.", "OK")
                        success_count += 1; time.sleep(3)

                    except Exception as e:
                        error_msg = f"❌ Gagal lapor URL {url} jalur '{path_name.upper()}': {type(e).__name__}"
                        self.log(error_msg, "ERR")
                        fail_count += 1
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_path = os.path.join(ERROR_DIR, f"error_{ts}.png")
                        try:
                            self.webdriver.save_screenshot(screenshot_path)
                            self.log(f"Screenshot disimpan di: {screenshot_path}", "WARN")
                        except Exception as se: self.log(f"Gagal mengambil screenshot: {se}", "ERR")
                        
                        with open(ERROR_URL_FILE, "a", encoding="utf-8") as f_err: f_err.write(f"{url} - {error_msg}\n")
                            
                    finally:
                        reports_per_url += 1
                        if self.webdriver: self.webdriver.quit(); self.webdriver = None
        
        total_time = timedelta(seconds=time.time() - start_time)
        avg_time = (total_time / len(urls_to_process)) if urls_to_process else timedelta(0)
        summary = f"""
────── Summary ──────
🎯 Total URL Diproses : {len(urls_to_process)}
✅ Berhasil Dilaporkan : {success_count}
❌ Gagal Dilaporkan   : {fail_count}
🕒 Total Waktu        : {str(total_time).split('.')[0]}
⏱️ Rata-rata/URL      : {str(avg_time).split('.')[0][2:]}
"""
        self.log(summary, "SUM")
        messagebox.showinfo("Selesai", f"Tugas pelaporan selesai!\n\nBerhasil: {success_count}\nGagal: {fail_count}")
        self.bot_finished()

    def bot_finished(self):
        self.start_button.config(state="normal"); self.stop_button.config(state="disabled"); self.bot_thread = None

if __name__ == "__main__":
    app = BotGUI()
    app.mainloop()