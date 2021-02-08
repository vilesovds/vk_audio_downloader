# -*- coding: utf-8 -*-
import vk_api
from vk_api.audio import VkAudio
import re
import requests
from tqdm import tqdm
import os
import traceback

FORBIDDEN_CHARS = '/\\\?%*:|"<>!'
PLAY_LIST_KEY = 'playlist'
ALBUM_KEY = 'album'


def get_track_full_name(t_data):
    full_name = f"{t_data['artist'][:50].strip()} - {t_data['title'][:50].strip()}"
    full_name = re.sub('[' + FORBIDDEN_CHARS + ']', "", full_name)
    full_name = re.sub(' +', ' ', full_name)
    return full_name + ".mp3"


def assure_folder_exists(root, folder):
    full_path = os.path.join(root, folder)
    if not os.path.isdir(full_path):
        os.mkdir(full_path)

    return full_path


def two_factor():
    code = input('Code to login: ')
    return code, True


def login(vk_login, vk_password):
    try:
        vk_session = vk_api.VkApi(login=vk_login, password=vk_password, auth_handler=two_factor)
        vk_session.auth()
    except Exception as err:
        traceback.print_exc(limit=1)
        exit(-1)
    return vk_session


def download(session, url, path=os.path.curdir):
    vk_audio = VkAudio(session)
    # analise url
    try:
        if url.find(ALBUM_KEY) > 0 or url.find(PLAY_LIST_KEY) > 0:
            params = url.split('/')[-1].split('_')
            audio_list = vk_audio.get(*params)
        else:
            req = vk_session.method('users.get', {'user_ids': url.split('/')[-1]})
            user = req[0].get('id')
            audio_list = vk_audio.get(owner_id=user)
    except Exception as err:
        traceback.print_exc(limit=1)
        exit(-1)

    assure_folder_exists(os.getcwd(), path)

    length = len(audio_list)
    print(f'Downloading {length} tracks')

    for i, track in enumerate(audio_list, 1):
        url = track['url']
        name = get_track_full_name(track)
        print(f'Downloading {i}/{length}: {name}')
        r = requests.get(url, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        with open(os.path.join(path, name), 'wb') as f:
            for data in tqdm(iterable=r.iter_content(chunk_size=1024),
                             total=total_size//1024,
                             unit='KB'):
                f.write(data)


def print_help(script_name):
    print('Usage:')
    print(f'python {script_name} <url> [<path>]')
    print('url should be like this')
    print('https://vk.com/music/album/-2000287271_10287271_f3363cc30df3a41df9')
    print('https://vk.com/music/playlist/-50715672_37938267_7476d3d845a23f6629')
    print('https://vk.com/id1')


if __name__ == "__main__":
    import sys
    import configparser
    config = configparser.ConfigParser()

    config.read("config.ini")

    username = config['Vk_auth']['username']
    password = config['Vk_auth']['password']

    vk_session = login(username, password)
    if len(sys.argv) < 2:
        print_help(sys.argv[0])
    elif len(sys.argv) == 2:
        download(vk_session, sys.argv[1])
    else:
        download(vk_session, sys.argv[1], sys.argv[2])
