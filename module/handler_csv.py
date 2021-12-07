import csv
import os


def read_csv(path):
    with open(path, encoding="utf8") as file:
        csv_reader = csv.reader(file)
        count = 0
        count2 = 0

        category = []

        for row in csv_reader:

            if count == 0:
                # Вывод строки, содержащей заголовки для столбцов
                print(f'Файл содержит столбцы: {", ".join(row)}')
                count += 1
                continue

            if 'artist:' in row[2] and int(row[1]) > 0:
                count2 += 1

            category.append(row[4])

            if int(row[1]) < 50:
                continue

            count += 1

        category = list(set(category))
        category.sort()

        print(f'Всего в файле {count} строк.')
        print(f'category: {category}')
        print(f'artist: {count2}')


if __name__ == "__main__":
    os.chdir(os.getcwd())
    os.chdir("..")

    read_csv('data/tags.csv')
