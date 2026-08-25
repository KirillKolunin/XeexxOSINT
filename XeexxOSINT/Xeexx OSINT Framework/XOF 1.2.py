import re
import socket
import hashlib
import threading
import ipaddress

import requests
import dns.resolver
import dns.reversename
import whois
import phonenumbers

from phonenumbers import (
    geocoder,
    carrier,
    timezone,
    PhoneNumberType
)

import tkinter as tk
from tkinter import messagebox


# =========================================================
# XEEXX OSINT
# =========================================================

APP_NAME = "XEEXX OSINT"
VERSION = "v1.2"

BG = "#080B10"
SIDEBAR = "#0D1118"
CARD = "#111720"
CARD_2 = "#151C26"
BORDER = "#202A36"

TEXT = "#F2F5F8"
TEXT_SECONDARY = "#8D99A8"

ACCENT = "#6C63FF"
ACCENT_HOVER = "#8179FF"

GREEN = "#35D07F"
RED = "#FF5C70"
YELLOW = "#F5C451"


# =========================================================
# HELPERS
# =========================================================

def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def valid_email(email):
    pattern = (
        r"^[a-zA-Z0-9._%+-]+"
        r"@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    return bool(re.match(pattern, email))


# =========================================================
# PHONE NUMBER TYPE
# =========================================================

def phone_type_name(number_type):

    types = {
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.FIXED_LINE: "Fixed line",
        PhoneNumberType.FIXED_LINE_OR_MOBILE:
            "Fixed line / Mobile",
        PhoneNumberType.TOLL_FREE: "Toll free",
        PhoneNumberType.PREMIUM_RATE: "Premium rate",
        PhoneNumberType.SHARED_COST: "Shared cost",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.PERSONAL_NUMBER:
            "Personal number",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "Voicemail",
        PhoneNumberType.UNKNOWN: "Unknown"
    }

    return types.get(
        number_type,
        "Unknown"
    )


# =========================================================
# PHONE LOOKUP
# =========================================================

def phone_lookup(phone):

    phone = phone.strip()

    result = {
        "status": False,
        "message": "",
        "input": phone,
        "international": "-",
        "national": "-",
        "country": "-",
        "country_code": "-",
        "region": "-",
        "carrier": "-",
        "timezone": "-",
        "number_type": "-",
        "possible": False,
        "valid": False
    }

    if not phone:

        result["message"] = "Введите номер телефона"

        return result

    try:

        # -------------------------------------------------
        # Если номер начинается с +,
        # страна определяется автоматически.
        #
        # Для номеров без + используется RU как пример.
        # Можно изменить на нужный ISO-код.
        # -------------------------------------------------

        if phone.startswith("+"):

            parsed = phonenumbers.parse(
                phone,
                None
            )

        else:

            # По умолчанию RU.
            # Пользователь может вводить +код страны
            # для автоматического определения.
            parsed = phonenumbers.parse(
                phone,
                "RU"
            )

        # -------------------------------------------------
        # Возможность существования номера
        # -------------------------------------------------

        result["possible"] = (
            phonenumbers.is_possible_number(
                parsed
            )
        )

        # -------------------------------------------------
        # Валидность
        # -------------------------------------------------

        result["valid"] = (
            phonenumbers.is_valid_number(
                parsed
            )
        )

        # -------------------------------------------------
        # Международный формат
        # -------------------------------------------------

        result["international"] = (
            phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
        )

        # -------------------------------------------------
        # Национальный формат
        # -------------------------------------------------

        result["national"] = (
            phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.NATIONAL
            )
        )

        # -------------------------------------------------
        # Country code
        # -------------------------------------------------

        result["country_code"] = (
            "+" + str(
                parsed.country_code
            )
        )

        # -------------------------------------------------
        # Country
        # -------------------------------------------------

        country = geocoder.country_name_for_number(
            parsed,
            "en"
        )

        result["country"] = (
            country
            if country
            else "Unknown"
        )

        # -------------------------------------------------
        # Region
        # -------------------------------------------------

        region = geocoder.description_for_number(
            parsed,
            "en"
        )

        result["region"] = (
            region
            if region
            else "Unknown"
        )

        # -------------------------------------------------
        # Carrier
        # -------------------------------------------------

        operator = carrier.name_for_number(
            parsed,
            "en"
        )

        result["carrier"] = (
            operator
            if operator
            else "Unknown"
        )

        # -------------------------------------------------
        # Timezone
        # -------------------------------------------------

        zones = timezone.time_zones_for_number(
            parsed
        )

        if zones:

            result["timezone"] = "\n".join(
                zones
            )

        # -------------------------------------------------
        # Number type
        # -------------------------------------------------

        number_type = phonenumbers.number_type(
            parsed
        )

        result["number_type"] = (
            phone_type_name(
                number_type
            )
        )

        # -------------------------------------------------
        # Final status
        # -------------------------------------------------

        result["status"] = True

        if result["valid"]:

            result["message"] = (
                "Номер прошёл проверку"
            )

        elif result["possible"]:

            result["message"] = (
                "Номер имеет возможный формат, "
                "но не подтверждён как действительный"
            )

        else:

            result["message"] = (
                "Номер имеет некорректный формат"
            )

    except phonenumbers.NumberParseException as error:

        result["message"] = (
            f"Ошибка разбора номера: {error}"
        )

    except Exception as error:

        result["message"] = (
            f"Ошибка Phone Lookup: {error}"
        )

    return result


