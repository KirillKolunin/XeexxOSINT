import tkinter as tk
from tkinter import ttk, messagebox
import whois
import socket
import ipaddress
import threading
import re


# ============================================================
# XEEXX OSINT TOOL
# WHOIS / DNS LOOKUP
# ============================================================


APP_NAME = "Xeexx OSINT Tool"
VERSION = "v1.0"


# ============================================================
# УТИЛИТЫ
# ============================================================

def clean_target(target):
    """
    Очищает введённый адрес.

    Поддерживает:
    example.com
    https://example.com
    http://example.com/test
    www.example.com
    """

    if not target:
        return ""

    target = target.strip()
    target = target.lower()

    # Удаляем протокол
    target = re.sub(r"^https?://", "", target)

    # Удаляем www.
    if target.startswith("www."):
        target = target[4:]

    # Удаляем путь
    target = target.split("/")[0]

    # Удаляем порт
    target = target.split(":")[0]

    # Удаляем пробелы
    target = target.strip()

    return target


def is_ip(target):
    """
    Проверяет, является ли строка IP-адресом.
    """

    try:
        ipaddress.ip_address(target)
        return True

    except ValueError:
        return False


def safe_value(value):
    """
    Безопасно преобразует данные WHOIS.
    """

    try:

        if value is None:
            return "—"

        if isinstance(value, list):

            if not value:
                return "—"

            return "\n".join(str(x) for x in value)

        return str(value)

    except Exception:
        return "—"


def resolve_domain(domain):
    """
    Получает IP домена.
    """

    try:

        result = socket.getaddrinfo(
            domain,
            80,
            type=socket.SOCK_STREAM
        )

        ips = []

        for item in result:

            ip = item[4][0]

            if ip not in ips:
                ips.append(ip)

        return ips

    except Exception:
        return []


def reverse_dns(ip):
    """
    Reverse DNS.
    """

    try:
        hostname = socket.gethostbyaddr(ip)

        return hostname[0]

    except Exception:
        return "—"


# ============================================================
# WHOIS DOMAIN
# ============================================================

def domain_whois(domain):

    result = {
        "success": False,
        "type": "DOMAIN",
        "target": domain
    }

    try:

        data = whois.whois(domain)

    except Exception as e:

        result["error"] = (
            "WHOIS сервер не ответил.\n"
            f"{type(e).__name__}: {e}"
        )

        return result

    try:

        result["success"] = True

        result["domain"] = safe_value(
            getattr(data, "domain_name", None)
        )

        result["registrar"] = safe_value(
            getattr(data, "registrar", None)
        )

        result["creation_date"] = safe_value(
            getattr(data, "creation_date", None)
        )

        result["updated_date"] = safe_value(
            getattr(data, "updated_date", None)
        )

        result["expiration_date"] = safe_value(
            getattr(data, "expiration_date", None)
        )

        result["status"] = safe_value(
            getattr(data, "status", None)
        )

        result["name_servers"] = safe_value(
            getattr(data, "name_servers", None)
        )

        result["emails"] = safe_value(
            getattr(data, "emails", None)
        )

        result["organization"] = safe_value(
            getattr(data, "org", None)
        )

        result["country"] = safe_value(
            getattr(data, "country", None)
        )

        result["dnssec"] = safe_value(
            getattr(data, "dnssec", None)
        )

        result["raw"] = safe_value(
            getattr(data, "text", None)
        )

        # DNS
        result["ips"] = resolve_domain(domain)

        return result

    except Exception as e:

        result["success"] = False

        result["error"] = (
            "Ошибка обработки WHOIS-ответа.\n"
            f"{type(e).__name__}: {e}"
        )

        return result


# ============================================================
# WHOIS IP
# ============================================================

def ip_lookup(ip):

    result = {
        "success": True,
        "type": "IP",
        "ip": ip
    }

    try:

        hostname = reverse_dns(ip)

        result["hostname"] = hostname

    except Exception as e:

        result["hostname"] = "—"

        result["warning"] = str(e)

    return result


# ============================================================
# ОСНОВНОЙ LOOKUP
# ============================================================

def whois_lookup(target):

    target = clean_target(target)

    if not target:

        return {
            "success": False,
            "error": "Введите домен или IP-адрес."
        }

    # IP
    if is_ip(target):

        return ip_lookup(target)

    # Domain
    return domain_whois(target)


