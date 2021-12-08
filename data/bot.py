from discord.ext import commands
import importlib, sys
import subprocess
import asyncio
import aiohttp
import discord
import time
import json
import io
import re 

from module import rnd
from module.status import status

# Загрузка настроек
# ID каналов
with open ('./config/channel.json', 'r') as f:
    ID = json.load(f)

# Токен бота
with open ('./config/token.json', 'r') as f:
    TOKEN = json.load(f)

# Список цитат
with open ('./data/citat.json', 'r') as f:
    CITATLIST = json.load(f)

# Список персонажей
with open ('./data/character.json', 'r') as f:
    CHARACTER = json.load(f)

# Список персонажей
with open ('./data/tag.json', 'r') as f:
    TAG = json.load(f)

# Список URL с бухлом
with open ('./data/alco.json', 'r') as f:
    ALCO = json.load(f)

alco_lassitude = 0
lassitude = 0
recall = None

async def search(string):

    l = []
    
    url = 'https://www.derpibooru.org/api/v1/json/search/images?' + string
    
    # Получаем список изображений
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            response = await resp.json()
    
    images = response.get('images')
    
    if images:
        for i in range(len(images)):
            if 'tags' in images[i]:
                
                # Ищем тег артиста
                for tag in images[i]['tags']:
                    if 'artist:' in tag:
                        artist = tag[7:]
                        break
                else:
                    artist = 'None artist'
                
                # Ищем рейтинг
                for tag in images[i]['tags']:
                    if tag == 'safe':
                        safe = True
                        break
                else:
                    safe = False

                # .svg не поддерживается дискордом, поэтому заменяем на .png
                if images[i]['format'] != 'svg':
                    name = str(images[i]['id']) + '.' + images[i]['format']
                else:
                    name = str(images[i]['id']) + '.png'
                                
            # исключение, когда находит пикчу без списка тегов
            # возможно такого не бывает. Но точно есть в реверсивном поиске
            else:
                safe = False
                name = 'blank.png'
            
            # Преобразуем дату загрузки в секунды от начала эпохи
            date = int(time.mktime(time.strptime(images[i]['first_seen_at'], '%Y-%m-%dT%H:%M:%SZ')))
            
            # Записываем результаты
            l.append({'id': images[i]['id'], 'format': images[i]['format'], 'name': name, 'full': images[i]['representations']['full'], 'url': ('https://www.derpibooru.org/images/' + str(images[i]['id'])), 'artist': artist.capitalize(), 'date': date, 'safe': safe})
            
    else:
        # Заглушка на случай ошибки
        l.append({'id': None, 'format': None, 'name': None, 'full': None, 'url': None, 'artist': 'None artist', 'date': None, 'safe': None})
        
    return l



async def reverse_search(message, url):

    # Добавляем эмотикон лупы к сообщению-запросу
    await message.add_reaction('\U0001F50D')
    
    l = []
    
    for k in range(0, 65, 5):
        
        url_dist = 'https://www.derpibooru.org/api/v1/json/search/reverse?url=' + url + '&distance=' + str(k/100.0)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url_dist) as resp:
                response = await resp.json()
                
        images = response.get('images')
        if images:
            if 'tags' in images[0]:
                for tag in images[0]['tags']:
                    if tag == 'safe':
                        safe = True
                        break
                else:
                    safe = False
            else:
                safe = False        

            
            l.append({'url': ('https://www.derpibooru.org/images/' + str(images[0]['id'])), 'distance': k, 'safe': safe})
            break                       
        
        else:
            # если с текущим distance нет результата - ждем
            await asyncio.sleep(0.1)    
                    
    else:
        # результат не найден
        l.append({'url': False, 'distance': k, 'safe': False})
        
    # Формируем ответ
    if l[0]['url']:
        
        if l[0]['distance'] < 20:
            answer = 'Я нашла! Изи-пизи.\n'
            
        elif l[0]['distance'] < 35:
            answer = 'Выглядит похоже...\n'
            
        elif l[0]['distance'] < 45:
            answer = 'Было не просто гоняться за этой штукой!\n'
            
        else:
            answer = 'Хм... Как думаешь, это то что надо?\n'
            

        if l[0]['safe']:
            answer += l[0]['url']
        else:
            answer += '*Возможно NSFW*\n<' + l[0]['url'] + '>'
            
    else:
        answer = 'Извини, Анон, ничего не нашла...'
        
        
    await message.reply(answer, mention_author=True)



