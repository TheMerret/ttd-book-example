from fabric.api import run
from fabric.context_managers import settings


def _get_manage_dot_py(sitename):
    """получить manage.py"""
    return f'~/sites/{sitename}/virtualenv/bin/python3 ~/sites/{sitename}/source/manage.py'


def reset_database(host, sitename):
    """обнулить базу данных"""
    manage_dot_py = _get_manage_dot_py(sitename)
    with settings(key_filename='~/.ssh/id_rsa_kali', host_string=f'kali@{host}'):
        run(f'{manage_dot_py} flush --noinput')


def create_session_on_server(host, email, sitename):
    """создать сеанс на сервере"""
    manage_dot_py = _get_manage_dot_py(sitename)
    with settings(key_filename='~/.ssh/id_rsa_kali', host_string=f'kali@{host}'):
        session_key = run(f'{manage_dot_py} create_session {email}')
        return session_key.strip()
