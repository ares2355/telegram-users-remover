import csv
import os

import PySimpleGUI as sg
from PIL import Image
from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.types import User

load_dotenv()

CLIENT_API_ID = int(os.getenv('CLIENT_API_ID', '0'))
CLIENT_API_KEY = os.getenv('CLIENT_API_KEY', '')
CLIENT_API_HASH = os.getenv('CLIENT_API_HASH', '')


def get_contacts_table(client: Client):
    contacts = client.get_contacts()
    table = [[contact.first_name, contact.last_name, contact.phone_number] for contact in contacts]
    return contacts, table


def popup_image(text, filename=None, image_data=None):
    window = sg.Window('', [
        [sg.Text(text, enable_events=True)],
        [sg.Image(filename=filename, data=image_data, enable_events=True)]
    ])
    window.read(close=True)


with Client(CLIENT_API_KEY, api_id=CLIENT_API_ID, api_hash=CLIENT_API_HASH) as app:
    sg.theme('DarkAmber')
    sg.set_options(
        text_color='#e46eff',
        element_text_color='#e46eff',
        titlebar_text_color='#e46eff'
    )
    contacts_list, contacts_table = get_contacts_table(app)
    layout = [
        [sg.Text('Выберите контакты (с CTRL):', key='Text')],
        [sg.Table(values=contacts_table,
                  headings=['Имя', 'Фамилия', 'Телефон'],
                  max_col_width=100,
                  justification='left',
                  bind_return_key=True,
                  key="TABLE",
                  num_rows=20)],
        [
            sg.Button('Сохранить контакты', key="SAVE"),
            sg.Button('Удалить выбранные', key="REMOVE")
        ]
    ]

    window = sg.Window('Удаление контактов Telegram', layout)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        print(f'[Значения] values={values}, [Событие] event={event}')
        if event == 'TABLE':
            i = values['TABLE'][0]
            user: User = contacts_list[i]
            user_id = user.id
            avatars = app.get_profile_photos(user_id)
            if len(avatars) > 0:
                path_to_image = app.download_media(avatars[-1])
                path_to_image_png = path_to_image.replace('.jpg', '.png')
                # ТОЖЕ САМОЕ: Image.open(path_to_image).save(path_to_image_png)
                image = Image.open(path_to_image)
                image.save(path_to_image_png)
                popup_image('Аватар пользователя:', path_to_image_png)
                os.remove(path_to_image)
                os.remove(path_to_image_png)
            else:
                sg.PopupError('У пользователя нет аватарки 😯')
        elif event == 'REMOVE':
            contacts_indexes = values['TABLE']
            try:
                app.delete_contacts([contacts_list[i].id for i in contacts_indexes])
                for i in contacts_indexes:
                    print(f'Удален контакт: {contacts_list[i].first_name} {contacts_list[i].last_name}')
            except Exception as e:
                sg.Popup(f'Ошибка во время обработки запроса :(\n{e}')
            else:
                sg.Popup(f'Успешно удалено контактов: {len(contacts_indexes)}.')
                contacts_list, contacts_table = get_contacts_table(app)
                window['TABLE'].update(values=contacts_table)
        elif event == 'SAVE':
            path_to_file = sg.PopupGetFolder('Выберите папку для сохранения контактов')
            if path_to_file is None:
                path_to_file = 'contacts.csv'
            else:
                path_to_file += '/contacts.csv'
            with open(path_to_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(window['TABLE'].ColumnHeadings)
                writer.writerows(contacts_table)
            sg.PopupAutoClose(f'Контакты сохранены в файл {path_to_file}!')
    window.close()
