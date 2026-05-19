"""Проверяем исправленный _get_properties — должен вернуть Max BC3332-A."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')
from app.parsers.citilink import _get_properties

url = 'https://www.citilink.ru/product/mysh-a4tech-bloody-l65-max-igrovaya-opticheskaya-provodnaya-usb-belyi-1874606/'
props, price = _get_properties(url)
print(f"Сенсор:  {props.get('Сенсор')!r}")
print(f"Цена:    {price}")
print(f"Бренд:   {props.get('Бренд')!r}")
print(f"Вес:     {props.get('Вес')!r}")
print(f"DPI:     {props.get('Разрешение сенсора, макс.')!r}")
