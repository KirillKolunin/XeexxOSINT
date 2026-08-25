import phonenumbers
from phonenumbers import geocoder, carrier, timezone


# ============================================================
# XEEXX OSINT TOOL v1.0
# PHONE LOOKUP
# By @xeexx
# ============================================================


def phone_lookup(phone):
    """
    Анализ телефонного номера.

    Получает:
    - Страну
    - Код страны
    - Регион
    - Оператора
    - Тип номера
    - Часовой пояс
    - International format
    - National format
    - E.164
    - Valid / Possible
    """

    phone = phone.strip()

    if not phone:
        return {
            "success": False,
            "error": "Номер телефона не введён."
        }

    try:
        # ----------------------------------------------------
        # Определяем регион
        # ----------------------------------------------------

        if phone.startswith("+"):
            number = phonenumbers.parse(phone, None)
        else:
            # Если номер введён без +,
            # по умолчанию используется Россия.
            number = phonenumbers.parse(phone, "RU")

        # ----------------------------------------------------
        # Проверка номера
        # ----------------------------------------------------

        possible = phonenumbers.is_possible_number(number)
        valid = phonenumbers.is_valid_number(number)

        # ----------------------------------------------------
        # Основная информация
        # ----------------------------------------------------

        country_code = number.country_code
        national_number = number.national_number

        # ----------------------------------------------------
        # Страна
        # ----------------------------------------------------

        country = geocoder.country_name_for_number(
            number,
            "en"
        )

        if not country:
            country = "Unknown"

        # ----------------------------------------------------
        # Регион
        # ----------------------------------------------------

        region = geocoder.description_for_number(
            number,
            "en"
        )

        if not region:
            region = "Unknown"

        # ----------------------------------------------------
        # Оператор
        # ----------------------------------------------------

        operator = carrier.name_for_number(
            number,
            "en"
        )

        if not operator:
            operator = "Unknown"

        # ----------------------------------------------------
        # Timezone
        # ----------------------------------------------------

        timezones = timezone.time_zones_for_number(number)

        if timezones:
            timezone_result = ", ".join(timezones)
        else:
            timezone_result = "Unknown"

        # ----------------------------------------------------
        # Тип номера
        # ----------------------------------------------------

        number_type = phonenumbers.number_type(number)

        type_names = {
            phonenumbers.PhoneNumberType.FIXED_LINE:
                "Fixed Line",

            phonenumbers.PhoneNumberType.MOBILE:
                "Mobile",

            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE:
                "Fixed Line / Mobile",

            phonenumbers.PhoneNumberType.TOLL_FREE:
                "Toll Free",

            phonenumbers.PhoneNumberType.PREMIUM_RATE:
                "Premium Rate",

            phonenumbers.PhoneNumberType.SHARED_COST:
                "Shared Cost",

            phonenumbers.PhoneNumberType.VOIP:
                "VoIP",

            phonenumbers.PhoneNumberType.PERSONAL_NUMBER:
                "Personal Number",

            phonenumbers.PhoneNumberType.PAGER:
                "Pager",

            phonenumbers.PhoneNumberType.UAN:
                "UAN",

            phonenumbers.PhoneNumberType.VOICEMAIL:
                "Voicemail",

            phonenumbers.PhoneNumberType.UNKNOWN:
                "Unknown"
        }

        phone_type = type_names.get(
            number_type,
            "Unknown"
        )

        # ----------------------------------------------------
        # Форматы номера
        # ----------------------------------------------------

        international = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.INTERNATIONAL
        )

        national = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.NATIONAL
        )

        e164 = phonenumbers.format_number(
            number,
            phonenumbers.PhoneNumberFormat.E164
        )

        # ----------------------------------------------------
        # Результат
        # ----------------------------------------------------

        return {
            "success": True,

            "input": phone,

            "international": international,

            "national": national,

            "e164": e164,

            "country_code": country_code,

            "national_number": national_number,

            "country": country,

            "region": region,

            "carrier": operator,

            "timezone": timezone_result,

            "type": phone_type,

            "possible": possible,

            "valid": valid
        }

    # --------------------------------------------------------
    # Ошибка неправильного номера
    # --------------------------------------------------------

    except phonenumbers.NumberParseException as e:

        return {
            "success": False,
            "error": f"Некорректный номер телефона: {e}"
        }

    # --------------------------------------------------------
    # Любая другая ошибка
    # --------------------------------------------------------

    except Exception as e:

        return {
            "success": False,
            "error": f"Ошибка: {e}"
        }


