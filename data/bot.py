from discord.ext import commands
import importlib, sys
import urllib.parse
import subprocess
import asyncio
import aiohttp
import discord
import time
import json
import io
import re 

from module import check_tags
from module import search_pic
from module import req
from module import rnd

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


async def reverse_search(message, url):

    # Добавляем эмотикон лупы к сообщению-запросу
    await message.add_reaction('\U0001F50D')
    
    answer = await asyncio.create_task(search_pic.reverse_derp(url))
    
    await message.remove_reaction('\U0001F50D', bot.user)
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
    l = await asyncio.create_task(search_pic.search_derp(string))

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
    

# Дополнительный слой для слежения за художниками
async def bg_task_follow_additional_layer(artist_path):

    # Загружаем
    # Список художников
    try:
        with open(artist_path['list'], 'r') as f:
            l_artist = json.load(f)
    
    except FileNotFoundError:
        await bot.get_channel(ID['LOGS']).send(str(e))
    except Exception as e:
        await bot.get_channel(ID['LOGS']).send(str(e))
    else:
        if not l_artist:
            await bot.get_channel(ID['LOGS']).send(str('Список художников пуст'))

    # Теги для фильтрации
    try:
        with open(artist_path['filter'], 'r') as f:
            q = json.load(f)
    except Exception as e:
        await bot.get_channel(ID['LOGS']).send(str(e))
        q = []

    # Последние пикчи
    # Если ошибка чтения - создаем пустой словарь
    try:
        with open(artist_path['storage'], 'r') as f:
            last = json.load(f)
    except Exception as e:
        await bot.get_channel(ID['LOGS']).send(str(e))
        last = {}

    # Список фолловеров
    try:
        with open(artist_path['followers'], 'r') as f:
            l_follow = json.load(f)
    except:
        l_follow = {}
    

    # Последовательно пробегаемся по первой, второй и третьей функции
    # {'artist':[{'id', 'format', 'name', 'full', 'url', 'artist', 'date', 'safe'},{...}],...}
    try:
        temp = await asyncio.create_task(check_tags.first(l_artist, q))
        temp = await asyncio.create_task(check_tags.second(temp))
            
        write, new = await asyncio.create_task(check_tags.third(temp, last))
    except Exception as e:
        await bot.get_channel(ID['LOGS']).send(str(e) + '\nСлежение за художниками приостановлено')
        return

    # Записываем обновленный словарь
    with open(artist_path['storage'], 'w') as f:
        json.dump(write, f, indent=4)
    
    try:
        notify = await asyncio.create_task(check_tags.followers(new, l_follow))
    except:
        notify = {}
    
    return new, notify


# Функция управления списком фолловеров
async def manage_followers(artist_path):

    try:
        with open(artist_path['mem'], 'r') as f:
            mem = json.load(f)
    except:
        # Выход если нет сохраненных сообщений
        return

    try:
        with open(artist_path['followers'], 'r') as f:
            followers = json.load(f)
    except:
        followers = {}
    
    for i in range(len(mem)):
        for artist in mem[i]:

            message = await bot.get_channel(ID['PAINT']).fetch_message(mem[i][artist])
            
            plus = followers.get(artist)
            
            if not plus:
                plus = []


            # Сначала собираем все зеленые
            for reaction in message.reactions:
                if '\U0001F7E2' in reaction.emoji:
                    users = await reaction.users().flatten()
                    for user in users:
                        if user == bot.user:
                            continue
                            
                        plus.append(user.id)

            plus = list(set(plus))
            
            # Удаляем из списка зеленых красные
            for reaction in message.reactions:
                if '\U0001F534' in reaction.emoji:
                    users = await reaction.users().flatten()
                    for user in users:
                        if user == bot.user:
                            continue
                            
                        plus.remove(user.id)
                        
                        text = 'Привет! Ты отписан от обновлений артиста ' + artist
                        try:
                            user = await bot.fetch_user(user.id)
                            await user.send(text)
                        except:
                            pass
            
            
            old = followers.get(artist)
            
            if old:
                for user_id in plus:
                    if not user_id in old:
                        
                        text = 'Привет! Ты подписан на обновления артиста ' + artist
                        try:
                            user = await bot.fetch_user(user_id)
                            await user.send(text)
                        except:
                            pass
            
            else:
                if plus:
                    for user_id in plus:
                        text = 'Привет! Ты подписан на обновления артиста ' + artist
                        try:
                            user = await bot.fetch_user(user_id)
                            await user.send(text)
                        except:
                            pass

            followers[artist] = plus
    
    # Записываем фолловеров
    while True:
        try:
            with open(artist_path['followers'], 'w') as f:
                json.dump(followers, f, indent=4)
            break
        except:
            await asyncio.sleep(rnd.time(5))

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
    l = await asyncio.create_task(search_pic.search_derp(string))

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