# =========================================================
# GMAIL LOOKUP
# =========================================================

def gmail_lookup(email):

    email = email.strip().lower()

    result = {
        "status": False,
        "message": "",
        "email": email,
        "domain": "-",
        "ip": "-",
        "mx": [],
        "gravatar": "Не найден"
    }

    if not valid_email(email):

        result["message"] = (
            "Некорректный формат email"
        )

        return result

    _, domain = email.split("@", 1)

    result["domain"] = domain

    if domain not in (
        "gmail.com",
        "googlemail.com"
    ):

        result["message"] = (
            "Это не Gmail-адрес"
        )

        return result

    result["status"] = True

    result["message"] = (
        "Корректный Gmail-адрес"
    )

    # IP
    try:

        result["ip"] = socket.gethostbyname(
            domain
        )

    except Exception:

        result["ip"] = "Не удалось определить"

    # MX
    try:

        resolver = dns.resolver.Resolver()

        answers = resolver.resolve(
            domain,
            "MX"
        )

        result["mx"] = sorted([
            f"{answer.preference} "
            f"{str(answer.exchange).rstrip('.')}"
            for answer in answers
        ])

    except Exception:

        result["mx"] = []

    # Gravatar
    try:

        email_hash = hashlib.md5(
            email.encode("utf-8")
        ).hexdigest()

        url = (
            "https://www.gravatar.com/avatar/"
            + email_hash
            + "?d=404"
        )

        response = requests.get(
            url,
            timeout=7,
            headers={
                "User-Agent": "Xeexx-OSINT/1.2"
            }
        )

        if response.status_code == 200:

            result["gravatar"] = (
                "Публичный профиль найден"
            )

        else:

            result["gravatar"] = "Не найден"

    except Exception:

        result["gravatar"] = (
            "Ошибка проверки"
        )

    return result


# =========================================================
# IP LOOKUP
# =========================================================

def ip_lookup(target):

    target = target.strip()

    result = {
        "status": False,
        "message": "",
        "target": target,
        "ip": "-",
        "hostname": "-",
        "version": "-",
        "reverse_dns": "-"
    }

    try:

        if is_ip(target):

            ip = target

        else:

            ip = socket.gethostbyname(
                target
            )

        result["ip"] = ip

        ip_obj = ipaddress.ip_address(
            ip
        )

        result["version"] = (
            "IPv4"
            if ip_obj.version == 4
            else "IPv6"
        )

        try:

            hostname = socket.gethostbyaddr(
                ip
            )[0]

            result["hostname"] = hostname
            result["reverse_dns"] = hostname

        except Exception:

            result["hostname"] = "Не найден"
            result["reverse_dns"] = "Не найден"

        result["status"] = True

        result["message"] = (
            "IP успешно определён"
        )

    except Exception as error:

        result["message"] = (
            f"Не удалось определить IP: {error}"
        )

    return result


# =========================================================
# DNS LOOKUP
# =========================================================

