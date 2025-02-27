# Yandex Music Rhythmbox plugin
Плагин для работы с музыкальным сервисом Яндекс.Музыка в Rhythmbox.

## Установка
Для работы плагина требуется установить [неофициальную Python библиотеку API Yandex Music](https://github.com/MarshalX/yandex-music-api).

    $ pip install yandex-music --upgrade

Затем скачать плагин и переместить его в папку с плагинами Rhythmbox.

    $ wget https://github.com/dobroweb/rhythmbox-plugin-yandex-music/archive/refs/tags/0.1-alpha.tar.gz
    $ tar -zxvf rhythmbox-plugin-yandex-music*.tar.gz
    $ mkdir -p ~/.local/share/rhythmbox/plugins/
    $ mv rhythmbox-plugin-yandex-music* ~/.local/share/rhythmbox/plugins/yandex-music

После чего активировать плагин в настройках Rhythmbox.

## Настройка
Все возможности будут доступны только после авторизации в сервисе Яндекс.Музыка и при наличии активной подписки.

Запустите Rhythmbox, выберите источник "Мне нравится" из группы "Яндекс.Музыка" и авторизуйтесь, используя ваш логин и пароль. Плагин хранит только token, который генерирует Яндекс, и использует его для дальнейшей авторизации.