async def post_pic(message):
    global recall
    
    j = 0;  answer = '';    string = '';     detect = '';    service = False
    
    for key in TAG:
        
        if '*сервис' in message.content.lower():
            service = True


        if key in message.content.lower():
            if string:
                string += '%2C' + TAG[key]
            else:
                string += TAG[key]

            if detect:
                detect += ', ' + TAG[key]
            else:
                detect += TAG[key]
    
    for key in CHARACTER:

        
        if key in message.content.lower():
            if string:
                string += '%2C' + CHARACTER[key]
            else:
                string += CHARACTER[key]
            j += 1
                
            if detect:
                detect += ', ' + CHARACTER[key]
            else:
                detect += CHARACTER[key]
                
    
    # проверка на парные действия
    if j > 0:
        check_duo = ['буп', 'кусь', 'кусб', 'хвать', 'boop', 'bite', 'hug', 'сосет', 'сосут']
        check_duo_true = any(check_duo in message.content.lower() for check_duo in check_duo)
    
        if check_duo_true:
            j += 1
    
    if j == 1:
        if string:
            string += '%2C+solo'
        else:
            string += '+solo'
        
    if not string:
        answer = 'Я не поняла ни единого слова, поэтому покажу свой любимый рисунок!'
        string += '+pony%2C+score.gte%3A450'
    
    
    if service:
        if detect:
            await message.reply(('Эти слова я поняла: ' + detect), mention_author=True)
        else:
            await message.reply('Ничего не разобрать...', mention_author=True)
        return
        
    # Запоминаем последний запрос
    recall = string
        
    # фильтр для клоп-канала
    if message.channel.id == ID['CLOP']:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191484&q=' + string
    
    # фильтр для дарк-канала
    elif message.channel.id == ID['DARK']:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191483&q=' + string
    
    # любой другой видимый канал - постит сейф
    else:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=' + string
    
    # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
    l = await asyncio.create_task(search(string))

    task = asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name'], answer))
    return
    
    
    
async def upload(message, url, derp_url, name, answer = None):
    
    # Прерываем, если получен пустой ответ
    if not derp_url:
        answer = 'Сюда нельзя постить такое!'
        return await message.reply(answer, mention_author=True)
        
    if not answer:
        answer = '<' + derp_url + '>'
    else:
        answer += '\n<' + derp_url + '>'
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await message.reply('Не могу загрузить крутую картинку...', mention_author=True)
            data = io.BytesIO(await resp.read())
            await message.reply(answer, file=discord.File(data, name), mention_author=True)
    
    return


# Функция повтора
async def repeat(message, string):
    # Все проверки выполняются для того, чтобы избежать ситуации
    # когда запрос был сделан в одном канале, а повтор в другом
    
    # фильтр для клоп-канала
    if message.channel.id == ID['CLOP']:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191484&q=' + string
    # фильтр для дарк-канала
    elif message.channel.id == ID['DARK']:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191483&q=' + string
    # любой другой видимый канал - постит сейф
    else:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=' + string
    
    # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
    l = await asyncio.create_task(search(string))

    task = asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name'], 'Ха-ха! Так и знала, что тебе понравится!'))
    return



async def alco(message, url):
    await bot.wait_until_ready()
    global alco_lassitude
    
    alco_lassitude += 50

    name = re.findall(r'https://derpicdn.net/img/view/\d+/\d+/\d+/(\d+[.]\w+)', url)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return await message.reply('Не могу загрузить крутую картинку...', mention_author=True)
            data = io.BytesIO(await resp.read())
            await message.reply(file=discord.File(data, name[0]), mention_author=False)
    
    return


