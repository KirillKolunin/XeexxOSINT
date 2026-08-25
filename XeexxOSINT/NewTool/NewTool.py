import json
import re
import socket
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
 
try:
    import requests
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False
 
APP_NAME = "XEEXX"
APP_AUTHOR = "made by @xeexxr"
 
BANNER = r"""
██╗  ██╗███████╗███████╗██╗  ██╗██╗  ██╗
╚██╗██╔╝██╔════╝██╔════╝╚██╗██╔╝╚██╗██╔╝
 ╚███╔╝ █████╗  █████╗   ╚███╔╝  ╚███╔╝
 ██╔██╗ ██╔══╝  ██╔══╝   ██╔██╗  ██╔██╗
██╔╝ ██╗███████╗███████╗██╔╝ ██╗██╔╝ ██╗
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
        Legitimate OSINT Toolkit
"""
 
# ---------------------------------------------------------------------------
# Username check: public profile URLs only. A hit just means "a public page
# at this URL responds"; it does not confirm identity or reveal private data.
# ---------------------------------------------------------------------------
USERNAME_SITES = {
    "GitHub":     "https://github.com/{u}",
    "GitLab":     "https://gitlab.com/{u}",
    "Reddit":     "https://www.reddit.com/user/{u}/about.json",
    "X (Twitter)": "https://x.com/{u}",
    "Instagram":  "https://www.instagram.com/{u}/",
    "TikTok":     "https://www.tiktok.com/@{u}",
    "Telegram":   "https://t.me/{u}",
    "Steam":      "https://steamcommunity.com/id/{u}",
    "Twitch":     "https://www.twitch.tv/{u}",
    "Medium":     "https://medium.com/@{u}",
    "DevTo":      "https://dev.to/{u}",
    "HackerNews": "https://news.ycombinator.com/user?id={u}",
    "Keybase":    "https://keybase.io/{u}",
    "Pinterest":  "https://www.pinterest.com/{u}/",
    "Facebook":   "https://www.facebook.com/{u}",
}
 
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; XEEXX-OSINT/1.0)"}
 
 
def check_username_site(site, url_template, username, timeout=6):
    url = url_template.format(u=username)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if site == "Reddit":
            found = resp.status_code == 200 and '"name"' in resp.text
        else:
            found = resp.status_code == 200
        return site, url, found, resp.status_code
    except requests.RequestException as e:
        return site, url, None, str(e)
 
 
# ---------------------------------------------------------------------------
# WHOIS: raw socket client against the standard WHOIS protocol (port 43).
# Starts at IANA's root server and follows the "refer" to the authoritative
# registry WHOIS server, same as any public `whois` command line client.
# ---------------------------------------------------------------------------
def whois_query(server, query, timeout=10):
    with socket.create_connection((server, 43), timeout=timeout) as s:
        s.sendall((query + "\r\n").encode())
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
    return b"".join(chunks).decode(errors="replace")
 
 
def whois_lookup(domain):
    domain = domain.strip().lower()
    try:
        iana = whois_query("whois.iana.org", domain)
    except Exception as e:
        return f"Error contacting whois.iana.org: {e}"
 
    refer_server = None
    for line in iana.splitlines():
        if line.lower().startswith("refer:"):
            refer_server = line.split(":", 1)[1].strip()
            break
 
    if not refer_server:
        return iana or "No WHOIS data found."
 
    try:
        result = whois_query(refer_server, domain)
        return result
    except Exception as e:
        return f"IANA referred to {refer_server}, but query failed: {e}\n\n--- IANA response ---\n{iana}"
 
 
# ---------------------------------------------------------------------------
# IP Geolocation: public, keyless API (ip-api.com) - no auth, no scraping.
# ---------------------------------------------------------------------------
def ip_lookup(ip_or_host):
    url = f"http://ip-api.com/json/{ip_or_host}?fields=status,message,query,country,regionName,city,zip,lat,lon,isp,org,as,timezone,reverse,proxy,hosting"
    resp = requests.get(url, timeout=8)
    data = resp.json()
    return data
 
 
