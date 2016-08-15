#!/bin/bash
sudo apt-get update
sudo apt-get install git python-pip make build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev libffi-dev libxml2-dev libxslt-dev python3.5-dev libpq-dev -y
sudo pip install virtualenvwrapper

git clone https://github.com/yyuu/pyenv.git ~/.pyenv
git clone https://github.com/yyuu/pyenv-virtualenvwrapper.git ~/.pyenv/plugins/pyenv-virtualenvwrapper

echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenvwrapper)"' >> ~/.bashrc

echo 'You need to Run ". ~/.bashrc && sh setup2.sh"'
sleep '5'
