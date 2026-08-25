import tkinter as tk
from tkinter import messagebox
import requests
import ipaddress
import math


APP_NAME = "Xeexx OS — IP Geolocation"
API_URL = "http://ip-api.com/json/"


# ============================================================
# IP VALIDATION
# ============================================================

def is_valid_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


# ============================================================
# CLEAR RESULTS
# ============================================================

def clear_results():

    for widget in result_frame.winfo_children():
        widget.destroy()

    result_frame.pack_forget()

    status_label.config(
        text="Готов к поиску",
        fg="#888888"
    )


# ============================================================
# IP LOOKUP
# ============================================================

def lookup_ip():

    ip = ip_entry.get().strip()

    if not ip:
        messagebox.showwarning(
            "Xeexx OS",
            "Введите IP-адрес."
        )
        return

    if not is_valid_ip(ip):

        messagebox.showerror(
            "Xeexx OS",
            "Некорректный IP-адрес.\n\n"
            "Пример: 8.8.8.8"
        )

        return

    # Очистка предыдущего результата
    clear_results()

    status_label.config(
        text="Получение информации...",
        fg="#aaaaaa"
    )

    lookup_button.config(
        state="disabled"
    )

    root.update_idletasks()

    try:

        response = requests.get(
            API_URL + ip,
            params={
                "fields": (
                    "status,message,query,country,countryCode,"
                    "region,regionName,city,zip,lat,lon,"
                    "timezone,isp,org,as"
                )
            },
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        if data.get("status") != "success":

            status_label.config(
                text="Ошибка получения данных",
                fg="#ff5555"
            )

            messagebox.showerror(
                "Xeexx OS",
                data.get(
                    "message",
                    "Не удалось получить информацию."
                )
            )

            return

        show_results(data)

        status_label.config(
            text="Lookup завершён",
            fg="#55ff88"
        )

    except requests.exceptions.Timeout:

        status_label.config(
            text="Время ожидания истекло",
            fg="#ff5555"
        )

        messagebox.showerror(
            "Xeexx OS",
            "Сервер не ответил в течение 10 секунд."
        )

    except requests.exceptions.ConnectionError:

        status_label.config(
            text="Ошибка подключения",
            fg="#ff5555"
        )

        messagebox.showerror(
            "Xeexx OS",
            "Не удалось подключиться к API.\n\n"
            "Проверь интернет-соединение."
        )

    except requests.exceptions.HTTPError as e:

        status_label.config(
            text="HTTP ошибка",
            fg="#ff5555"
        )

        messagebox.showerror(
            "Xeexx OS",
            f"HTTP ошибка:\n{e}"
        )

    except ValueError:

        status_label.config(
            text="Ошибка ответа API",
            fg="#ff5555"
        )

        messagebox.showerror(
            "Xeexx OS",
            "API вернул некорректный ответ."
        )

    except Exception as e:

        status_label.config(
            text="Неизвестная ошибка",
            fg="#ff5555"
        )

        messagebox.showerror(
            "Xeexx OS",
            f"Произошла ошибка:\n\n{e}"
        )

    finally:

        lookup_button.config(
            state="normal"
        )


# ============================================================
# SHOW RESULTS
# ============================================================

def show_results(data):

    result_frame.pack(
        fill="both",
        expand=True,
        padx=25,
        pady=(10, 20)
    )

    values = [

        ("IP Address", data.get("query", "—")),

        ("Country", data.get("country", "—")),

        ("Country Code", data.get("countryCode", "—")),

        ("Region", data.get("regionName", "—")),

        ("City", data.get("city", "—")),

        ("ZIP Code", data.get("zip", "—")),

        ("Latitude", data.get("lat", "—")),

        ("Longitude", data.get("lon", "—")),

        ("Timezone", data.get("timezone", "—")),

        ("ISP", data.get("isp", "—")),

        ("Organization", data.get("org", "—")),

        ("ASN", data.get("as", "—")),
    ]

    for index, (name, value) in enumerate(values):

        name_label = tk.Label(
            result_frame,
            text=name,
            font=("Segoe UI", 10, "bold"),
            bg="#111111",
            fg="#777777",
            anchor="w"
        )

        name_label.grid(
            row=index,
            column=0,
            sticky="w",
            padx=(15, 20),
            pady=5
        )

        value_label = tk.Label(
            result_frame,
            text=str(value),
            font=("Segoe UI", 10),
            bg="#111111",
            fg="#eeeeee",
            anchor="w"
        )

        value_label.grid(
            row=index,
            column=1,
            sticky="w",
            padx=10,
            pady=5
        )

    result_frame.columnconfigure(
        1,
        weight=1
    )


# ============================================================
# NEW SEARCH
# ============================================================

def new_search():

    ip_entry.delete(
        0,
        tk.END
    )

    clear_results()

    ip_entry.focus()


# ============================================================
# ENTER KEY
# ============================================================

def on_enter(event):

    lookup_ip()


# ============================================================
# MOUSE GLOW
# ============================================================

mouse_x = 325
mouse_y = 360

glow_enabled = True


def mouse_move(event):

    global mouse_x
    global mouse_y

    mouse_x = event.x
    mouse_y = event.y


def draw_mouse_glow():

    if not glow_enabled:
        return

    glow_canvas.delete(
        "glow"
    )

    # Размер свечения
    max_radius = 170

    # Несколько прозрачных по ощущениям колец.
    # Tkinter Canvas не поддерживает настоящую прозрачность,
    # поэтому используется плавный переход цветов.
    glow_colors = [
        "#151515",
        "#141414",
        "#131313",
        "#121212",
        "#111111",
        "#101010",
        "#0f0f0f",
        "#0e0e0e",
        "#0d0d0d",
        "#0c0c0c",
        "#0b0b0b",
    ]

    steps = len(glow_colors)

    for i, color in enumerate(glow_colors):

        radius = max_radius - (
            i * (max_radius / steps)
        )

        x1 = mouse_x - radius
        y1 = mouse_y - radius

        x2 = mouse_x + radius
        y2 = mouse_y + radius

        glow_canvas.create_oval(
            x1,
            y1,
            x2,
            y2,
            fill=color,
            outline="",
            tags="glow"
        )

    # Маленькое центральное свечение
    glow_canvas.create_oval(
        mouse_x - 25,
        mouse_y - 25,
        mouse_x + 25,
        mouse_y + 25,
        fill="#191919",
        outline="",
        tags="glow"
    )

    root.after(
        25,
        draw_mouse_glow
    )


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()

root.title(
    APP_NAME
)

root.geometry(
    "650x720"
)

root.minsize(
    600,
    650
)

root.configure(
    bg="#080808"
)


# ============================================================
# BACKGROUND CANVAS
# ============================================================

glow_canvas = tk.Canvas(
    root,
    bg="#080808",
    highlightthickness=0,
    bd=0
)

glow_canvas.place(
    x=0,
    y=0,
    relwidth=1,
    relheight=1
)


# Следим за мышью
root.bind(
    "<Motion>",
    mouse_move
)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg="#080808"
)