# ============================================================
# GUI
# ============================================================

class XeexxOSINT:

    def __init__(self, root):

        self.root = root

        self.root.title(
            f"{APP_NAME} {VERSION}"
        )

        self.root.geometry(
            "1050x700"
        )

        self.root.minsize(
            850,
            600
        )

        self.create_interface()


    # ========================================================
    # INTERFACE
    # ========================================================

    def create_interface(self):

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = tk.Frame(
            self.root,
            bg="#111111",
            height=80
        )

        header.pack(
            fill="x"
        )

        title = tk.Label(
            header,
            text="XEEXX OSINT TOOL",
            font=("Segoe UI", 22, "bold"),
            fg="white",
            bg="#111111"
        )

        title.pack(
            pady=(15, 0)
        )

        subtitle = tk.Label(
            header,
            text="WHOIS / DNS LOOKUP",
            font=("Segoe UI", 10),
            fg="#aaaaaa",
            bg="#111111"
        )

        subtitle.pack()


        # ----------------------------------------------------
        # SEARCH AREA
        # ----------------------------------------------------

        search_frame = tk.Frame(
            self.root,
            padx=20,
            pady=20
        )

        search_frame.pack(
            fill="x"
        )


        self.entry = tk.Entry(
            search_frame,
            font=("Segoe UI", 14)
        )

        self.entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=8
        )

        self.entry.insert(
            0,
            "example.com / 8.8.8.8"
        )


        self.lookup_button = tk.Button(
            search_frame,
            text="WHOIS LOOKUP",
            font=("Segoe UI", 11, "bold"),
            bg="#222222",
            fg="white",
            activebackground="#333333",
            activeforeground="white",
            command=self.start_lookup
        )

        self.lookup_button.pack(
            side="left",
            padx=(10, 0),
            ipadx=15,
            ipady=7
        )


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status = tk.Label(
            self.root,
            text="Ready",
            anchor="w",
            padx=20
        )

        self.status.pack(
            fill="x"
        )


        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        output_frame = tk.Frame(
            self.root,
            padx=20,
            pady=10
        )

        output_frame.pack(
            fill="both",
            expand=True
        )


        scrollbar = tk.Scrollbar(
            output_frame
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )


        self.output = tk.Text(
            output_frame,
            font=("Consolas", 10),
            wrap="word",
            yscrollcommand=scrollbar.set
        )

        self.output.pack(
            fill="both",
            expand=True
        )


        scrollbar.config(
            command=self.output.yview
        )


        # ----------------------------------------------------
        # FOOTER
        # ----------------------------------------------------

        footer = tk.Frame(
            self.root
        )

        footer.pack(
            fill="x"
        )


        made_by = tk.Label(
            footer,
            text="Made by tg:@xeexxr",
            font=("Segoe UI", 9),
            fg="#777777"
        )

        made_by.pack(
            side="left",
            padx=20,
            pady=8
        )


        version = tk.Label(
            footer,
            text=VERSION,
            font=("Segoe UI", 9),
            fg="#777777"
        )

        version.pack(
            side="right",
            padx=20
        )


        # ENTER
        self.entry.bind(
            "<Return>",
            lambda event: self.start_lookup()
        )


    # ========================================================
    # START LOOKUP
    # ========================================================

    def start_lookup(self):

        target = self.entry.get().strip()

        if not target:

            messagebox.showwarning(
                "Xeexx OSINT",
                "Введите домен или IP."
            )

            return


        # Если пользователь не заменил placeholder
        if target == "example.com / 8.8.8.8":

            messagebox.showwarning(
                "Xeexx OSINT",
                "Введите настоящий домен или IP."
            )

            return


        self.lookup_button.config(
            state="disabled"
        )

        self.status.config(
            text="Lookup in progress..."
        )

        self.output.delete(
            "1.0",
            "end"
        )

        self.output.insert(
            "end",
            "[*] Starting lookup...\n\n"
        )


        # Очень важно:
        # WHOIS выполняется в отдельном потоке,
        # чтобы GUI не зависал.

        thread = threading.Thread(
            target=self.lookup_worker,
            args=(target,),
            daemon=True
        )

        thread.start()


    # ========================================================
    # WORKER
    # ========================================================

    def lookup_worker(self, target):

        try:

            result = whois_lookup(target)

            self.root.after(
                0,
                lambda: self.show_result(result)
            )

        except Exception as e:

            self.root.after(
                0,
                lambda: self.show_error(e)
            )


    # ========================================================
    # RESULT
    # ========================================================

    def show_result(self, result):

        try:

            self.lookup_button.config(
                state="normal"
            )

            self.status.config(
                text="Lookup completed"
            )

            self.output.delete(
                "1.0",
                "end"
            )


            if not result.get("success"):

                self.output.insert(
                    "end",
                    "[ERROR]\n\n"
                )

                self.output.insert(
                    "end",
                    result.get(
                        "error",
                        "Unknown error"
                    )
                )

                return


            target_type = result.get(
                "type",
                "UNKNOWN"
            )


            self.output.insert(
                "end",
                "=" * 70 + "\n"
            )

            self.output.insert(
                "end",
                f"XEEXX OSINT TOOL | {target_type} LOOKUP\n"
            )

            self.output.insert(
                "end",
                "=" * 70 + "\n\n"
            )


            if target_type == "DOMAIN":

                self.print_field(
                    "Target",
                    result.get("target")
                )

                self.print_field(
                    "Domain",
                    result.get("domain")
                )

                self.print_field(
                    "Registrar",
                    result.get("registrar")
                )

                self.print_field(
                    "Created",
                    result.get("creation_date")
                )

                self.print_field(
                    "Updated",
                    result.get("updated_date")
                )

                self.print_field(
                    "Expires",
                    result.get("expiration_date")
                )

                self.print_field(
                    "Organization",
                    result.get("organization")
                )

                self.print_field(
                    "Country",
                    result.get("country")
                )

                self.print_field(
                    "DNSSEC",
                    result.get("dnssec")
                )


                self.output.insert(
                    "end",
                    "\n[NAME SERVERS]\n"
                )

                self.output.insert(
                    "end",
                    result.get(
                        "name_servers",
                        "—"
                    )
                )

                self.output.insert(
                    "end",
                    "\n\n[STATUS]\n"
                )

                self.output.insert(
                    "end",
                    result.get(
                        "status",
                        "—"
                    )
                )


                self.output.insert(
                    "end",
                    "\n\n[EMAILS]\n"
                )

                self.output.insert(
                    "end",
                    result.get(
                        "emails",
                        "—"
                    )
                )


                self.output.insert(
                    "end",
                    "\n\n[RESOLVED IP]\n"
                )

                ips = result.get(
                    "ips",
                    []
                )

                if ips:

                    self.output.insert(
                        "end",
                        "\n".join(ips)
                    )

                else:

                    self.output.insert(
                        "end",
                        "—"
                    )


                self.output.insert(
                    "end",
                    "\n\n[RAW WHOIS]\n"
                )

                self.output.insert(
                    "end",
                    result.get(
                        "raw",
                        "—"
                    )
                )


            elif target_type == "IP":

                self.print_field(
                    "IP",
                    result.get("ip")
                )

                self.print_field(
                    "Reverse DNS",
                    result.get("hostname")
                )


            self.output.insert(
                "end",
                "\n\n" + "=" * 70
            )


        except Exception as e:

            self.show_error(e)


    # ========================================================
    # PRINT FIELD
    # ========================================================

    def print_field(self, name, value):

        self.output.insert(
            "end",
            f"{name:<20}: {value}\n"
        )


    # ========================================================
    # ERROR
    # ========================================================

    def show_error(self, error):

        try:

            self.lookup_button.config(
                state="normal"
            )

            self.status.config(
                text="Error"
            )

            self.output.insert(
                "end",
                "\n\n"
                "[CRITICAL ERROR]\n"
                "-------------------------\n"
            )

            self.output.insert(
                "end",
                f"{type(error).__name__}: {error}\n"
            )

        except Exception:
            pass


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        root = tk.Tk()

        app = XeexxOSINT(root)

        root.mainloop()

    except Exception as e:

        messagebox.showerror(
            "Xeexx OSINT Tool",
            f"Fatal error:\n\n{e}"
        )


if __name__ == "__main__":
    main()