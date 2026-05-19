"""Разведка Ситилинк через Selenium: структура DOM и JS-стейт после загрузки."""
import sys, time, json, re
sys.stdout.reconfigure(encoding='utf-8')
import os; os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
stealth(driver, languages=["ru-RU","ru"], vendor="Google Inc.",
        platform="Win32", webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine", fix_hairline=True)
driver.set_script_timeout(30)

try:
    # 1. Открываем каталог мышей
    print("Открываем каталог мышей...")
    driver.get("https://www.citilink.ru/catalog/myshi/")
    time.sleep(6)

    # 2. Смотрим что загрузилось в JS-стейт (Effector store)
    print("\n--- JS state после загрузки ---")
    state = driver.execute_script("""
        try {
            var nd = document.getElementById('__NEXT_DATA__');
            if (nd) {
                var d = JSON.parse(nd.textContent);
                var sub = d.props.pageProps.initialState.subcategory;
                return {
                    productsFilter: sub.productList,
                    productsInFilter: sub.productsFilter
                };
            }
        } catch(e) { return {error: e.toString()}; }
    """)
    if state:
        pl = state.get("productsFilter", {})
        pf = state.get("productsInFilter", {})
        print(f"productList.isPending: {pl.get('isPending')}, payload keys: {list((pl.get('payload') or {}).keys())[:10]}")
        products_filter = (pf.get("payload") or {}).get("productsFilter", {})
        products = products_filter.get("products", [])
        print(f"productsFilter products count: {len(products)}")
        total = products_filter.get("total") or products_filter.get("count")
        print(f"total: {total}")

    # 3. Ищем карточки товаров в DOM
    print("\n--- Поиск карточек в DOM ---")
    selectors = [
        ".product-card", ".ProductCard", "[data-meta-name='ProductCard']",
        "[class*='product-card']", "[class*='ProductCard']",
        "article", "[data-product-id]", "[data-id]",
    ]
    for sel in selectors:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            print(f"  '{sel}': найдено {len(els)}")
            # Смотрим атрибуты первого элемента
            el = els[0]
            attrs = driver.execute_script("""
                var el = arguments[0];
                var res = {};
                for (var i = 0; i < el.attributes.length; i++) {
                    res[el.attributes[i].name] = el.attributes[i].value;
                }
                return res;
            """, el)
            print(f"    attrs: {dict(list(attrs.items())[:8])}")

    # 4. Пробуем дождаться загрузки полного списка
    print("\n--- Ждём загрузки списка товаров (10 сек) ---")
    time.sleep(10)

    # Читаем стейт снова после полной загрузки
    state2 = driver.execute_script("""
        try {
            // Пробуем window.__effector_stores__ или аналоги
            if (window.__effector_stores__) return {type: 'effector_stores', keys: Object.keys(window.__effector_stores__).slice(0,10)};
            // Пробуем найти данные через React fiber
            var nodes = document.querySelectorAll('[data-meta-name]');
            var result = [];
            for (var i = 0; i < Math.min(nodes.length, 5); i++) {
                result.push({tag: nodes[i].tagName, meta: nodes[i].getAttribute('data-meta-name'), text: nodes[i].innerText.slice(0,100)});
            }
            return {type: 'meta_nodes', data: result};
        } catch(e) { return {error: e.toString()}; }
    """)
    print(f"State2: {json.dumps(state2, ensure_ascii=False)[:400]}")

    # 5. Страница товара — характеристики
    print("\n--- Страница товара ---")
    driver.get("https://www.citilink.ru/product/mysh-oklik-202mw-chernyi-optich-1000dpi-besprov-usb-3but-2070314/")
    time.sleep(6)

    char_data = driver.execute_script("""
        try {
            var nd = document.getElementById('__NEXT_DATA__');
            var d = JSON.parse(nd.textContent);
            var state = d.props.pageProps.initialState;
            // Ищем характеристики в productPage
            var pp = state.productPage || {};
            return {productPage_keys: Object.keys(pp), gql: Object.keys(state.gql || {}).slice(0,5)};
        } catch(e) { return {error: e.toString()}; }
    """)
    print(f"Product page state: {char_data}")

    # DOM: ищем блок характеристик
    char_selectors = [
        "[data-meta-name='Specifications']",
        "[class*='Specifications']", "[class*='specifications']",
        "[class*='properties']", "[class*='Properties']",
        ".product-characteristics", "table.specs",
    ]
    for sel in char_selectors:
        els = driver.find_elements(By.CSS_SELECTOR, sel)
        if els:
            print(f"  '{sel}': найдено {len(els)}")
            print(f"    text: {els[0].text[:200]!r}")

finally:
    driver.quit()
    print("\nДрайвер закрыт")