header.pack(
    fill="x",
    padx=25,
    pady=(25, 5)
)


title_label = tk.Label(
    header,
    text="Xeexx OS",
    font=("Segoe UI", 25, "bold"),
    bg="#080808",
    fg="#ffffff"
)

title_label.pack(
    anchor="w"
)


subtitle_label = tk.Label(
    header,
    text="IP GEOLOCATION",
    font=("Segoe UI", 10),
    bg="#080808",
    fg="#666666"
)

subtitle_label.pack(
    anchor="w",
    pady=(2, 0)
)


# ============================================================
# AUTHOR
# ============================================================

author_label = tk.Label(
    root,
    text="By @xeexxr",
    font=("Segoe UI", 9),
    bg="#080808",
    fg="#555555"
)

author_label.pack(
    pady=(15, 5)
)


# ============================================================
# SEARCH FRAME
# ============================================================

search_frame = tk.Frame(
    root,
    bg="#111111"
)

search_frame.pack(
    fill="x",
    padx=25,
    pady=15
)


ip_entry = tk.Entry(
    search_frame,
    font=("Segoe UI", 12),
    bg="#181818",
    fg="#ffffff",
    insertbackground="#ffffff",
    relief="flat",
    bd=0
)

ip_entry.pack(
    side="left",
    fill="x",
    expand=True,
    padx=(15, 10),
    pady=15,
    ipady=8
)

ip_entry.insert(
    0,
    "8.8.8.8"
)


lookup_button = tk.Button(
    search_frame,
    text="LOOKUP",
    font=("Segoe UI", 10, "bold"),
    bg="#222222",
    fg="#ffffff",
    activebackground="#333333",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    cursor="hand2",
    command=lookup_ip
)

lookup_button.pack(
    side="right",
    padx=(0, 15),
    pady=15,
    ipadx=12,
    ipady=8
)


ip_entry.bind(
    "<Return>",
    on_enter
)


# ============================================================
# STATUS
# ============================================================

status_label = tk.Label(
    root,
    text="Готов к поиску",
    font=("Segoe UI", 9),
    bg="#080808",
    fg="#888888"
)

status_label.pack(
    pady=(0, 5)
)


# ============================================================
# RESULT FRAME
# ============================================================

result_frame = tk.Frame(
    root,
    bg="#111111"
)


# ============================================================
# NEW SEARCH BUTTON
# ============================================================

new_search_button = tk.Button(
    root,
    text="NEW SEARCH",
    font=("Segoe UI", 9, "bold"),
    bg="#111111",
    fg="#aaaaaa",
    activebackground="#222222",
    activeforeground="#ffffff",
    relief="flat",
    bd=0,
    cursor="hand2",
    command=new_search
)

new_search_button.pack(
    pady=(0, 15),
    ipadx=15,
    ipady=6
)


# ============================================================
# FOOTER
# ============================================================

footer = tk.Label(
    root,
    text="IP geolocation provides approximate location data",
    font=("Segoe UI", 8),
    bg="#080808",
    fg="#444444"
)

footer.pack(
    side="bottom",
    pady=10
)


# ============================================================
# START
# ============================================================

ip_entry.focus()

draw_mouse_glow()

root.mainloop()