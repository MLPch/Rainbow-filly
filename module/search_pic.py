import asyncio
import time


async def search_derp(q):
    url = 'https://www.derpibooru.org/api/v1/json/search/images?' + q

    l = []

    # Получаем список изображений
    response = await asyncio.create_task(req.json_get(url))

    # Вытаскиваем список пикч
    images = response.get('images')

    # Если нет списка пикч возвращаем пустой список
    if not images:
        return l

    for i in range(len(images)):

        artist = 'None artist'
        safe = False

        for tag in images[i]['tags']:

            # Ищем тег артиста
            if tag.startswith('artist:'):
                artist = tag[7:]

            # Ищем рейтинг
            if tag == 'safe':
                safe = True

        # .svg в именах файла не подгружает превью в дискорде, поэтому заменяем на .png
        if images[i]['format'] != 'svg':
            name = str(images[i]['id']) + '.' + images[i]['format']
        else:
            name = str(images[i]['id']) + '.png'

        # Ограничение на 10000px по одной из сторон
        image_url = ''
        if images[i]['height'] > 9000 or images[i]['width'] > 9000:
            image_url = images[i]['representations']['large']
        else:
            image_url = images[i]['representations']['full']

        # Преобразуем дату загрузки в секунды от начала эпохи
        date = int(time.mktime(time.strptime(images[i]['first_seen_at'], '%Y-%m-%dT%H:%M:%SZ')))

        # Записываем результаты
        l.append({
            'id': images[i]['id'],
            'format': images[i]['format'],
            'name': name,
            'full': images[i]['representations']['full'],
            'url': ('https://www.derpibooru.org/images/' + str(images[i]['id'])),
            'artist': artist.capitalize(),
            'date': date,
            'size': images[i]['size'],
            'safe': safe
        })

    return l


async def search_poner(q):
    url = 'https://ponerpics.org/api/v1/json/search/images?' + q

    l = []

    # Получаем список изображений
    response = await asyncio.create_task(req.json_get(url))

    # Вытаскиваем список пикч
    images = response.get('images')

    # Если нет списка пикч возвращаем пустой список
    if not images:
        return l

    for i in range(len(images)):

        artist = 'None artist'
        safe = False

        for tag in images[i]['tags']:

            # Ищем тег артиста
            if tag.startswith('artist:'):
                artist = tag[7:]

            # Ищем рейтинг
            if tag == 'safe':
                safe = True

        # .svg в именах файла не подгружает превью в дискорде, поэтому заменяем на .png
        if images[i]['format'] != 'svg':
            name = str(images[i]['id']) + '.' + images[i]['format']
        else:
            name = str(images[i]['id']) + '.png'

        # Преобразуем дату загрузки в секунды от начала эпохи
        date = int(time.mktime(time.strptime(images[i]['first_seen_at'], '%Y-%m-%dT%H:%M:%SZ')))

        # Записываем результаты
        l.append({
            'id': images[i]['id'],
            'format': images[i]['format'],
            'name': name,
            'full': images[i]['representations']['full'],
            'url': ('https://ponerpics.org/images/' + str(images[i]['id'])),
            'artist': artist.capitalize(),
            'date': date,
            'safe': safe
        })

    return l


async def reverse_derp(url):
    l = []

    for k in range(0, 71, 10):

        url_dist = 'https://www.derpibooru.org/api/v1/json/search/reverse?url=' + url + '&distance=' + str(k / 100)

        # Получаем список изображений
        response = await asyncio.create_task(req.json_post(url_dist))

        # Вытаскиваем список пикч
        images = response.get('images')

        # Eсли с текущим distance нет результата - ждем
        if not images:
            await asyncio.sleep(0.15)
            continue

        for i in range(len(images)):
            safe = False

            if images[i]['duplicate_of'] is not None:
                img_id = str(images[i]['duplicate_of'])

            else:
                img_id = str(images[i]['id'])

                if 'tags' in images[i]:
                    for tag in images[i]['tags']:
                        if tag == 'safe':
                            safe = True

            l.append({
                'url': ('https://www.derpibooru.org/images/' + img_id),
                'distance': k,
                'safe': safe
            })
        break

    # Прошли по всему distance и не нашли результата
    else:

        # ###################################################################### #
        # Временная примочка, чтобы искать еще на понибуре если не найдено на DB #
        # ###################################################################### #

        for k in range(0, 71, 10):

            url_dist = 'https://ponerpics.org/api/v1/json/search/reverse?url=' + url + '&distance=' + str(k / 100)

            # Получаем список изображений
            response = await asyncio.create_task(req.json_post(url_dist))

            # Вытаскиваем список пикч
            images = response.get('images')

            # Eсли с текущим distance нет результата - ждем
            if not images:
                await asyncio.sleep(0.15)
                continue

            for i in range(len(images)):
                safe = False

                if images[i]['duplicate_of'] is not None:
                    img_id = str(images[i]['duplicate_of'])

                else:
                    img_id = str(images[i]['id'])

                    if 'tags' in images[i]:
                        for tag in images[i]['tags']:
                            if tag == 'safe':
                                safe = True

                l.append({
                    'url': ('https://ponerpics.org/images/' + img_id),
                    'distance': k,
                    'safe': safe
                })
            break


        # Прошли по всему distance и не нашли результата
        else:
            l.append({
                'url': False,
                'distance': k,
                'safe': False
            })

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
            answer += '*Не заглядывать во время полета!*\n<' + l[0]['url'] + '>'

        # Если результатов несколько
        if len(l) > 1:
            # записываем все что есть в списке кроме нулевого
            for i in range(len(l)):
                if not l[i]['url'] in answer:
                    answer += '\n<' + l[i]['url'] + '>'

    else:
        answer = 'Извини, Анон, ничего не нашла...'

    return answer


if __name__ == "__main__":
    import req

    url = 'https://derpicdn.net/img/view/2012/1/2/0.jpg'

    print(asyncio.run(reverse_derp(url)))