async def message_func(message):
    if message.reference:
        ref_id = re.split(' |=', str(message.reference))
        reply = await bot.get_channel(int(ref_id[4])).fetch_message(int(ref_id[2]))
        
        if reply.attachments:
            # разделяем строку по знаку одиночной кавычки, чтобы получить чистую ссылку
            reply_attach_url = re.split('\'', str(reply.attachments))
            reply_attach_url = reply_attach_url[3]
            
        else:
            reply_attach_url = re.findall(r'https?:\/\/\S+', str(reply.content))
            if reply_attach_url:
                reply_attach_url = reply_attach_url[0]
            else:
                reply_attach_url = None
    else:
        reply_attach_url = None
    
    
    if message.attachments:
        # разделяем строку по знаку одиночной кавычки, чтобы получить чистую ссылку
        message_attach_url = re.split('\'', str(message.attachments))
        message_attach_url = message_attach_url[3]
        
    else:
        message_attach_url = re.findall(r'https?:\/\/\S+', str(message.content))
        
        if message_attach_url:
            message_attach_url = message_attach_url[0]
        else:
            message_attach_url = None
            
    return reply_attach_url, message_attach_url



async def reply_func(message):
    if message.reference:
        id_reference = re.split(' |=', str(message.reference))
        reply = await bot.get_channel(int(id_reference[4])).fetch_message(int(id_reference[2]))
        reply_author = reply.author
    else:
        reply_author = None
            
    return reply_author



async def bg_task_lassitude():                                        # фоновая задача снижения усталости
    await bot.wait_until_ready()
    global alco_lassitude
    global lassitude
    global recall
    
    while True:
        await asyncio.sleep(rnd.time(80))

        if lassitude > 0:
            lassitude -= 1 
        
        if alco_lassitude > 0:
            alco_lassitude -= 1 
            
        if lassitude < 1 and recall:
            recall = None


# фоновая задача слежения за художниками
# функция принудительно замедлена, т.к. высокой скорости исполнения от нее не требуется
async def bg_task_follow():                                  
    await bot.wait_until_ready()
    
    while True:
        
        # Загружаем список художников
        artist_list = None
        while not artist_list:
            try:
                with open('./artist/list.json', 'r') as f:
                    artist_list = json.load(f)
                    
            except:
                await bot.get_channel(ID['LOGS']).send('Ошибка открытия списка художников')
                print('Ошибка открытия списка художников')
                await asyncio.sleep(120)
                
            else:
                if not artist_list:
                    print('Список художников пуст')
                    
                    # Завершаем функцию если список художников пуст (!!!)
                    return
            
            
        await asyncio.sleep(1)

        # Загружаем последние пикчи
        # Если файла нет - создаем пустой словарь
        try:
            with open('./artist/follow.json', 'r') as f:
                last_pic = json.load(f)
        except IOError:
            last_pic = {}

        await asyncio.sleep(1)

        # Заполняем словарь новых пикч следуя списку артистов
        new_list = {}
        for artist in artist_list:

            tag = '-literal+mindfuck%2C-gas+mask+fetish%2C-syringe%2C-pregnant%2C-dollified%2C-encasement%2C+-art+pack%3Aroyal+horns%2C'

            string = 'per_page=21&sf=first_seen_at&sd=desc&filter_id=56027&q=' + tag + '+artist%3A' + artist
            l = await asyncio.create_task(search(string))

            await asyncio.sleep(7)

            if not l:
                print('У', artist, 'пустая выдача')
            
            new_list[artist] = l
            

        # Очищаем список от старых пикч
        clear_list = {}
        for artist in new_list:
            
            l = []
    
            # Время устаревания в секундах
            old_age = 3600
    
            for i in range(len(new_list[artist])):
                
                await asyncio.sleep(1.3)
                
                if old_age > time.time() - new_list[artist][i]['date']:
                    l.append(new_list[artist][i])
            
            if not l:
                l.append(new_list[artist][0])
            
            clear_list[artist] = l


        # Сравниваем старые пикчи с новыми и готовим новый словарь для обновления
        future_list = {}
        for artist in clear_list:
            
            l = []
            
            # Проверка на случай отсутствия записей
            # Происходит когда в список артистов был добавлен новый
            # И для него еще нет данных
            check = last_pic.get(artist)
            if check:
                for i in range(len(clear_list[artist])):
                    for k in range(len(last_pic[artist])):
                
                        # Перебираем старый словарь сравнивая с новым если есть совпадение - записываем и выходим
                        if clear_list[artist][i]['id'] == last_pic[artist][k]['id']:
                            l.append(clear_list[artist][i])
                            await asyncio.sleep(1)
                            break
                            
                    # Если прошли по всем ID старого словаря и не получили совпадения - то ID новый, записываем
                    else:
                        
                        l.append(clear_list[artist][i])
                        
                        if clear_list[artist][i]['id'] < last_pic[artist][0]['id']:
                            break
                        
                        if clear_list[artist][i]['safe']:
                            text = 'Посмотрите какую крутую новую картинку нарисовал ' + clear_list[artist][i]['artist'] + '!\n<' + clear_list[artist][i]['url'] + '>'
                            name = clear_list[artist][i]['name']
                        else:
                            text = 'Посмотрите какую крутую новую картинку нарисовал ' + clear_list[artist][i]['artist'] + '! Ой-ёй!' + '\n<' + clear_list[artist][i]['url'] + '>'
                            name = 'SPOILER_' + clear_list[artist][i]['name']
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(clear_list[artist][i]['full']) as resp:
                                data = io.BytesIO(await resp.read())
                                
                                # если появляется ошибка при прямой загрузке файла - просто крепим ссылку
                                try:
                                    await bot.get_channel(ID['PAINT']).send(text, file=discord.File(data, name))
                                except:
                                    
                                    if clear_list[artist][i]['safe']:
                                        text = 'Посмотрите какую крутую новую картинку нарисовал ' + clear_list[artist][i]['artist'] + '\n' + clear_list[artist][i]['url']
                                    else:
                                        text = 'Посмотрите какую крутую новую картинку нарисовал ' + clear_list[artist][i]['artist'] + '! Ой-ёй!\n<' + clear_list[artist][i]['url'] + '>'

                                    await bot.get_channel(ID['PAINT']).send(text)
                        continue

            else:
                # Добовляем в словарь данные по новому артисту

                l = clear_list[artist]
                
            future_list[artist] = l

        # Записываем обновленный словарь
        with open('./artist/follow.json', 'w') as f:
            json.dump(future_list, f, indent=4)


