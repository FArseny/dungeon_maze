## run project

`git clone git@github.com:FArseny/dungeon_maze.git`

`cd dungeon_maze`

`pipenv shell`

`pipenv install -r requirements.txt`

`python3 server.py`


## description
`server.py` - запуск + роутер

`game_manager.py` - логика для поиска игры

`game.py` - реализация класса игры(ее состояние) и логика персонажей

`tools.py` - вспомогательные инструменты

`t_bot.py` - отправка уведомления в телеграме о том, что кто-то начал искать игру (чтобы составить компанию)