def dns_lookup(target):

    target = target.strip()

    result = {
        "status": False,
        "message": "",
        "target": target,
        "type": (
            "IP"
            if is_ip(target)
            else "DOMAIN"
        ),
        "A": [],
        "AAAA": [],
        "MX": [],
        "NS": [],
        "TXT": [],
        "CNAME": [],
        "PTR": []
    }

    if not target:

        result["message"] = (
            "Пустой запрос"
        )

        return result

    resolver = dns.resolver.Resolver()

    # -----------------------------------------------------
    # IP -> PTR
    # -----------------------------------------------------

    if is_ip(target):

        try:

            reverse_name = (
                dns.reversename.from_address(
                    target
                )
            )

            answers = resolver.resolve(
                reverse_name,
                "PTR"
            )

            result["PTR"] = [
                str(answer).rstrip(".")
                for answer in answers
            ]

            result["status"] = True

            result["message"] = (
                "Reverse DNS выполнен"
            )

        except Exception:

            result["message"] = (
                "PTR-запись не найдена"
            )

        return result

    # -----------------------------------------------------
    # DOMAIN
    # -----------------------------------------------------

    record_types = [
        "A",
        "AAAA",
        "MX",
        "NS",
        "TXT",
        "CNAME"
    ]

    found_any = False

    for record_type in record_types:

        try:

            answers = resolver.resolve(
                target,
                record_type
            )

            found_any = True

            for answer in answers:

                if record_type == "MX":

                    value = (
                        f"{answer.preference} "
                        f"{str(answer.exchange).rstrip('.')}"
                    )

                else:

                    value = str(
                        answer
                    ).rstrip(".")

                result[
                    record_type
                ].append(
                    value
                )

        except Exception:

            pass

    if found_any:

        result["status"] = True

        result["message"] = (
            "DNS lookup завершён"
        )

    else:

        result["message"] = (
            "DNS-записи не найдены"
        )

    return result


# =========================================================
# WHOIS LOOKUP
# =========================================================

def whois_lookup(target):

    target = target.strip()

    result = {
        "status": False,
        "message": "",
        "domain": target,
        "registrar": "-",
        "creation": "-",
        "expiration": "-",
        "updated": "-",
        "name_servers": [],
        "status_info": [],
        "emails": [],
        "organization": "-"
    }

    if not target:

        result["message"] = (
            "Введите домен"
        )

        return result

    target = re.sub(
        r"^https?://",
        "",
        target,
        flags=re.IGNORECASE
    )

    target = target.split("/")[0]
    target = target.split(":")[0]

    result["domain"] = target

    try:

        data = whois.whois(
            target
        )

        if not data:

            result["message"] = (
                "WHOIS не вернул данные"
            )

            return result

        result["status"] = True

        result["message"] = (
            "WHOIS lookup завершён"
        )

        if data.registrar:

            result["registrar"] = str(
                data.registrar
            )

        if data.creation_date:

            result["creation"] = str(
                data.creation_date
            )

        if data.expiration_date:

            result["expiration"] = str(
                data.expiration_date
            )

        if data.updated_date:

            result["updated"] = str(
                data.updated_date
            )

        if data.name_servers:

            if isinstance(
                data.name_servers,
                (list, tuple)
            ):

                result["name_servers"] = [
                    str(x)
                    for x in data.name_servers
                ]

            else:

                result["name_servers"] = [
                    str(data.name_servers)
                ]

        if data.status:

            if isinstance(
                data.status,
                (list, tuple)
            ):

                result["status_info"] = [
                    str(x)
                    for x in data.status
                ]

            else:

                result["status_info"] = [
                    str(data.status)
                ]

        if data.emails:

            if isinstance(
                data.emails,
                (list, tuple)
            ):

                result["emails"] = [
                    str(x)
                    for x in data.emails
                ]

            else:

                result["emails"] = [
                    str(data.emails)
                ]

        organization = getattr(
            data,
            "org",
            None
        )

        if organization:

            result["organization"] = str(
                organization
            )

    except Exception as error:

        result["message"] = (
            f"WHOIS ошибка: {error}"
        )

    return result


# =========================================================
# GUI
# =========================================================