async def bg_task_post():                                             # фоновая задача отправки 
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(rnd.time(6000))

        hour = time.localtime(time.time()).tm_hour
            
        # Сделана поправка на +0 часовой пояс (-3 от Москвы)
        if hour >= 3 and hour < 6:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C+morning+ponies%2C+score.gte%3A50'
                    
        elif hour > 19 or hour < 1:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C+sleep%2C+score.gte%3A50'
                
        elif hour >= 1 and hour < 3:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rainbowbat%2C+score.gte%3A50'
                
        else:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C+score.gte%3A120'
        

        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search(string))
        
        async with aiohttp.ClientSession() as session:
            async with session.get(l[0]['full']) as resp:
                if resp.status != 200:
                    return await bot.get_channel(ID['PICS']).send('Не могу загрузить крутую картинку...')
                data = io.BytesIO(await resp.read())
                await bot.get_channel(ID['PICS']).send('<' + l[0]['url'] + '>', file=discord.File(data, l[0]['name']))


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)                
bot.remove_command('help')


@bot.event
async def on_ready():
    await bot.get_channel(ID['LOGS']).send('<t:' + str(int(time.time())) + '>')
    print('#'*50  + '\n#' + ' '*10 + 'Бот \'Рядужная филли\' запущен' + ' '*10 + '#\n' + '#'*50)



