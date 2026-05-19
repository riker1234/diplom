"""DOM структура характеристик и поиск через Selenium."""
import sys, time, json
sys.stdout.reconfigure(encoding='utf-8')
import os; os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
stealth(driver, languages=["ru-RU","ru"], vendor="Google Inc.", platform="Win32",
        webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True)
driver.set_script_timeout(30)

try:
    # === 1. Структура DOM на /properties/ ===
    print("=== /properties/ DOM структура ===")
    driver.get("https://www.citilink.ru/product/mysh-a4tech-bloody-l65-max-igrovaya-opticheskaya-provodnaya-usb-belyi-1874606/properties/")
    time.sleep(5)

    # Ищем отдельные строки name/value
    rows = driver.execute_script("""
        var result = [];
        // Пробуем найти пары имя/значение
        var allEls = document.querySelectorAll('[class*="Properties"]');
        var classes = new Set();
        allEls.forEach(function(el) {
            el.className.split(' ').forEach(function(c) { if (c.includes('ropert')) classes.add(c); });
        });
        return Array.from(classes);
    """)
    print(f"Классы с 'ropert': {rows}")

    # Смотрим все уникальные классы содержащие данные
    classes = driver.execute_script("""
        var classes = new Set();
        document.querySelectorAll('*').forEach(function(el) {
            if (el.className && typeof el.className === 'string') {
                el.className.split(' ').forEach(function(c) {
                    if (c.length > 3 && (c.includes('prop') || c.includes('Prop') || c.includes('spec') || c.includes('Spec') || c.includes('char') || c.includes('Char') || c.includes('param') || c.includes('Param'))) {
                        classes.add(c);
                    }
                });
            }
        });
        return Array.from(classes).slice(0, 30);
    """)
    print(f"\nРелевантные классы: {classes}")

    # Пробуем извлечь все пары ключ-значение напрямую
    pairs = driver.execute_script("""
        var result = [];
        // Ищем элементы содержащие текст после двоеточия (паттерн "Название: Значение")
        var els = document.querySelectorAll('[class*="Properties"]');
        els.forEach(function(el) {
            var children = el.children;
            if (children.length >= 2) {
                var name = children[0].innerText.trim();
                var val = children[1].innerText.trim();
                if (name && val && name.length < 80) {
                    result.push([name, val]);
                }
            } else if (el.innerText.includes(':')) {
                var text = el.innerText.trim();
                result.push(['RAW', text.slice(0, 100)]);
            }
        });
        return result.slice(0, 30);
    """)
    print(f"\nПары name/value ({len(pairs)}):")
    for p in pairs:
        print(f"  {p[0]!r}: {p[1]!r}")

    # Цена товара
    price = driver.execute_script("""
        var el = document.querySelector('[class*="Price__price"], [class*="price__price"], [data-meta-name="Price"]');
        return el ? el.innerText : null;
    """)
    print(f"\nЦена: {price!r}")

    # === 2. Поиск — товары в DOM ===
    print("\n\n=== Поиск 'игровая мышь' ===")
    driver.get("https://www.citilink.ru/search/?text=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%B0%D1%8F+%D0%BC%D1%8B%D1%88%D1%8C")
    time.sleep(6)

    search_cards = driver.execute_script("""
        var cards = document.querySelectorAll('[data-meta-product-id]');
        var result = [];
        for (var i = 0; i < Math.min(cards.length, 5); i++) {
            var c = cards[i];
            var a = c.querySelector('a[href*="/product/"]');
            var priceEl = c.querySelector('[class*="Price__price"], [class*="price"]');
            result.push({
                id: c.getAttribute('data-meta-product-id'),
                href: a ? a.href : '',
                price: priceEl ? priceEl.innerText.trim().slice(0,20) : ''
            });
        }
        return {count: cards.length, items: result};
    """)
    print(f"Карточек: {search_cards.get('count')}")
    for item in search_cards.get('items', []):
        print(f"  id={item['id']} price={item['price']!r} url={item['href'][-60:]!r}")

finally:
    driver.quit()
    print("\nДрайвер закрыт")
