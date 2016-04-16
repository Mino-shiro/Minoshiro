pyenv install 3.5.1

sudo apt-get install libffi-dev libxml2-dev libxslt-dev -y

pyvenv venv
source venv/bin/activate

pip install git+https://github.com/Rapptz/discord.py@async
pip install -r requirements.txt
