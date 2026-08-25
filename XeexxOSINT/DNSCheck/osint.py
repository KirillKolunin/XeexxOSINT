import requests
import socket
import ssl
import dns.resolver
import whois
from urllib.parse import urlparse


print("\n")
print("╔══════════════════════════════╗")
print("║       Xeexx OSINT Tool       ║")
print("║      Made by tg:@xeexxr      ║")
print("║            v1.0              ║")
print("╚══════════════════════════════╝")

def get_domain(target):
    if not target.startswith(("http://", "https://")):
        target = "https://" + target

    parsed = urlparse(target)
    return parsed.hostname


def dns_lookup(target):
    print("\n=== DNS LOOKUP ===")

    # Проверяем, является ли target IP-адресом
    import ipaddress

    try:
        ip = ipaddress.ip_address(target)

        # =========================
        # IP ADDRESS
        # =========================

        print(f"Тип: IP-адрес")
        print(f"IP: {ip}")
        print("\n[PTR / Reverse DNS]")

        try:
            hostname = socket.gethostbyaddr(str(ip))[0]
            print(hostname)
        except socket.herror:
            print("Reverse DNS не найден")

        return

    except ValueError:
        # Если это не IP — считаем, что это домен
        pass

    # =========================
    # DOMAIN
    # =========================

    print(f"Тип: Домен")
    print(f"Domain: {target}")

    record_types = ["A", "AAAA", "MX", "NS", "TXT", "CNAME"]

    for record_type in record_types:
        print(f"\n[{record_type}]")

        try:
            answers = dns.resolver.resolve(
                target,
                record_type
            )

            for answer in answers:
                print(answer)

        except dns.resolver.NoAnswer:
            print("Нет данных")

        except dns.resolver.NXDOMAIN:
            print("Домен не существует")
            break

        except dns.resolver.NoNameservers:
            print("DNS-сервер не ответил")

        except Exception as e:
            print("Ошибка:", e)


def ip_lookup(domain):
    print("\n=== IP INFORMATION ===")

    try:
        ip = socket.gethostbyname(domain)

        print("Domain:", domain)
        print("IP:", ip)

        return ip

    except Exception as e:
        print("Ошибка:", e)
        return None


def whois_lookup(domain):
    print("\n=== WHOIS ===")

    try:
        data = whois.whois(domain)

        print("Domain:", data.domain_name)
        print("Registrar:", data.registrar)
        print("Creation date:", data.creation_date)
        print("Expiration date:", data.expiration_date)
        print("Name servers:", data.name_servers)

    except Exception as e:
        print("WHOIS error:", e)


def http_headers(domain):
    print("\n=== HTTP HEADERS ===")

    try:
        url = "https://" + domain

        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True
        )

        print("Status:", response.status_code)
        print("Final URL:", response.url)

        for name, value in response.headers.items():
            print(f"{name}: {value}")

    except Exception as e:
        print("Ошибка:", e)


def ssl_information(domain):
    print("\n=== SSL INFORMATION ===")

    try:
        context = ssl.create_default_context()

        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(
                sock,
                server_hostname=domain
            ) as secure_socket:

                certificate = secure_socket.getpeercert()

                print("Subject:", certificate.get("subject"))
                print("Issuer:", certificate.get("issuer"))
                print("Valid from:", certificate.get("notBefore"))
                print("Valid until:", certificate.get("notAfter"))

    except Exception as e:
        print("SSL error:", e)


def robots_txt(domain):
    print("\n=== ROBOTS.TXT ===")

    try:
        url = "https://" + domain + "/robots.txt"

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code == 200:
            print(response.text[:5000])
        else:
            print("robots.txt не найден")

    except Exception as e:
        print("Ошибка:", e)


def security_txt(domain):
    print("\n=== SECURITY.TXT ===")

    try:
        url = "https://" + domain + "/.well-known/security.txt"

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code == 200:
            print(response.text[:5000])
        else:
            print("security.txt не найден")

    except Exception as e:
        print("Ошибка:", e)


def full_scan(domain):
    print("\n")
    print("=" * 50)
    print("       XEEXX OSINT TOOL v1.0")
    print("=" * 50)

    print("\nTarget:", domain)

    ip_lookup(domain)
    dns_lookup(domain)
    whois_lookup(domain)
    http_headers(domain)
    ssl_information(domain)
    robots_txt(domain)
    security_txt(domain)

    print("\n" + "=" * 50)
    print("Scan completed")
    print("=" * 50)


def menu():
    while True:

        print("\n")
        print("╔══════════════════════════════╗")
        print("║       Xeexx OSINT Tool       ║")
        print("║            v1.0              ║")
        print("╚══════════════════════════════╝")

        print("\n[1] Полная проверка домена")
        print("[2] DNS Lookup")
        print("[3] IP Lookup")
        print("[4] WHOIS")
        print("[5] HTTP Headers")
        print("[6] SSL информация")
        print("[7] robots.txt")
        print("[8] security.txt")
        print("[0] Выход")

        choice = input("\nВыберите действие: ")

        if choice == "0":
            print("\nMade by Xeexx with love ;)")
            break

        domain = input("\nВведите домен: ").strip()
        domain = get_domain(domain)

        if not domain:
            print("Некорректный домен!")
            continue

        if choice == "1":
            full_scan(domain)

        elif choice == "2":
            dns_lookup(domain)

        elif choice == "3":
            ip_lookup(domain)

        elif choice == "4":
            whois_lookup(domain)

        elif choice == "5":
            http_headers(domain)

        elif choice == "6":
            ssl_information(domain)

        elif choice == "7":
            robots_txt(domain)

        elif choice == "8":
            security_txt(domain)

        else:
            print("Неизвестная команда!")

        input("\nНажмите Enter, чтобы продолжить...")


if __name__ == "__main__":
    menu()