# Фоновая задача снижения усталости
async def bg_task_lassitude():                                        
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
    
    artist_path = {
        'mem': './artist/mem.json',
        'list': './artist/list.json',
        'filter': './artist/filter.json',
        'storage': './artist/storage.json',
        'followers': './artist/followers.json'}
    
    # Загружаем ID запощенных сообщений
    try:
        with open(artist_path['mem'], 'r') as f:
            mem = json.load(f)
    except:
        mem = []


    while True:
        
        # Получаем словарь новых и словарь подписчиков
        try:
            new, notify = await asyncio.create_task(bg_task_follow_additional_layer(artist_path))
        except Exception as e:
            await bot.get_channel(ID['LOGS']).send('Повторная попытка через 20 минут.')
            await asyncio.sleep(1200)
            continue


        # Уведомляем подписчиков об обновлении
        for user_id in notify:
            text = notify[user_id][0]
            try:
                user = await bot.fetch_user(user_id)
                await user.send(text)
            except:
                pass
        
        # Готовим пост в канал
        for artist in new:
            if new[artist]:
                for i in range(len(new[artist])):
                    
                    if new[artist][i]['safe']:
                        text = 'Посмотрите какую крутую новую картинку нарисовал ' + new[artist][i]['artist'] + '\n' + new[artist][i]['url']
                    else:
                        text = 'Посмотрите какую крутую новую картинку нарисовал ' + new[artist][i]['artist'] + '! Ой-ёй!\n<' + new[artist][i]['url'] + '>'
                    
                    # Записываем данные о запощенном сообщении
                    temp = await bot.get_channel(ID['PAINT']).send(text)
                    
                    # Проставляем эмотиконы
                    message = await bot.get_channel(ID['PAINT']).fetch_message(temp.id)
                    await message.add_reaction('\U0001F7E2')
                    await message.add_reaction('\U0001F534')
                    
                    # Запоминаем ID сообщений
                    mem.append({new[artist][i]['artist']: temp.id})
                    
                    await asyncio.sleep(rnd.time(5))
        
        # Забываем старые сообщения
        while len(mem) > 5:
            mem.pop(0)

        # Записываем ID сообщений
        while True:
            try:
                with open(artist_path['mem'], 'w') as f:
                    json.dump(mem, f, indent=4)
                break
            except:
                await asyncio.sleep(rnd.time(5))
        
        # Проверяем фолловеров
        try:
            await asyncio.create_task(manage_followers(artist_path))
        except:
            pass
        
        await asyncio.sleep(rnd.time(300))



# фоновая задача отправки
async def bg_task_post():                                             
    await bot.wait_until_ready()
    while True:
        await asyncio.sleep(rnd.time(7500))

        hour = time.localtime(time.time()).tm_hour
        
        # утро
        if hour >= 6 and hour < 9:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C+morning+ponies%2C+score.gte%3A50'
        
        # ночь
        elif hour > 22 or hour < 5:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C+sleep%2C+score.gte%3A50'
        
        # зубки
        elif hour >= 5 and hour < 6:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rainbowbat%2C+score.gte%3A50'
        
        # день
        else:
            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C+score.gte%3A120'
        

        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search_pic.search_derp(string))
        
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
        
        
        # Команды для запроса помощи
        check_help = ['помощ', 'помоч', 'help']
        check_help_true = any(check_help in message.content.lower() for check_help in check_help)
        
        if check_help_true:
            lassitude += 5
            
            if message.channel.id == ID['PAINT']:
                text = 'Ха-ха! Ты захотел узнать как это работает? \nОчень просто! Если ты нажмешь на зеленый кружок \U0001F7E2 под рисунком артиста - я запомню тебя, и обязательно разыщу для того чтобы показать его новые рисунки! \nЕсли ты вдруг захочешь "отписаться" от моих крутых уведомлений - нажми на красный кружок \U0001F534 под рисунком больше ненужного тебе, одинокого и грустного артиста. \n\nИ запомни: Один красный - сильнее тысячи зеленых!'
                
                await message.reply('```' + text + '```', mention_author=True)
                
        
        
        # Ищем ссылки в прикрепленных или в .content
        reply_attach_url, message_attach_url = await asyncio.create_task(message_func(message))
        
        # Команды для запуска поиска
        check_find = ['найди', 'поищи', 'find']
        check_find_true = any(check_find in message.content.lower() for check_find in check_find)
        
        if check_find_true and not message.channel.id == ID['PAINT']:
                    
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
        if check_post_true and not bot.user == reply_author and not message.channel.id == ID['PAINT']:
            
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

    
    # Постит пикчи с Дэш при упоминании
    # В сейф-каналах
    if lassitude < 6 and bot.user in message.mentions and not bot.user == reply_author and not message.channel.id == ID['CLOP'] and not message.channel.id == ID['DARK'] and not message.channel.id == ID['PAINT']:
            
        lassitude += 1
        
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C-anthro%2C+score.gte%3A150'
            
        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search_pic.search_derp(string))

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
            l = await asyncio.create_task(search_pic.search_derp(string))
            
            text = 'Тебе нравится, конееб?'

            task = await asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name'], text))
            
        return

    # В дарке
    if lassitude < 7 and bot.user in message.mentions and not bot.user == reply_author and message.channel.id == ID['DARK']:
        lassitude += 1
        
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191483&q=+solo%2C+score.gte%3A10'
            
        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search_pic.search_derp(string))

        task = await asyncio.create_task(upload(message, l[0]['full'], l[0]['url'], l[0]['name']))
        return

    return 


bot.loop.create_task(bg_task_lassitude()) 
bot.loop.create_task(bg_task_follow())
bot.loop.create_task(bg_task_post())
bot.run(TOKEN[0])