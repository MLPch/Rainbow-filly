import asyncio
import io
import json
import re
import time

import aiohttp
import disnake
from disnake.ext import commands
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

from config import config
from module import check_tags
from module import rnd
from module import search_pic

# Загрузка настроек
# ID каналов
with open('./config/channel.json', 'r') as f:
    ID = json.load(f)

# Список цитат
with open('./data/citat.json', 'r') as f:
    CITATLIST = json.load(f)

# Список персонажей
with open('./data/character.json', 'r') as f:
    CHARACTER = json.load(f)

# Список тегов
with open('./data/tag.json', 'r') as f:
    TAG = json.load(f)

# Список URL с бухлом
with open('./data/alco.json', 'r') as f:
    ALCO = json.load(f)

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

    j = 0
    answer = ''
    string = ''
    detect = {}
    service = False

    try:
        message_text = re.sub(r'(<\W\d+>)', '', message.content.lower())
        summary = message_text.strip()
    except:
        return await message.reply('Ничего непонятно! Ля-ля-ля-ля!')

    if 'artist:' in message_text:
        artist_list = re.findall(r'(artist:\S+)', message_text)

        for artist in artist_list:
            message_text = message_text.replace(artist, '?' * len(artist))
            detect[artist] = 100

    for key in TAG:

        if key in message_text:
            message_text = message_text.replace(key, '?' * len(key))

            detect[key] = 100

            continue

        procent = fuzz.ratio(key, message_text)

        if procent > 65:
            detect[key] = procent

    # Сортировка по убыванию процентов
    detect = dict(sorted(detect.items(), key=lambda x: x[1], reverse=True))

    for key in detect:
        if 'artist:' in key:
            if string:
                string += '%2C' + key
            else:
                string += key

            continue

        if detect[key] == 100:
            if string:
                string += '%2C' + TAG[key]
            else:
                string += TAG[key]

            continue

        elif detect[key] < 100 and not string:

            string += TAG[key]
            break

    if not string:
        answer = 'Я не поняла ни единого слова, поэтому покажу свой любимый рисунок!'
        string += '+pony%2C+score.gte%3A450'

    # Запоминаем последний запрос
    recall = [string, message]

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

    # Логирование
    summary += '\n' + message_text.strip()
    summary += '\n' + str(dict(list(detect.items())[:5]))
    summary += '\n' + string.split('&q=', 1)[1]
    summary += '\nresult: ' + str(len(l))
    await bot.get_channel(ID['LOGS']).send(summary)

    if not l:
        return await message.reply('Я ничего не смогла найти.')

    task = asyncio.create_task(upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name'], answer))
    return


async def upload(message, size, url, derp_url, name, answer=None):
    # Прерываем, если получен пустой ответ
    if not derp_url:
        answer = 'Сюда нельзя постить такое!'
        return await message.reply(answer, mention_author=True)

    # size > 8Mb
    if size > 8103750:
        return await message.reply(derp_url, mention_author=True)

    if not answer:
        answer = '<' + derp_url + '>'
    else:
        answer += '\n<' + derp_url + '>'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = io.BytesIO(await resp.read())
                await message.reply(answer, file=disnake.File(data, name), mention_author=True)

    except:
        await message.reply(derp_url, mention_author=True)

    return


# Дополнительный слой для слежения за художниками
async def bg_task_follow_additional_layer(artist_path):
    # Загружаем
    # Список художников
    try:
        with open(artist_path['list'], 'r') as f:
            l_artist = json.load(f)

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

    # return new, notify
    return new


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
async def repeat(message, recall):
    # Все проверки выполняются для того, чтобы избежать ситуации
    # когда запрос был сделан в одном канале, а повтор в другом
    if not recall:
        return
    # фильтр для клоп-канала
    if message.channel.id == ID['CLOP']:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191484&q=' + recall[0]
    # фильтр для дарк-канала
    elif message.channel.id == ID['DARK']:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191483&q=' + recall[0]
    # любой другой видимый канал - постит сейф
    else:
        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=' + recall[0]

    # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
    l = await asyncio.create_task(search_pic.search_derp(string))

    # task = asyncio.create_task(upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name'], 'Ха-ха! Так и знала, что тебе понравится!'))
    task = asyncio.create_task(upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name']))
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


async def reply_author_func(message):
    try:
        return await bot.get_channel(message.reference.channel_id).fetch_message(message.reference.message_id)
    except:
        return None


# Фоновая задача снижения усталости
async def bg_task_lassitude():
    await bot.wait_until_ready()
    global lassitude
    global recall

    while True:
        await asyncio.sleep(rnd.time(80))

        if lassitude > 0:
            lassitude -= 1

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
            # new, notify = await asyncio.create_task(bg_task_follow_additional_layer(artist_path))
            new = await asyncio.create_task(bg_task_follow_additional_layer(artist_path))
        except Exception as e:
            await bot.get_channel(ID['LOGS']).send('Повторная попытка через 20 минут.')
            await asyncio.sleep(1800)
            continue

        # Проверяем что ответ не пустой
        if not new:
            await asyncio.sleep(2800)
            continue

        # Готовим пост в канал
        for artist in new:
            if new[artist]:
                for i in range(len(new[artist])):

                    if new[artist][i]['safe']:
                        # text = 'Посмотрите какую крутую новую картинку нарисовал ' + new[artist][i]['artist'] + '\n' + new[artist][i]['url'] + '\n' + '*Подписаться - :green_circle: Отписаться - :red_circle:*'
                        text = 'Посмотрите какую крутую новую картинку нарисовал ' + new[artist][i]['artist'] + '\n' + \
                               new[artist][i]['url']
                    else:
                        text = 'Посмотрите какую крутую новую картинку нарисовал ' + new[artist][i][
                            'artist'] + '! Ой-ёй!\n|| ' + new[artist][i]['url'] + ' ||'
                    # Записываем данные о запощенном сообщении
                    temp = await bot.get_channel(ID['PAINT']).send(text)

                    # Запоминаем ID сообщений
                    mem.append({new[artist][i]['artist']: temp.id})

                    await asyncio.sleep(5)

        # Забываем старые сообщения
        while len(mem) > 10:
            mem.pop(0)

        # Записываем ID сообщений
        while True:
            try:
                with open(artist_path['mem'], 'w') as f:
                    json.dump(mem, f, indent=4)
                break
            except:
                await asyncio.sleep(5)

        await asyncio.sleep(rnd.time(200))


# фоновая задача отправки
async def bg_task_post(channel_id, specific_tags, filter_id):
    await bot.wait_until_ready()

    hour = time.localtime(time.time()).tm_hour

    # утро
    if 7 <= hour < 8:
        string = f'page=1&sf=random&per_page=50&sd=desc&filter_id={filter_id}&q={specific_tags}%2C+morning+ponies'

    # ночь
    elif hour > 23 or hour < 7:
        string = f'page=1&sf=random&per_page=50&sd=desc&filter_id={filter_id}&q={specific_tags}%2C+sleep'

    # день
    else:
        string = f'page=1&sf=random&per_page=50&sd=desc&filter_id={filter_id}&q={specific_tags}'

    # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
    l = await asyncio.create_task(search_pic.search_derp(string))

    async with aiohttp.ClientSession() as session:
        async with session.get(l[0]['full']) as resp:
            data = io.BytesIO(await resp.read())
            await bot.get_channel(channel_id).send('<' + l[0]['url'] + '>', file=disnake.File(data, l[0]['name']))


async def save_members_in_dnp_channel_dacaoo():
    members = {}
    members_list = []

    for channel_name in DNP_channel:
        channel = bot.get_guild(953973375473156157).get_channel(DNP_channel[channel_name])

        members[f'NAME:{channel_name} ID:{DNP_channel[channel_name]}'] = {}
        members_list = channel.members

        for member in members_list:
            members[f'NAME:{channel_name} ID:{DNP_channel[channel_name]}'][member.name] = member.id

        await asyncio.sleep(1)

    with open("/home/dacaoo/python/rainbowfilly/members-in-dnp-channel.txt", 'w') as f:
        json.dump(members, f, indent=4)


async def bg_supervisor_post():
    await bot.wait_until_ready()

    for channel_name in bg_post_channels:
        bg_post_channels[channel_name][3] = rnd.time(26000) + int(time.time())

    while True:
        for channel_name in bg_post_channels:
            if bg_post_channels[channel_name][3] < int(time.time()):
                bg_post_channels[channel_name][3] = rnd.time(26000) + int(time.time())

                try:
                    await asyncio.create_task(bg_task_post(bg_post_channels[channel_name][0],
                                                           bg_post_channels[channel_name][1],
                                                           bg_post_channels[channel_name][2], ))
                except Exception as error:
                    await bot.get_channel(ID['LOGS']).send(f'Ошибка автопоста в {channel_name}.\n' + error)

        await asyncio.sleep(600)


async def add_permissions(payload, channel_id):
    member = bot.get_guild(payload.guild_id).get_member(payload.user_id)
    channel = bot.get_guild(payload.guild_id).get_channel(channel_id)

    await channel.set_permissions(member, read_messages=True,
                                  read_message_history=True,
                                  send_messages=True,
                                  attach_files=True,
                                  embed_links=True,
                                  add_reactions=True,
                                  create_public_threads=True,
                                  send_messages_in_threads=True,
                                  external_stickers=True,
                                  external_emojis=True,
                                  change_nickname=True,
                                  request_to_speak=True,
                                  create_instant_invite=False,
                                  kick_members=False,
                                  ban_members=False,
                                  administrator=False,
                                  manage_channels=False,
                                  manage_guild=False,
                                  view_audit_log=False,
                                  priority_speaker=False,
                                  stream=False,
                                  send_tts_messages=False,
                                  manage_messages=False,
                                  mention_everyone=False,
                                  view_guild_insights=False,
                                  connect=False,
                                  speak=False,
                                  mute_members=False,
                                  deafen_members=False,
                                  move_members=False,
                                  use_voice_activation=False,
                                  manage_nicknames=False,
                                  manage_roles=False,
                                  manage_webhooks=False,
                                  manage_emojis=False,
                                  use_application_commands=False,
                                  manage_events=False,
                                  manage_threads=False,
                                  create_private_threads=False,
                                  use_embedded_activities=False,
                                  moderate_members=False)


async def dnp_permissions(payload, channel_id):
    member = bot.get_guild(payload.guild_id).get_member(payload.user_id)
    channel = bot.get_guild(payload.guild_id).get_channel(channel_id)

    await channel.set_permissions(member, read_messages=True,
                                  read_message_history=True,
                                  attach_files=True,
                                  embed_links=True,
                                  add_reactions=True,
                                  create_public_threads=True,
                                  send_messages_in_threads=True,
                                  external_stickers=True,
                                  external_emojis=True,
                                  change_nickname=True,
                                  request_to_speak=True,
                                  send_messages=False,
                                  create_instant_invite=False,
                                  kick_members=False,
                                  ban_members=False,
                                  administrator=False,
                                  manage_channels=False,
                                  manage_guild=False,
                                  view_audit_log=False,
                                  priority_speaker=False,
                                  stream=False,
                                  send_tts_messages=False,
                                  manage_messages=False,
                                  mention_everyone=False,
                                  view_guild_insights=False,
                                  connect=False,
                                  speak=False,
                                  mute_members=False,
                                  deafen_members=False,
                                  move_members=False,
                                  use_voice_activation=False,
                                  manage_nicknames=False,
                                  manage_roles=False,
                                  manage_webhooks=False,
                                  manage_emojis=False,
                                  use_application_commands=False,
                                  manage_events=False,
                                  manage_threads=False,
                                  create_private_threads=False,
                                  use_embedded_activities=False,
                                  moderate_members=False)


async def remove_permissions(payload, channel_id):
    member = bot.get_guild(payload.guild_id).get_member(payload.user_id)
    channel = bot.get_guild(payload.guild_id).get_channel(channel_id)

    # Удаление из списка доступка к каналу, дальнейшее регулирование ложиться на роли юзера
    await channel.set_permissions(member, overwrite=None)

    # Прямой запрет на доступ к каналу, разрешение ролей игнорируются
    # await channel.set_permissions(member, read_messages            = False,
    # read_message_history     = False,
    # send_messages            = False,
    # attach_files             = False,
    # embed_links              = False,
    # add_reactions            = False,
    # create_public_threads    = False,
    # send_messages_in_threads = False,
    # external_stickers        = False,
    # external_emojis          = False,
    # change_nickname          = False,
    # request_to_speak         = False)


intents = disnake.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')


@bot.event
async def on_ready():
    await asyncio.sleep(3)

    await save_members_in_dnp_channel_dacaoo()

    try:
        with open('./data/ID_log.json', 'r') as f:
            del_list = json.load(f)
    except:
        del_list = []

    logs = ''
    while True:
        try:
            with open('./journalctl.log', 'r') as f:
                new_logs = f.read()
            new_logs = new_logs.partition('\n')[2]
            if not new_logs:
                new_logs = 'No entries'

            if not logs:
                logs = new_logs

            if new_logs != logs and 'No entries' not in new_logs:
                logs = new_logs
                await bot.get_channel(ID['LOGS']).send(f'<@775483306241949706>\n{logs}')
        except:
            pass

        if del_list:
            for msg_id in del_list:
                try:
                    msg = await bot.get_channel(msg_id[0]).fetch_message(msg_id[1])
                    await msg.delete()
                    del_list.remove(msg_id)

                except:
                    del_list.remove(msg_id)
                    continue

        try:
            msg_id = await bot.get_channel(ID['LOGS']).send(f'[{len(del_list)}] <t:{int(time.time())}:R> была онлайн')
            del_list.append([msg_id.channel.id, msg_id.id])

            with open('./data/ID_log.json', 'w') as f:
                json.dump(del_list, f, indent=4)
        except:
            pass

        await asyncio.sleep(600)


@bot.event
async def on_raw_reaction_add(payload):

    if payload.message_id == NSFW_access_message_id:
        member = bot.get_guild(payload.guild_id).get_member(payload.user_id)

        for name_channel in NSFW_channel:
            await add_permissions(payload, NSFW_channel[name_channel])
            await asyncio.sleep(0.2)

        user_roles_id = [role.id for role in payload.member.roles]
        user_id = payload.member.id

        # Для VIP-ролей доступны дополнительные каналы
        if any(role_id in VIP_roles.values() for role_id in user_roles_id):
            for name_channel in VIP_NSFW_channel:
                await add_permissions(payload, VIP_NSFW_channel[name_channel])
                await asyncio.sleep(0.2)

        # Для VIP-участников DNP не работает
        if user_id not in VIP_members.values():
            for name_channel in DNP_channel:

                # Для VIP-каналов пропускаем выставление прав для того чтобы не открывать каналы.
                if DNP_channel[name_channel] not in VIP_NSFW_channel.values():
                    await dnp_permissions(payload, DNP_channel[name_channel])
                    await asyncio.sleep(0.2)

        with open('./log permissions.log', 'a') as f:
            f.write(f'[{time.strftime("%d.%m.%y - %H:%M:%S", time.localtime())}]\t' +
                    f'Пользователь {member} id({payload.user_id}) получил доступ к NSFW каналам\n')


@bot.event
async def on_raw_reaction_remove(payload):

    if payload.message_id == NSFW_access_message_id:
        member = bot.get_guild(payload.guild_id).get_member(payload.user_id)

        for name_channel in NSFW_channel:
            await remove_permissions(payload, NSFW_channel[name_channel])
            await asyncio.sleep(0.2)

        for name_channel in VIP_NSFW_channel:
            await remove_permissions(payload, VIP_NSFW_channel[name_channel])
            await asyncio.sleep(0.2)

        with open('./log permissions.log', 'a') as f:
            f.write(f'[{time.strftime("%d.%m.%y - %H:%M:%S", time.localtime())}]\t' +
                    f'Пользователь {member} id({payload.user_id}) отозвал доступ к NSFW каналам\n')


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    global lassitude

    # Ищем имя в ответах
    reply_author = None
    if message.reference:
        reply_author = await asyncio.create_task(reply_author_func(message))

    # Если имя бота есть в сообщении или ответе - заходим
    if bot.user == reply_author or bot.user in message.mentions:

        # Примочка для удаления постов бота
        check_del = ['удали', 'удоли', 'del']
        check_del_true = any(check_del in message.content.lower() for check_del in check_del)

        # ID dacaoo#0
        if message.author.id == 775483306241949706 and check_del_true:

            msg = await bot.get_channel(message.reference.channel_id).fetch_message(message.reference.message_id)

            if msg.author == bot.user:
                msg_id = msg.id
                try:
                    await msg.delete()
                    await bot.get_channel(ID['LOGS']).send(f'Message id '
                                                           f'{msg_id} deleted')
                except Exception as error:
                    await bot.get_channel(ID['LOGS']).send(f'Message id '
                                                           f'{msg_id} NOT deleted')
                return
            else:
                pass
                return

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

        # Заходим только если было прямое упоминание, без упоминания бота в ответе
        # Сделано для исключения реакции на ответ с текстом на ответ бота (комментарий на пост от юзера)
        # Т.к. словарь содержит очень много ключей, которые могут вызывать ложные срабатывания и вобще
        if bot.user != reply_author and message.channel.id != ID['PAINT']:

            # Ищем теги в тексте поста, если есть прямое совпадение по тексту - то сразу заходим
            # Если совпадения нет, то считаем через FuzzyWuzzy и если точность >65 заходим
            check_post_true = any(check_post in message.content.lower() for check_post in TAG)

            if check_post_true:
                check_post_procent = 100

            else:
                # process это часть FuzzyWuzzy
                # считаем через проценты
                check_post_procent = process.extractOne(message.content.lower(), TAG)
                # extractOne возвращает кортеж, первое - совпавший тег, второе - процент
                # Вход в поиск производится при любом совпадении 
                check_post_procent = check_post_procent[1]

            if check_post_procent > 65:
                return asyncio.create_task(post_pic(message))

    # Проверяем является ли автор сообщения о повторе тем же самым автором
    # В recall[1] хранится message предыдущего вызова
    check_repeat = ['повто', 'еще', 'ещё', 'моар', 'исчо', 'moar', 'more', 'добавк']
    if recall \
        and recall[1].author == message.author \
        and recall[1].channel.id == message.channel.id:
        # Если автор тот же, то упоминание не обязательно

        if lassitude > 10:
            return

        check_repeat_true = any(check_repeat in message.content.lower() for check_repeat in check_repeat)

        if check_repeat_true and not message.channel.id == ID['PAINT']:
            lassitude += 1

            # Повторяем последний запрос
            task = asyncio.create_task(repeat(message, recall))
            return

    else:
        # Если автор отличается то заходим только если было упоминание бота

        if lassitude > 10:
            return

        if bot.user == reply_author or bot.user in message.mentions:

            check_repeat_true = any(check_repeat in message.content.lower() for check_repeat in check_repeat)

            if check_repeat_true and not message.channel.id == ID['PAINT']:
                lassitude += 1

                # Повторяем последний запрос
                task = asyncio.create_task(repeat(message, recall))
                return

    # Постит пикчи с Дэш при упоминании
    # В сейф-каналах
    # magic-place-bat-pony - 951143313652744252
    if lassitude < 6 \
            and bot.user in message.mentions \
            and not bot.user == reply_author \
            and not message.channel.id == ID['CLOP'] \
            and not message.channel.id == ID['DARK'] \
            and not message.channel.id == ID['PAINT'] \
            and not message.channel.id == 951143313652744252:

        lassitude += 1

        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-oc%2C+solo%2C+rd%2C+pony%2C-anthro%2C+score.gte%3A150'

        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search_pic.search_derp(string))

        task = await asyncio.create_task(
            upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name'], rnd.choice(CITATLIST)))

        if lassitude >= 6:
            await message.channel.send('... Уф! Валюсь с ног! Пришло время поспать :zzz:')
        return

        # Если ткнули ник в особых каналах
    # В клопе
    if lassitude < 5 and bot.user in message.mentions and not bot.user == reply_author and message.channel.id == ID[
        'CLOP']:
        lassitude += 1

        if lassitude < 4:
            return await message.reply('Ай! Не тыкай в меня своими сосисками!')

        elif lassitude == 4:
            return await message.reply('Ты хочешь увидеть мое секретное местечко?')

        elif lassitude == 5:

            string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191484&q=-oc%2C+solo%2C+rd%2C+vulva%2C+pony%2C-anthro%2C+score.gte%3A290'

            # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
            l = await asyncio.create_task(search_pic.search_derp(string))

            text = 'Тебе нравится, конееб?'

            task = await asyncio.create_task(
                upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name'], text))

        return

    # В дарке
    if lassitude < 7 and bot.user in message.mentions and not bot.user == reply_author and message.channel.id == ID[
        'DARK']:
        lassitude += 1

        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191483&q=+solo%2C+score.gte%3A60'

        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search_pic.search_derp(string))

        task = await asyncio.create_task(upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name']))
        return

    # В канале фестралов
    if lassitude < 7 and bot.user in message.mentions and not bot.user == reply_author and message.channel.id == 951143313652744252:
        lassitude += 1

        string = 'page=1&sf=random%3A' + rnd.key() + '&per_page=50&sd=desc&filter_id=191485&q=-webm%2C+bat+pony%2C+pony%2C+score.gte%3A200'

        # Функция возвращает список вида l[{id:, format:, name:, full:, url:, artist:, safe:}]
        l = await asyncio.create_task(search_pic.search_derp(string))

        task = await asyncio.create_task(upload(message, l[0]['size'], l[0]['full'], l[0]['url'], l[0]['name']))
        return

    return


bot.loop.create_task(bg_task_follow())
bot.loop.create_task(bg_task_lassitude())
bot.loop.create_task(bg_supervisor_post())

bot.run(config.TOKEN)
