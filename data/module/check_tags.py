import urllib.parse
import asyncio
import aiohttp
import time
import json
import sys

from module import search_pic

# Собирает словарь списков с ключами вида:
# {'artist':[{'id', 'format', 'name', 'full', 'url', 'artist', 'date', 'safe'},{...}],...}
async def first(l_artist, q):
    
    # Заполняем словарь новых пикч следуя списку артистов
    future = {}
    for artist in l_artist:
        
        qloc = q.copy()
        
        # Проверяем тег артиста
        if not artist.startswith('artist:'):
            artist = 'artist:' + artist
        
        qloc.append(artist)
        qloc = ','.join(qloc)

        url = {
                'per_page': 50,
                'sf': 'first_seen_at',
                'sd': 'desc',
                'filter_id': 56027,
                'q': qloc
               }
        
        url = urllib.parse.urlencode(url, quote_via=urllib.parse.quote_plus)

        l = await asyncio.create_task(search_pic.search_derp(url))
        
        future[artist] = l
        
        # Задержка между запросами чтобы не нашлепали по ручкам
        await asyncio.sleep(21)
        
    return future



# функция очистки списка от старых пикч
# сохраняет самую последнюю запощенную в выходе
# {'artist':[{'id', 'format', 'name', 'full', 'url', 'artist', 'date', 'safe'},{...}],...}
async def second(past):
    
    future = {}
    
    for artist in past:
        l = []

        # Время устаревания в секундах
        old_age = 3600

        for i in range(len(past[artist])):
            
            if old_age > time.time() - past[artist][i]['date']:
                l.append(past[artist][i])
        
        # Запись последней пикчи если ни одна не прошла проверку по времени
        if not l:
            l.append(past[artist][0])
        
        future[artist] = l
        
    return future



# Сравниваем старые пикчи с новыми и готовим новый словарь для обновления
# {'artist':[{'id', 'format', 'name', 'full', 'url', 'artist', 'date', 'safe'},{...}],...}
async def third(past, last=None):

    write = {}; new = {}
    for artist in past:
        
        l = []; k = []
        
        # Проверка на случай отсутствия записей
        # Происходит когда в список артистов был добавлен новый
        # И для него еще нет данных
        check = last.get(artist)
        if check:

            for i in range(len(past[artist])):
                for j in range(len(last[artist])):
            
                    # Перебираем старый словарь сравнивая с новым если есть совпадение - записываем и выходим
                    if past[artist][i]['id'] == last[artist][j]['id']:
                        l.append(past[artist][i])
                        break
                
                # Если прошли по всем ID старого словаря и не получили совпадения - то ID новый, записываем
                else:
                    
                    #Проверка по старшенству ID
                    # if past[artist][i]['id'] < last[artist][0]['id']:
                        # break
                        
                    l.append(past[artist][i])
                    k.append(past[artist][i])

                continue

        else:
            # Добовляем в словарь данные по новому артисту
            l = past[artist]
        
        write[artist] = l
        new[artist] = k
    
    return write, new
    


# Формируем сообщеня отслеживающим
async def followers(new, l_followers):

    f = {}
    
    for key in new:
        
        images = new.get(key)
        if not images:
            continue
            
        for i in range(len(images)):

            follower = l_followers.get(images[i]['artist'])
            if not follower:
                continue
                
            for j in range(len(follower)):
                    string = 'У артиста '+ images[i]['artist'] +' есть обновления!'
                    
                    for i in range(len(images)):
                        if images[i]['safe']:
                            string += '\n' + images[i]['url'] + ' '
                        else:
                            string += '\n**NSFW**\n<' + images[i]['url'] + '> '
                        
                    f[follower[j]] = [string]


    return f



if __name__ == "__main__":
    import search_pic
    
    artist_path = {
            'list': '../artist/list.json',
            'filter': '../artist/filter.json',
            'storage': '../artist/storage.json',
            'followers': '../artist/followers.json'}
            
    
    # Загружаем
    # Список художников
    try:
        with open(artist_path['list'], 'r') as f:
            l_artist = json.load(f)
    
    except FileNotFoundError:
        print(str(e))
    except Exception as e:
        print(str(e))
    else:
        if not l_artist:
            print('Список художников пуст')


    # Теги для фильтрации
    try:
        with open(artist_path['filter'], 'r') as f:
            q = json.load(f)
    except Exception as e:
        print(str(e))
        q = []


    # Последние пикчи
    # Если ошибка чтения - создаем пустой словарь
    try:
        with open(artist_path['storage'], 'r') as f:
            last = json.load(f)
    except Exception as e:
        print(str(e))
        last = {}


    # Список фолловеров
    try:
        with open(artist_path['followers'], 'r') as f:
            l_follow = json.load(f)
    except Exception as e:
        print(str(e))
    


    # Последовательно пробегаемся по первой, второй и третьей функции
    # {'artist':[{'id', 'format', 'name', 'full', 'url', 'artist', 'date', 'safe'},{...}],...}
    try:
        temp = asyncio.run(first(l_artist, q))
        temp = asyncio.run(second(temp))
        
        write, new = asyncio.run(third(temp, last))
    except Exception as e:
         print(str(e) + '\nСлежение за художниками остановлено')
         sys.exit(0)


    # Записываем обновленный словарь
    # with open('../artist/follow.json', 'w') as f:
        # json.dump(write, f, indent=4)
    
    try:
        l = asyncio.run(followers(new, l_follow))
    except:
        pass
        
    print(l)