class XeexxOSINT:

    def __init__(self, root):

        self.root = root

        self.root.title(
            f"{APP_NAME} {VERSION}"
        )

        self.root.geometry(
            "1150x720"
        )

        self.root.minsize(
            950,
            620
        )

        self.root.configure(
            bg=BG
        )

        self.current_module = "gmail"

        self.root.grid_columnconfigure(
            1,
            weight=1
        )

        self.root.grid_rowconfigure(
            0,
            weight=1
        )

        self.create_sidebar()
        self.create_main()

    # =====================================================
    # SIDEBAR
    # =====================================================

    def create_sidebar(self):

        self.sidebar = tk.Frame(
            self.root,
            bg=SIDEBAR,
            width=235
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.sidebar.grid_propagate(
            False
        )

        tk.Label(
            self.sidebar,
            text="XEEXX",
            font=(
                "Segoe UI",
                25,
                "bold"
            ),
            fg=TEXT,
            bg=SIDEBAR
        ).pack(
            anchor="w",
            padx=25,
            pady=(30, 0)
        )

        tk.Label(
            self.sidebar,
            text="OSINT FRAMEWORK",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=ACCENT,
            bg=SIDEBAR
        ).pack(
            anchor="w",
            padx=27,
            pady=(0, 35)
        )

        tk.Label(
            self.sidebar,
            text="MODULES",
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=SIDEBAR
        ).pack(
            anchor="w",
            padx=27,
            pady=(0, 10)
        )

        self.module_buttons = {}

        self.create_module_button(
            "✉   Gmail Lookup",
            "gmail"
        )

        self.create_module_button(
            "◎   IP Lookup",
            "ip"
        )

        self.create_module_button(
            "⌁   DNS Lookup",
            "dns"
        )

        self.create_module_button(
            "◈   WHOIS",
            "whois"
        )

        self.create_module_button(
            "☎   Phone Lookup",
            "phone"
        )

        bottom = tk.Frame(
            self.sidebar,
            bg=SIDEBAR
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=25,
            pady=25
        )

        tk.Label(
            bottom,
            text="Xeexx OSINT",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=SIDEBAR
        ).pack(
            anchor="w"
        )

        tk.Label(
            bottom,
            text=VERSION,
            font=(
                "Segoe UI",
                8
            ),
            fg="#566171",
            bg=SIDEBAR
        ).pack(
            anchor="w",
            pady=(3, 0)
        )

    def create_module_button(
        self,
        text,
        module
    ):

        button = tk.Label(
            self.sidebar,
            text=text,
            font=(
                "Segoe UI",
                10,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=SIDEBAR,
            padx=18,
            pady=12,
            anchor="w",
            cursor="hand2"
        )

        button.pack(
            fill="x",
            padx=12,
            pady=3
        )

        button.bind(
            "<Button-1>",
            lambda event, m=module:
            self.switch_module(m)
        )

        self.module_buttons[
            module
        ] = button

    # =====================================================
    # MAIN
    # =====================================================

    def create_main(self):

        self.main = tk.Frame(
            self.root,
            bg=BG
        )

        self.main.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=35,
            pady=30
        )

        self.main.grid_columnconfigure(
            0,
            weight=1
        )

        self.main.grid_rowconfigure(
            3,
            weight=1
        )

        self.header_title = tk.Label(
            self.main,
            text="GMAIL LOOKUP",
            font=(
                "Segoe UI",
                25,
                "bold"
            ),
            fg=TEXT,
            bg=BG
        )

        self.header_title.grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.header_description = tk.Label(
            self.main,
            text="Analyze a Gmail address",
            font=(
                "Segoe UI",
                10
            ),
            fg=TEXT_SECONDARY,
            bg=BG
        )

        self.header_description.grid(
            row=0,
            column=0,
            sticky="w",
            pady=(55, 0)
        )

        # -------------------------------------------------
        # Search Card
        # -------------------------------------------------

        self.search_card = tk.Frame(
            self.main,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        self.search_card.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(25, 20)
        )

        self.search_card.grid_columnconfigure(
            0,
            weight=1
        )

        self.input_label = tk.Label(
            self.search_card,
            text="EMAIL ADDRESS",
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=CARD
        )

        self.input_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(18, 5)
        )

        self.entry = tk.Entry(
            self.search_card,
            font=(
                "Segoe UI",
                12
            ),
            bg=CARD_2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0
        )

        self.entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 18),
            ipady=12
        )

        self.entry.bind(
            "<Return>",
            lambda event:
            self.start_search()
        )

        buttons = tk.Frame(
            self.search_card,
            bg=CARD
        )

        buttons.grid(
            row=2,
            column=0,
            sticky="e",
            padx=20,
            pady=(0, 18)
        )

        self.search_button = tk.Button(
            buttons,
            text="SEARCH",
            command=self.start_search,
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg="white",
            bg=ACCENT,
            activeforeground="white",
            activebackground=ACCENT_HOVER,
            relief="flat",
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2"
        )

        self.search_button.pack(
            side="left",
            padx=(0, 8)
        )

        tk.Button(
            buttons,
            text="CLEAR",
            command=self.clear,
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=CARD_2,
            activeforeground=TEXT,
            activebackground=BORDER,
            relief="flat",
            bd=0,
            padx=25,
            pady=10,
            cursor="hand2"
        ).pack(
            side="left"
        )

        # -------------------------------------------------
        # Status
        # -------------------------------------------------

        self.status = tk.Label(
            self.main,
            text="● READY",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=GREEN,
            bg=BG
        )

        self.status.grid(
            row=2,
            column=0,
            sticky="w",
            pady=(0, 10)
        )

        # -------------------------------------------------
        # Results Card
        # -------------------------------------------------

        self.results_card = tk.Frame(
            self.main,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1
        )

        self.results_card.grid(
            row=3,
            column=0,
            sticky="nsew"
        )

        tk.Label(
            self.results_card,
            text="RESULTS",
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=CARD
        ).pack(
            anchor="w",
            padx=20,
            pady=(18, 10)
        )

        self.create_scrollable_results()

        self.show_empty()

        self.update_module_buttons()

    # =====================================================
    # SCROLLABLE RESULTS
    # =====================================================

    def create_scrollable_results(self):

        container = tk.Frame(
            self.results_card,
            bg=CARD
        )

        container.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=(0, 15)
        )

        container.grid_rowconfigure(
            0,
            weight=1
        )

        container.grid_columnconfigure(
            0,
            weight=1
        )

        self.results_canvas = tk.Canvas(
            container,
            bg=CARD,
            highlightthickness=0,
            bd=0
        )

        self.results_canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        self.results_scrollbar = tk.Scrollbar(
            container,
            orient="vertical",
            command=self.results_canvas.yview,
            bg=CARD_2,
            troughcolor=CARD,
            activebackground=ACCENT,
            width=10
        )

        self.results_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.results_canvas.configure(
            yscrollcommand=
            self.results_scrollbar.set
        )

        self.results_frame = tk.Frame(
            self.results_canvas,
            bg=CARD
        )

        self.canvas_window = (
            self.results_canvas.create_window(
                (0, 0),
                window=self.results_frame,
                anchor="nw"
            )
        )

        self.results_frame.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.results_canvas.bind(
            "<Configure>",
            self.resize_canvas_frame
        )

        # Windows
        self.results_canvas.bind(
            "<MouseWheel>",
            self.on_mousewheel
        )

        # Linux
        self.results_canvas.bind(
            "<Button-4>",
            self.on_mousewheel_linux
        )

        self.results_canvas.bind(
            "<Button-5>",
            self.on_mousewheel_linux
        )

    # =====================================================
    # MOUSE WHEEL
    # =====================================================

    def bind_mousewheel_recursive(
        self,
        widget
    ):

        widget.bind(
            "<MouseWheel>",
            self.on_mousewheel
        )

        widget.bind(
            "<Button-4>",
            self.on_mousewheel_linux
        )

        widget.bind(
            "<Button-5>",
            self.on_mousewheel_linux
        )

        for child in widget.winfo_children():

            self.bind_mousewheel_recursive(
                child
            )

    def on_mousewheel(
        self,
        event
    ):

        if event.delta:

            self.results_canvas.yview_scroll(
                int(
                    -1 *
                    (event.delta / 120)
                ),
                "units"
            )

        return "break"

    def on_mousewheel_linux(
        self,
        event
    ):

        if event.num == 4:

            self.results_canvas.yview_scroll(
                -3,
                "units"
            )

        elif event.num == 5:

            self.results_canvas.yview_scroll(
                3,
                "units"
            )

        return "break"

    # =====================================================
    # CANVAS
    # =====================================================

    def update_scroll_region(
        self,
        event=None
    ):

        self.results_canvas.configure(
            scrollregion=
            self.results_canvas.bbox(
                "all"
            )
        )

    def resize_canvas_frame(
        self,
        event
    ):

        self.results_canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def refresh_scroll(self):

        self.results_frame.update_idletasks()

        self.results_canvas.configure(
            scrollregion=
            self.results_canvas.bbox(
                "all"
            )
        )

        self.results_canvas.yview_moveto(
            0
        )

    # =====================================================
    # MODULE SWITCH
    # =====================================================

    def switch_module(
        self,
        module
    ):

        self.current_module = module

        titles = {

            "gmail": (
                "GMAIL LOOKUP",
                "Analyze a Gmail address",
                "EMAIL ADDRESS"
            ),

            "ip": (
                "IP LOOKUP",
                "Resolve IP and reverse DNS information",
                "IP ADDRESS OR DOMAIN"
            ),

            "dns": (
                "DNS LOOKUP",
                "Inspect DNS records for a domain or IP",
                "DOMAIN OR IP ADDRESS"
            ),

            "whois": (
                "WHOIS LOOKUP",
                "Retrieve public domain registration information",
                "DOMAIN"
            ),

            "phone": (
                "PHONE LOOKUP",
                "Analyze public technical information about a phone number",
                "PHONE NUMBER"
            )
        }

        title, description, label = (
            titles[module]
        )

        self.header_title.config(
            text=title
        )

        self.header_description.config(
            text=description
        )

        self.input_label.config(
            text=label
        )

        self.clear()

        self.update_module_buttons()

    # =====================================================
    # MODULE BUTTONS
    # =====================================================

    def update_module_buttons(self):

        for module, button in (
            self.module_buttons.items()
        ):

            if module == self.current_module:

                button.config(
                    bg=ACCENT,
                    fg=TEXT
                )

            else:

                button.config(
                    bg=SIDEBAR,
                    fg=TEXT_SECONDARY
                )

    # =====================================================
    # SEARCH
    # =====================================================

    def start_search(self):

        target = self.entry.get().strip()

        if not target:

            messagebox.showwarning(
                "Xeexx OSINT",
                "Введите значение для поиска."
            )

            return

        module = self.current_module

        self.search_button.config(
            state="disabled",
            text="SEARCHING..."
        )

        self.status.config(
            text="● SEARCHING",
            fg=YELLOW
        )

        self.show_loading()

        thread = threading.Thread(
            target=self.run_search,
            args=(
                target,
                module
            ),
            daemon=True
        )

        thread.start()

    # =====================================================
    # SEARCH WORKER
    # =====================================================

    def run_search(
        self,
        target,
        module
    ):

        try:

            if module == "gmail":

                data = gmail_lookup(
                    target
                )

            elif module == "ip":

                data = ip_lookup(
                    target
                )

            elif module == "dns":

                data = dns_lookup(
                    target
                )

            elif module == "whois":

                data = whois_lookup(
                    target
                )

            elif module == "phone":

                data = phone_lookup(
                    target
                )

            else:

                data = {
                    "status": False,
                    "message":
                        "Неизвестный модуль"
                }

            self.root.after(
                0,
                lambda:
                self.display_result(
                    data,
                    module
                )
            )

        except Exception as error:

            self.root.after(
                0,
                lambda:
                self.show_error(
                    error
                )
            )

    # =====================================================
    # LOADING
    # =====================================================

    def show_loading(self):

        self.clear_results_widgets()

        tk.Label(
            self.results_frame,
            text="●",
            font=(
                "Segoe UI",
                30
            ),
            fg=ACCENT,
            bg=CARD
        ).pack(
            pady=(45, 5)
        )

        tk.Label(
            self.results_frame,
            text="Analyzing...",
            font=(
                "Segoe UI",
                12,
                "bold"
            ),
            fg=TEXT,
            bg=CARD
        ).pack()

        tk.Label(
            self.results_frame,
            text="Query is being processed",
            font=(
                "Segoe UI",
                9
            ),
            fg=TEXT_SECONDARY,
            bg=CARD
        ).pack(
            pady=5
        )

        self.refresh_scroll()

    # =====================================================
    # DISPLAY RESULT
    # =====================================================

    def display_result(
        self,
        data,
        module
    ):

        self.search_button.config(
            state="normal",
            text="SEARCH"
        )

        if data.get("status"):

            self.status.config(
                text="● COMPLETE",
                fg=GREEN
            )

        else:

            self.status.config(
                text="● NOT FOUND",
                fg=RED
            )

        self.clear_results_widgets()

        self.result_row(
            "STATUS",
            data.get(
                "message",
                "-"
            )
        )

        if module == "gmail":

            self.display_gmail(
                data
            )

        elif module == "ip":

            self.display_ip(
                data
            )

        elif module == "dns":

            self.display_dns(
                data
            )

        elif module == "whois":

            self.display_whois(
                data
            )

        elif module == "phone":

            self.display_phone(
                data
            )

        self.refresh_scroll()

    # =====================================================
    # PHONE RESULTS
    # =====================================================

    def display_phone(
        self,
        data
    ):

        self.result_row(
            "INPUT",
            data.get(
                "input",
                "-"
            )
        )

        self.result_row(
            "INTERNATIONAL",
            data.get(
                "international",
                "-"
            )
        )

        self.result_row(
            "NATIONAL",
            data.get(
                "national",
                "-"
            )
        )

        self.result_row(
            "COUNTRY",
            data.get(
                "country",
                "-"
            )
        )

        self.result_row(
            "COUNTRY CODE",
            data.get(
                "country_code",
                "-"
            )
        )

        self.result_row(
            "REGION",
            data.get(
                "region",
                "-"
            )
        )

        self.result_row(
            "CARRIER",
            data.get(
                "carrier",
                "-"
            )
        )

        self.result_row(
            "TIMEZONE",
            data.get(
                "timezone",
                "-"
            )
        )

        self.result_row(
            "TYPE",
            data.get(
                "number_type",
                "-"
            )
        )

        self.result_row(
            "POSSIBLE",
            "YES"
            if data.get("possible")
            else "NO"
        )

        self.result_row(
            "VALID",
            "YES"
            if data.get("valid")
            else "NO"
        )

    # =====================================================
    # GMAIL
    # =====================================================

    def display_gmail(
        self,
        data
    ):

        self.result_row(
            "EMAIL",
            data.get(
                "email",
                "-"
            )
        )

        self.result_row(
            "DOMAIN",
            data.get(
                "domain",
                "-"
            )
        )

        self.result_row(
            "DOMAIN IP",
            data.get(
                "ip",
                "-"
            )
        )

        self.result_row(
            "MX RECORDS",
            "\n".join(
                data.get(
                    "mx",
                    []
                )
            )
            or "Не найдены"
        )

        self.result_row(
            "GRAVATAR",
            data.get(
                "gravatar",
                "-"
            )
        )

    # =====================================================
    # IP
    # =====================================================

    def display_ip(
        self,
        data
    ):

        self.result_row(
            "TARGET",
            data.get(
                "target",
                "-"
            )
        )

        self.result_row(
            "IP ADDRESS",
            data.get(
                "ip",
                "-"
            )
        )

        self.result_row(
            "VERSION",
            data.get(
                "version",
                "-"
            )
        )

        self.result_row(
            "HOSTNAME",
            data.get(
                "hostname",
                "-"
            )
        )

        self.result_row(
            "REVERSE DNS",
            data.get(
                "reverse_dns",
                "-"
            )
        )

    # =====================================================
    # DNS
    # =====================================================

    def display_dns(
        self,
        data
    ):

        self.result_row(
            "TARGET",
            data.get(
                "target",
                "-"
            )
        )

        self.result_row(
            "TYPE",
            data.get(
                "type",
                "-"
            )
        )

        for record in (
            "A",
            "AAAA",
            "MX",
            "NS",
            "TXT",
            "CNAME",
            "PTR"
        ):

            values = data.get(
                record,
                []
            )

            self.result_row(
                record,
                "\n".join(values)
                if values
                else "Не найдены"
            )

    # =====================================================
    # WHOIS
    # =====================================================

    def display_whois(
        self,
        data
    ):

        self.result_row(
            "DOMAIN",
            data.get(
                "domain",
                "-"
            )
        )

        self.result_row(
            "REGISTRAR",
            data.get(
                "registrar",
                "-"
            )
        )

        self.result_row(
            "ORGANIZATION",
            data.get(
                "organization",
                "-"
            )
        )

        self.result_row(
            "CREATED",
            data.get(
                "creation",
                "-"
            )
        )

        self.result_row(
            "UPDATED",
            data.get(
                "updated",
                "-"
            )
        )

        self.result_row(
            "EXPIRES",
            data.get(
                "expiration",
                "-"
            )
        )

        self.result_row(
            "NAME SERVERS",
            "\n".join(
                data.get(
                    "name_servers",
                    []
                )
            )
            or "Не найдены"
        )

        self.result_row(
            "WHOIS STATUS",
            "\n".join(
                data.get(
                    "status_info",
                    []
                )
            )
            or "Не найден"
        )

        self.result_row(
            "WHOIS EMAILS",
            "\n".join(
                data.get(
                    "emails",
                    []
                )
            )
            or "Не найдены"
        )

    # =====================================================
    # RESULT ROW
    # =====================================================

    def result_row(
        self,
        title,
        value
    ):

        row = tk.Frame(
            self.results_frame,
            bg=CARD_2
        )

        row.pack(
            fill="x",
            pady=3
        )

        tk.Label(
            row,
            text=title,
            font=(
                "Segoe UI",
                8,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=CARD_2,
            width=16,
            anchor="nw"
        ).pack(
            side="left",
            padx=(15, 5),
            pady=12
        )

        value_label = tk.Label(
            row,
            text=str(value),
            font=(
                "Segoe UI",
                9
            ),
            fg=TEXT,
            bg=CARD_2,
            justify="left",
            anchor="w",
            wraplength=650
        )

        value_label.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5,
            pady=12
        )

        # Подключаем колесо к новой строке
        self.bind_mousewheel_recursive(
            row
        )

    # =====================================================
    # CLEAR RESULTS
    # =====================================================

    def clear_results_widgets(self):

        for widget in (
            self.results_frame.winfo_children()
        ):

            widget.destroy()

        self.results_canvas.yview_moveto(
            0
        )

    # =====================================================
    # EMPTY
    # =====================================================

    def show_empty(self):

        self.clear_results_widgets()

        tk.Label(
            self.results_frame,
            text="⌕",
            font=(
                "Segoe UI",
                35
            ),
            fg="#394352",
            bg=CARD
        ).pack(
            pady=(40, 5)
        )

        tk.Label(
            self.results_frame,
            text="No search performed",
            font=(
                "Segoe UI",
                12,
                "bold"
            ),
            fg=TEXT_SECONDARY,
            bg=CARD
        ).pack()

        tk.Label(
            self.results_frame,
            text=(
                "Enter a value above "
                "to start the lookup"
            ),
            font=(
                "Segoe UI",
                9
            ),
            fg="#566171",
            bg=CARD
        ).pack(
            pady=5
        )

        self.refresh_scroll()

    # =====================================================
    # ERROR
    # =====================================================

    def show_error(
        self,
        error
    ):

        self.search_button.config(
            state="normal",
            text="SEARCH"
        )

        self.status.config(
            text="● ERROR",
            fg=RED
        )

        self.clear_results_widgets()

        tk.Label(
            self.results_frame,
            text="Lookup failed",
            font=(
                "Segoe UI",
                14,
                "bold"
            ),
            fg=RED,
            bg=CARD
        ).pack(
            pady=(50, 5)
        )

        tk.Label(
            self.results_frame,
            text=str(error),
            font=(
                "Segoe UI",
                9
            ),
            fg=TEXT_SECONDARY,
            bg=CARD,
            wraplength=700,
            justify="left"
        ).pack()

        self.refresh_scroll()

    # =====================================================
    # CLEAR
    # =====================================================

    def clear(self):

        self.entry.delete(
            0,
            tk.END
        )

        self.status.config(
            text="● READY",
            fg=GREEN
        )

        self.search_button.config(
            state="normal",
            text="SEARCH"
        )

        self.show_empty()

        self.entry.focus()


# =========================================================
# START
# =========================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = XeexxOSINT(
        root
    )

    root.mainloop()