# ---------------------------------------------------------------------------
# Email validator: syntax check + domain resolvability + best-effort mail
# server reachability. No password/breach checking of any kind.
# ---------------------------------------------------------------------------
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
 
 
def email_check(email):
    lines = []
    email = email.strip()
    if not EMAIL_RE.match(email):
        return "Invalid email syntax."
 
    domain = email.split("@", 1)[1]
    lines.append(f"Syntax: valid")
    lines.append(f"Domain: {domain}")
 
    try:
        addr_info = socket.getaddrinfo(domain, None)
        ips = sorted(set(ai[4][0] for ai in addr_info))
        lines.append(f"Domain resolves: yes ({', '.join(ips)})")
    except socket.gaierror:
        lines.append("Domain resolves: NO — domain does not exist or has no DNS record")
        return "\n".join(lines)
 
    # Best-effort: try common mail port to see if a mail service answers.
    mail_open = False
    for port in (25, 587):
        try:
            with socket.create_connection((domain, port), timeout=4):
                mail_open = True
                break
        except OSError:
            continue
    lines.append(f"Mail port reachable (25/587): {'yes' if mail_open else 'no / blocked / not checked via MX'}")
    lines.append("\nNote: this only checks domain/DNS reachability, not whether the")
    lines.append("mailbox exists or has ever been used. No breach databases are queried.")
    return "\n".join(lines)
 
 
# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class XeexxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — OSINT Toolkit")
        self.geometry("880x640")
        self.configure(bg="#0d1117")
        self._build_header()
        self._build_tabs()
 
    def _build_header(self):
        header = tk.Frame(self, bg="#0d1117")
        header.pack(fill="x", pady=(8, 0))
        banner_lbl = tk.Label(
            header, text=BANNER, font=("Courier", 9), fg="#39ff88", bg="#0d1117", justify="left"
        )
        banner_lbl.pack()
        author_lbl = tk.Label(
            header, text=APP_AUTHOR, font=("Segoe UI", 10, "italic"), fg="#8b949e", bg="#0d1117"
        )
        author_lbl.pack(pady=(0, 6))
        disclaimer = tk.Label(
            header,
            text="Public-source OSINT only — no leaked databases, no private data access.",
            font=("Segoe UI", 9), fg="#f0883e", bg="#0d1117"
        )
        disclaimer.pack(pady=(0, 6))
 
    def _build_tabs(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background="#0d1117", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 6))
 
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
 
        self.tab_username = tk.Frame(nb, bg="#161b22")
        self.tab_whois = tk.Frame(nb, bg="#161b22")
        self.tab_ip = tk.Frame(nb, bg="#161b22")
        self.tab_email = tk.Frame(nb, bg="#161b22")
 
        nb.add(self.tab_username, text="Username Search")
        nb.add(self.tab_whois, text="Domain WHOIS")
        nb.add(self.tab_ip, text="IP Geolocation")
        nb.add(self.tab_email, text="Email Check")
 
        self._build_username_tab()
        self._build_whois_tab()
        self._build_ip_tab()
        self._build_email_tab()
 
    # ---- shared helpers -----------------------------------------------
    def _entry_row(self, parent, label_text):
        row = tk.Frame(parent, bg="#161b22")
        row.pack(fill="x", padx=16, pady=(16, 6))
        tk.Label(row, text=label_text, fg="#c9d1d9", bg="#161b22", font=("Segoe UI", 10)).pack(side="left")
        entry = tk.Entry(row, font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True, padx=8)
        return entry
 
    def _output_box(self, parent):
        box = scrolledtext.ScrolledText(
            parent, font=("Consolas", 10), bg="#0d1117", fg="#c9d1d9",
            insertbackground="#c9d1d9", wrap="word"
        )
        box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        return box
 
    def _run_async(self, fn):
        threading.Thread(target=fn, daemon=True).start()
 
    # ---- Username tab ---------------------------------------------------
    def _build_username_tab(self):
        self.username_entry = self._entry_row(self.tab_username, "Username:")
        btn = tk.Button(
            self.tab_username, text="Search", command=self._on_username_search,
            bg="#238636", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=4
        )
        btn.pack(anchor="w", padx=16)
        self.username_output = self._output_box(self.tab_username)
 
    def _on_username_search(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning(APP_NAME, "Enter a username first.")
            return
        if not HAVE_REQUESTS:
            messagebox.showerror(APP_NAME, "The 'requests' library is not installed.\nRun: pip install requests")
            return
 
        self.username_output.delete("1.0", tk.END)
        self.username_output.insert(tk.END, f"Checking '{username}' across {len(USERNAME_SITES)} platforms...\n\n")
 
        def worker():
            for site, tmpl in USERNAME_SITES.items():
                site_r, url, found, status = check_username_site(site, tmpl, username)
                if found is True:
                    line = f"[FOUND]   {site_r:<12} {url}\n"
                elif found is False:
                    line = f"[-----]   {site_r:<12} (HTTP {status})\n"
                else:
                    line = f"[ERROR]   {site_r:<12} {status}\n"
                self.username_output.insert(tk.END, line)
                self.username_output.see(tk.END)
 
        self._run_async(worker)
 
    # ---- WHOIS tab -------------------------------------------------------
    def _build_whois_tab(self):
        self.whois_entry = self._entry_row(self.tab_whois, "Domain:")
        btn = tk.Button(
            self.tab_whois, text="Lookup", command=self._on_whois_lookup,
            bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=4
        )
        btn.pack(anchor="w", padx=16)
        self.whois_output = self._output_box(self.tab_whois)
 
    def _on_whois_lookup(self):
        domain = self.whois_entry.get().strip()
        if not domain:
            messagebox.showwarning(APP_NAME, "Enter a domain first.")
            return
        self.whois_output.delete("1.0", tk.END)
        self.whois_output.insert(tk.END, f"Querying WHOIS for {domain}...\n\n")
 
        def worker():
            result = whois_lookup(domain)
            self.whois_output.insert(tk.END, result)
 
        self._run_async(worker)
 
    # ---- IP tab ------------------------------------------------------
    def _build_ip_tab(self):
        self.ip_entry = self._entry_row(self.tab_ip, "IP or hostname:")
        btn = tk.Button(
            self.tab_ip, text="Lookup", command=self._on_ip_lookup,
            bg="#1f6feb", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=4
        )
        btn.pack(anchor="w", padx=16)
        self.ip_output = self._output_box(self.tab_ip)
 
    def _on_ip_lookup(self):
        target = self.ip_entry.get().strip()
        if not target:
            messagebox.showwarning(APP_NAME, "Enter an IP address or hostname first.")
            return
        if not HAVE_REQUESTS:
            messagebox.showerror(APP_NAME, "The 'requests' library is not installed.\nRun: pip install requests")
            return
 
        self.ip_output.delete("1.0", tk.END)
        self.ip_output.insert(tk.END, f"Looking up {target}...\n\n")
 
        def worker():
            try:
                data = ip_lookup(target)
                if data.get("status") == "fail":
                    self.ip_output.insert(tk.END, f"Lookup failed: {data.get('message')}")
                else:
                    self.ip_output.insert(tk.END, json.dumps(data, indent=2, ensure_ascii=False))
            except Exception as e:
                self.ip_output.insert(tk.END, f"Error: {e}")
 
        self._run_async(worker)
 
    # ---- Email tab ---------------------------------------------------
    def _build_email_tab(self):
        self.email_entry = self._entry_row(self.tab_email, "Email address:")
        btn = tk.Button(
            self.tab_email, text="Check", command=self._on_email_check,
            bg="#8957e5", fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=4
        )
        btn.pack(anchor="w", padx=16)
        self.email_output = self._output_box(self.tab_email)
 
    def _on_email_check(self):
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showwarning(APP_NAME, "Enter an email address first.")
            return
        self.email_output.delete("1.0", tk.END)
 
        def worker():
            result = email_check(email)
            self.email_output.insert(tk.END, result)
 
        self._run_async(worker)
 
 
if __name__ == "__main__":
    app = XeexxApp()
    app.mainloop()
 