# ============================================================
# ВЫВОД РЕЗУЛЬТАТА
# ============================================================

def print_phone_lookup(result):

    print()
    print("=" * 60)
    print("                    XEEXX OSINT")
    print("                    PHONE LOOKUP")
    print("=" * 60)

    print("By @xeexx")
    print()

    # --------------------------------------------------------
    # Если произошла ошибка
    # --------------------------------------------------------

    if not result.get("success"):

        print("[ ERROR ]")
        print()
        print(result.get("error", "Неизвестная ошибка"))

        print("=" * 60)

        return

    # --------------------------------------------------------
    # Основная информация
    # --------------------------------------------------------

    print("[ PHONE INFORMATION ]")
    print()

    print(f"Input           : {result['input']}")
    print(f"E.164           : {result['e164']}")
    print(f"International   : {result['international']}")
    print(f"National        : {result['national']}")

    print()
    print("-" * 60)
    print()

    # --------------------------------------------------------
    # Географическая информация
    # --------------------------------------------------------

    print("[ LOCATION ]")
    print()

    print(f"Country Code    : +{result['country_code']}")
    print(f"Country         : {result['country']}")
    print(f"Region          : {result['region']}")

    print()
    print("-" * 60)
    print()

    # --------------------------------------------------------
    # Оператор
    # --------------------------------------------------------

    print("[ NETWORK ]")
    print()

    print(f"Carrier         : {result['carrier']}")
    print(f"Type            : {result['type']}")

    print()
    print("-" * 60)
    print()

    # --------------------------------------------------------
    # Дополнительная информация
    # --------------------------------------------------------

    print("[ ADDITIONAL INFORMATION ]")
    print()

    print(f"Timezone        : {result['timezone']}")
    print(f"Possible        : {result['possible']}")
    print(f"Valid           : {result['valid']}")

    print()
    print("=" * 60)


# ============================================================
# PHONE LOOKUP MENU
# ============================================================

def phone_lookup_menu():

    while True:

        print()
        print("=" * 60)
        print("                    XEEXX OSINT")
        print("                    PHONE LOOKUP")
        print("=" * 60)

        print("By @xeexx")
        print()

        print("Введите номер телефона.")
        print("Пример: +79991234567")
        print()
        print("Введите 0 для выхода.")
        print()

        try:

            phone = input("Введите номер телефона: ").strip()

        except (KeyboardInterrupt, EOFError):

            print()
            print("Выход из Phone Lookup...")
            break

        # ----------------------------------------------------
        # Выход
        # ----------------------------------------------------

        if phone == "0":

            print()
            print("Возврат в меню...")
            break

        # ----------------------------------------------------
        # Пустой ввод
        # ----------------------------------------------------

        if not phone:

            print()
            print("[!] Номер не введён.")

            input("\nНажмите Enter для продолжения...")
            continue

        # ----------------------------------------------------
        # Выполняем поиск
        # ----------------------------------------------------

        print()
        print("[*] Выполняется Phone Lookup...")

        result = phone_lookup(phone)

        # ----------------------------------------------------
        # Показываем результат
        # ----------------------------------------------------

        print_phone_lookup(result)

        # ----------------------------------------------------
        # После поиска НЕ закрываем программу
        # ----------------------------------------------------

        print()
        print("[ ENTER ] Новый поиск")
        print("[ 0     ] Выход")

        try:

            command = input("\nВаш выбор: ").strip()

        except (KeyboardInterrupt, EOFError):

            print()
            print("Выход...")
            break

        # ----------------------------------------------------
        # Выход
        # ----------------------------------------------------

        if command == "0":

            print()
            print("Phone Lookup завершён.")
            break

        # ----------------------------------------------------
        # Любой другой ввод / Enter = новый поиск
        # ----------------------------------------------------

        print()
        print("Запуск нового поиска...")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    try:

        phone_lookup_menu()

    except KeyboardInterrupt:

        print()
        print()
        print("Программа остановлена пользователем.")

    except Exception as e:

        print()
        print()
        print("[CRITICAL ERROR]")
        print(e)

        input("\nНажмите Enter для выхода...")