@bot.event
async def on_message(message):
    if message.author == bot.user or message.channel.id == ID['TEST']:
        return


    # Алкофункция. Реагирует на ключевые слова в сообщении и уходит в долгий сон
    global alco_lassitude

    check_alco = ['водоч', 'водк', 'сидр', 'виски']
    check_alco_true = any(check_alco in message.content.lower() for check_alco in check_alco)
    
    if check_alco_true and alco_lassitude < 3:
        task = asyncio.create_task(alco(message, rnd.choice(ALCO)))
        return
    
    global lassitude
    
    # Ищем имя в ответах
    reply_author = await asyncio.create_task(reply_func(message))
    
    # Если имя бота есть в сообщении или ответе - заходим
    if bot.user == reply_author or bot.user in message.mentions:
        
        # Начисляем усталость
        if lassitude > 10:
            return
            
        elif lassitude == 10:
            lassitude += 5
            return await message.reply('Я устала...')
            
        elif lassitude == 9:
            lassitude += 1
            await message.reply('Еще разок, и спать...')
                
        else:
            lassitude += 1
        
        # Ищем ссылки в прикрепленных или в .content
        reply_attach_url, message_attach_url = await asyncio.create_task(message_func(message))

        # Команды для запуска поиска
        check_find = ['найди', 'поищи', 'find']
        check_find_true = any(check_find in message.content.lower() for check_find in check_find)
        
        if check_find_true:
                    
            if not reply_attach_url and not message_attach_url:
                task = asyncio.create_task(post_pic(message))
                return
                           
            if message_attach_url:
                task = asyncio.create_task(reverse_search(message, message_attach_url))
                return
                    
            if reply_attach_url:
                task = asyncio.create_task(reverse_search(message, reply_attach_url))
                return
                    
            return await message.reply('Повторите команду.', mention_author=True)

        # Проверяем сначала словарь персонажей и если не находим - проверяем теги
        check_post_true = any(check_post in message.content.lower() for check_post in CHARACTER)
        if not check_post_true:
            check_post_true = any(check_post in message.content.lower() for check_post in TAG)
            
        # Заходим только если было прямое упоминание, без упоминания бота в ответе
        # Сделано для исключения реакции на ответ с текстом на ответ бота (комментарий на пост от юзера)
        # Т.к. словарь содержит очень много ключей, которые могут вызывать ложные срабатывания и вобще
        if check_post_true and not bot.user == reply_author:
            
            task = asyncio.create_task(post_pic(message))
            return 
            
        check_repeat = ['повто', 'еще', 'ещё']
        check_repeat_true = any(check_repeat in message.content.lower() for check_repeat in check_repeat)
        
        if check_repeat_true:
            if not recall:
                await message.reply('Я не помню, что у меня просили раньше.')
            else:
                # Повторяем последний запрос
                task = asyncio.create_task(repeat(message, recall))
            return
       
       
    if message.channel.id == ID['LOGS'] and 'стат' in message.content.lower():
        return await bot.get_channel(ID['LOGS']).send('```' + status('Rainbow-filly') + '```')
    
    
    if message.channel.id == ID['LOGS'] and 'бекап' in message.content.lower():
        task = asyncio.create_task(bkp(message))
    
    
    
    # Постит пикчи с Дэш при упоминании
    # В сейф-каналах
    if lassitude < 6 and bot.user in message.mentions and not bot.user == reply_author and not message.channel.id == ID['CLOP'] and not message.channel.id == ID['DARK']:
            
        lassitude += 1
        
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C-anthro%2C+score.gte%3A150'
            
        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search(string))

        task = await asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name'], rnd.choice(CITATLIST)))
        
        if lassitude >= 6:
            await message.channel.send('... Уф! Валюсь с ног! Пришло время поспать :zzz:')
        return 
        
        
    # Если ткнули ник в особых каналах
    # В клопе
    if lassitude < 5 and bot.user in message.mentions and not bot.user == reply_author and message.channel.id == ID['CLOP']:
        lassitude += 1
        
        if lassitude < 4:
            return await message.reply('Ай! Не тыкай в меня своими сосисками!')
            
        elif lassitude == 4:
            return await message.reply('Ты хочешь увидеть мое секретное местечко?')
            
        elif lassitude == 5:

            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191484&q=-oc%2C+solo%2C+rd%2C+vulva%2C+pony%2C-anthro%2C+score.gte%3A290'
            
            #Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
            l = await asyncio.create_task(search(string))
            
            text = 'Тебе нравится, конееб?'

            task = await asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name'], text))
            
        return

    # В дарке
    if lassitude < 7 and bot.user in message.mentions and not bot.user == reply_author and message.channel.id == ID['DARK']:
        lassitude += 1
        
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191483&q=+solo%2C+score.gte%3A10'
            
        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search(string))

        task = await asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name']))
        return

    return 


bot.loop.create_task(bg_task_lassitude()) 
bot.loop.create_task(bg_task_follow())
bot.loop.create_task(bg_task_post())
bot.run(TOKEN[0])