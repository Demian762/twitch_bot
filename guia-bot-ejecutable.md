para instalar en local:
pip install playsound
pip install python-Levenshtein
pip install -U twitchio
pip install howlongtobeatpy (la 1.0.7 anda mal)
pip install python-steam-api
pip install google-api-python-client
pip install gspread
pip install requests
pip install pandas

Para instalar en ambiente virtual:
en la terminal de git bash

python -m venv bot-env
source bot-env/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
pip list
pip install -U pyinstaller
(
corregir la version de ---> bot-env/Lib/site-packages/steam_web_api/_version.py
except Exception:
    __version__ = "2.0.4"
)

corregir la extension de ---> browsers.jsonl
D:\\02 - practicas Python\\00_twitch_bot\\bot-env\\Lib\\site-packages\\fake_useragent\\data\\browsers.json'

pyinstaller --onefile --add-data "storage/*:storage" --add-binary "D:\02 - practicas Python\00_twitch_bot\bot-env\Lib\site-packages\fake_useragent\data\browsers.json;fake_useragent/data" --paths="D:/02 - practicas Python/00_twitch_bot/bot-env/Lib/site-packages" bot_del_estadio.py

deactivate


