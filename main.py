import json
import requests
import time
import schedule
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

APP_VERSION = "0.1.0"
VERSION_FILE = Path(__file__).resolve().parent / "version.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}


def load_version():
    if VERSION_FILE.exists():
        try:
            return VERSION_FILE.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    return APP_VERSION


def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def get_price(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        price_elem = soup.find('span', {'class': 'a-price-whole'})
        if price_elem:
            whole = price_elem.text.strip()
            fraction_elem = soup.find('span', {'class': 'a-price-fraction'})
            fraction = fraction_elem.text.strip() if fraction_elem else '00'
            price_str = f"{whole}.{fraction}"
            return float(price_str.replace(',', ''))

        return None
    except Exception as e:
        return str(e)


def get_search_urls(query, max_results=5):
    """Use Selenium to scrape Amazon search results (bypasses anti-bot detection)"""
    encoded_query = requests.utils.quote(query)
    search_url = f"https://www.amazon.com/s?k={encoded_query}"
    
    driver = None
    try:
        # Configure Chrome options for headless browsing
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"user-agent={HEADERS['User-Agent']}")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print(f"Opening Amazon search for '{query}'...")
        driver.get(search_url)
        
        # Wait longer and try multiple selectors
        time.sleep(3)
        
        # Scroll down to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        results = []
        
        # Find search result items
        items = soup.find_all('div', {'data-component-type': 's-search-result'})
        
        if not items:
            items = soup.find_all('div', {'class': lambda x: x and 's-result-item' in x})
        
        if not items:
            print(f"  No items found for query '{query}'")
            return []
        
        for idx, item in enumerate(items):
            try:
                # Method 1: Look for h2 > a
                href = None
                title_link = item.find('h2')
                if title_link:
                    anchor = title_link.find('a', href=True)
                    if anchor:
                        href = anchor.get('href')
                
                # Method 2: If not found, look for any a tag in the item with /dp/
                if not href:
                    all_anchors = item.find_all('a', href=True)
                    for anchor in all_anchors:
                        potential_href = anchor.get('href', '')
                        if '/dp/' in potential_href:
                            href = potential_href
                            break
                
                if not href:
                    continue
                
                # Normalize href
                if href.startswith('/'):
                    href = 'https://www.amazon.com' + href.split('?')[0]
                elif not href.startswith('https'):
                    continue
                
                if href not in results and '/dp/' in href:
                    results.append(href)
                
                if len(results) >= max_results:
                    break
            except Exception as e:
                continue
        
        print(f"  Total products found for '{query}': {len(results)}")
        return results
        
    except Exception as e:
        print(f"Search error for '{query}': {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

class PriceMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Amazon PC Parts Price Monitor")
        self.geometry("750x700")
        self.configure(bg="#1e1e1e")
        
        # Define colors and fonts
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#00EEFF"
        self.frame_bg = "#2d2d2d"
        self.button_bg = "#00EEFF"
        self.button_hover = "#00EEFF"
        
        self.title_font = ("Segoe UI", 16, "bold")
        self.label_font = ("Segoe UI", 10, "bold")
        self.text_font = ("Segoe UI", 9)
        
        # Configure style
        self.configure(bg=self.bg_color)
        
        # Main title
        self.version = load_version()
        self.title(f"Amazon PC Parts Price Monitor v{self.version}")

        title_frame = tk.Frame(self, bg=self.accent_color, height=60)
        title_frame.pack(fill=tk.X, padx=0, pady=0)
        title_label = tk.Label(title_frame, text="🔍 Amazon PC Parts Monitor", font=self.title_font, 
                              bg=self.accent_color, fg="#000000", pady=15)
        title_label.pack(side=tk.LEFT, padx=(10, 0), pady=5)

        version_label = tk.Label(title_frame, text=f"v{self.version}", font=("Segoe UI", 10),
                                 bg=self.accent_color, fg="#000000")
        version_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Main content frame
        content_frame = tk.Frame(self, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Webhook section
        webhook_frame = tk.LabelFrame(content_frame, text="🔗 Discord Webhook", font=self.label_font,
                                      bg=self.frame_bg, fg=self.fg_color, padx=10, pady=10)
        webhook_frame.pack(fill=tk.X, pady=10)
        self.webhook_entry = tk.Entry(webhook_frame, width=90, font=self.text_font, bg="#3d3d3d", fg=self.fg_color, insertbackground=self.fg_color)
        self.webhook_entry.pack(fill=tk.X, pady=5)
        
        # Queries section
        queries_frame = tk.LabelFrame(content_frame, text="🔎 Search Queries", font=self.label_font,
                                     bg=self.frame_bg, fg=self.fg_color, padx=10, pady=10)
        queries_frame.pack(fill=tk.X, pady=10)
        self.queries_text = tk.Text(queries_frame, height=6, width=90, font=self.text_font, bg="#3d3d3d", fg=self.fg_color, insertbackground=self.fg_color)
        self.queries_text.pack(fill=tk.BOTH, expand=True, pady=5)
        self.queries_text.insert(tk.END, "pc parts\ncpu\ngpu\nmotherboard\nram\nssd\npsu\ncase\ncooler")
        
        # Settings section
        settings_frame = tk.LabelFrame(content_frame, text="⚙️ Settings", font=self.label_font,
                                      bg=self.frame_bg, fg=self.fg_color, padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        settings_inner = tk.Frame(settings_frame, bg=self.frame_bg)
        settings_inner.pack(fill=tk.X)
        
        # Max results
        tk.Label(settings_inner, text="Max Products per Query:", font=self.label_font, bg=self.frame_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=5)
        self.max_results_entry = tk.Entry(settings_inner, width=5, font=self.text_font, bg="#3d3d3d", fg=self.fg_color, insertbackground=self.fg_color)
        self.max_results_entry.insert(0, "5")
        self.max_results_entry.pack(side=tk.LEFT, padx=5)
        
        # Check interval
        tk.Label(settings_inner, text="Check Interval (min):", font=self.label_font, bg=self.frame_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=5)
        self.interval_entry = tk.Entry(settings_inner, width=5, font=self.text_font, bg="#3d3d3d", fg=self.fg_color, insertbackground=self.fg_color)
        self.interval_entry.insert(0, "60")
        self.interval_entry.pack(side=tk.LEFT, padx=5)
        
        self.load_config_values()
        
        # Buttons frame
        button_frame = tk.Frame(content_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = tk.Button(button_frame, text="▶ Start Monitoring", command=self.start_monitoring,
                                  font=self.label_font, bg=self.button_bg, fg="#000000", 
                                  padx=15, pady=10, relief=tk.FLAT, cursor="hand2")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(button_frame, text="⏹ Stop Monitoring", command=self.stop_monitoring,
                                 font=self.label_font, bg="#555555", fg=self.fg_color,
                                 padx=15, pady=10, relief=tk.FLAT, cursor="hand2", state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.test_btn = tk.Button(button_frame, text="📨 Test Webhook", command=self.test_webhook,
                                 font=self.label_font, bg="#0078D4", fg=self.fg_color,
                                 padx=15, pady=10, relief=tk.FLAT, cursor="hand2")
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        # Log section
        log_frame = tk.LabelFrame(content_frame, text="📋 Log", font=self.label_font,
                                 bg=self.frame_bg, fg=self.fg_color, padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, width=90, font=self.text_font, 
                               bg="#0d0d0d", fg="#00FF00", insertbackground=self.fg_color,
                               relief=tk.SUNKEN, bd=2)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self.monitoring = False
        self.prices = {}
        self.scheduler_thread = None

    def load_config_values(self):
        config = load_config()
        if not config:
            return

        webhook = config.get('webhook_url')
        if webhook:
            self.webhook_entry.insert(0, webhook)

        queries = config.get('queries')
        if queries and isinstance(queries, list):
            self.queries_text.delete('1.0', tk.END)
            self.queries_text.insert(tk.END, '\n'.join(queries))

        max_results = config.get('max_results')
        if isinstance(max_results, int):
            self.max_results_entry.delete(0, tk.END)
            self.max_results_entry.insert(0, str(max_results))

        interval = config.get('check_interval_minutes')
        if isinstance(interval, int):
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, str(interval))

    def test_webhook(self):
        webhook_url = self.webhook_entry.get().strip()
        if not webhook_url:
            messagebox.showerror("Error", "Please enter a Discord Webhook URL first.")
            return
        
        try:
            self.log("Testing Discord webhook...")
            message = "🧪 **Test Message** - Amazon Price Monitor is working!"
            webhook = DiscordWebhook(url=webhook_url, content=message)
            webhook.execute()
            self.log("✓ Test message sent successfully!")
            messagebox.showinfo("Success", "Test message sent to Discord!")
        except Exception as e:
            self.log(f"✗ Failed to send test message: {e}")
            messagebox.showerror("Error", f"Failed to send test message:\n{e}")

    def log(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def start_monitoring(self):
        webhook = self.webhook_entry.get().strip()
        queries_text = self.queries_text.get("1.0", tk.END).strip()
        queries = [q.strip() for q in queries_text.split("\n") if q.strip()]
        try:
            interval = int(self.interval_entry.get())
            max_results = int(self.max_results_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid number value. Enter valid integers.")
            return

        if not webhook:
            messagebox.showerror("Error", "Enter Discord Webhook URL.")
            return
        if not queries:
            messagebox.showerror("Error", "Enter at least one search query.")
            return

        self.config = {
            "webhook_url": webhook,
            "queries": queries,
            "check_interval_minutes": interval,
            "max_results": max_results,
        }
        self.monitoring = True
        self.start_btn.config(state=tk.DISABLED, bg="#555555")
        self.stop_btn.config(state=tk.NORMAL, bg="#FF0000")
        self.test_btn.config(state=tk.DISABLED)
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()
        self.log("Monitoring started")
        
    def stop_monitoring(self):
        self.monitoring = False
        self.start_btn.config(state=tk.NORMAL, bg=self.button_bg)
        self.stop_btn.config(state=tk.DISABLED, bg="#555555")
        self.test_btn.config(state=tk.NORMAL)
        self.log("Monitoring stopped")
        
    def run_scheduler(self):
        schedule.clear()
        schedule.every(self.config['check_interval_minutes']).minutes.do(self.check_prices)
        self.check_prices()  # Initial check
        while self.monitoring:
            schedule.run_pending()
            time.sleep(1)
            
    def check_prices(self):
        search_urls = []
        for query in self.config['queries']:
            urls = get_search_urls(query, self.config['max_results'])
            self.log(f"Found {len(urls)} products for query: {query}")
            search_urls.extend(urls)
            # Add delay between queries
            time.sleep(random.uniform(1, 3))

        unique_urls = list(dict.fromkeys(search_urls))
        self.log(f"Monitoring {len(unique_urls)} unique product URLs.")

        for url in unique_urls:
            price_result = get_price(url)
            if isinstance(price_result, str):
                self.log(f"Error getting price for {url}: {price_result}")
                continue
            
            if price_result is None:
                self.log(f"Could not find price for {url}")
                continue
            
            current_price = price_result
            previous_price = self.prices.get(url)
            if previous_price is None:
                self.prices[url] = current_price
                self.log(f"Started monitoring {url} at ${current_price:.2f}")
                try:
                    message = f"Started monitoring {url} at ${current_price:.2f}"
                    webhook = DiscordWebhook(url=self.config['webhook_url'], content=message)
                    webhook.execute()
                except Exception as e:
                    self.log(f"Failed to send initial webhook: {e}")
            elif current_price != previous_price:
                change_type = "dropped" if current_price < previous_price else "increased"
                difference = abs(current_price - previous_price)
                message = f"Price {change_type} for {url}: from ${previous_price:.2f} to ${current_price:.2f} (change: ${difference:.2f})"
                self.log(message)
                try:
                    webhook = DiscordWebhook(url=self.config['webhook_url'], content=message)
                    webhook.execute()
                except Exception as e:
                    self.log(f"Failed to send webhook: {e}")
                self.prices[url] = current_price

if __name__ == "__main__":
    app = PriceMonitorApp()
    app.mainloop()