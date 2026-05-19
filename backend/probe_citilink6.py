"""Финальный зонд: структура properties в JS + список товаров из каталога."""
import sys, time, json, re
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
    # === 1. Страница /properties/ — структура JS-стейта ===
    print("=== Страница /properties/ ===")
    # Используем товар из скриншота пользователя
    driver.get("https://www.citilink.ru/product/mysh-a4tech-bloody-l65-max-igrovaya-opticheskaya-provodnaya-usb-belyi-1874606/properties/")
    time.sleep(6)

    props_data = driver.execute_script("""
        try {
            var nd = document.getElementById('__NEXT_DATA__');
            var d = JSON.parse(nd.textContent);
            var pp = d.props.pageProps.initialState.productPage;
            var props = pp.properties || {};
            return {
                isPending: props.isPending,
                payloadKeys: Object.keys(props.payload || {}),
                sample: props.payload
            };
        } catch(e) { return {error: e.toString()}; }
    """)
    print(f"properties.isPending: {props_data.get('isPending')}")
    print(f"properties.payload keys: {props_data.get('payloadKeys')}")
    payload = props_data.get("sample") or {}
    for k, v in payload.items():
        if isinstance(v, list):
            print(f"\npayload['{k}'] len={len(v)}")
            if v and isinstance(v[0], dict):
                print(f"  first group keys: {list(v[0].keys())}")
                print(f"  first group: {json.dumps(v[0], ensure_ascii=False)[:400]}")
        else:
            print(f"payload['{k}']: {str(v)[:100]}")

    # === 2. Каталог — как получить список товаров после JS-загрузки ===
    print("\n\n=== Каталог мышей — товары после загрузки JS ===")
    driver.get("https://www.citilink.ru/catalog/myshi/")
    time.sleep(8)

    catalog_data = driver.execute_script("""
        try {
            var nd = document.getElementById('__NEXT_DATA__');
            var d = JSON.parse(nd.textContent);
            var sub = d.props.pageProps.initialState.subcategory;
            var pl = sub.productList;
            return {
                isPending: pl.isPending,
                payloadKeys: Object.keys(pl.payload || {}),
                productIds: (pl.payload || {}).productIds,
                limit: (pl.payload || {}).limit,
                offset: (pl.payload || {}).offset,
            };
        } catch(e) { return {error: e.toString()}; }
    """)
    print(f"productList.isPending: {catalog_data.get('isPending')}")
    print(f"productIds: {catalog_data.get('productIds', [])[:10]}")
    print(f"limit: {catalog_data.get('limit')}, offset: {catalog_data.get('offset')}")

    # DOM-карточки товаров
    print("\n--- DOM карточки после загрузки JS ---")
    cards_data = driver.execute_script("""
        // Ищем карточки с data-meta-name или по классам
        var cards = document.querySelectorAll('[data-meta-product-id], [data-product-id]');
        if (!cards.length) cards = document.querySelectorAll('[class*="ProductCardHorizontal"], [class*="product-card"]');
        var result = [];
        for (var i = 0; i < Math.min(cards.length, 5); i++) {
            var c = cards[i];
            result.push({
                tag: c.tagName,
                attrs: c.getAttribute('data-meta-product-id') || c.getAttribute('data-product-id') || c.getAttribute('class','').slice(0,60),
                href: (c.querySelector('a') || {}).href || '',
                text: c.innerText.slice(0, 100)
            });
        }
        return result;
    """)
    for c in cards_data:
        print(f"  {c}")

    # Попробуем поиск через fetch из контекста Selenium
    print("\n--- Fetch поиска из Selenium контекста ---")
    search_result = driver.execute_async_script("""
        var cb = arguments[arguments.length - 1];
        fetch('/search/?text=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%B0%D1%8F+%D0%BC%D1%8B%D1%88%D1%8C&limit=10', {
            headers: {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
        })
        .then(r => r.text())
        .then(t => cb({status: 'ok', preview: t.slice(0, 200)}))
        .catch(e => cb({error: e.toString()}));
    """)
    print(f"Search fetch: {search_result}")

finally:
    driver.quit()
    print("\nДрайвер закрыт")
