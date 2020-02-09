import argparse
import json
import pathlib
from pprint import pprint

from pymongo import MongoClient
from pymongo.errors import BulkWriteError

client = MongoClient(host='192.168.1.44', port=27017)
db = client['vacancies']
vacancy_unique_index = 'vacancy_link'


def _import_data_from_json(data_path):
    try:
        data_path = pathlib.Path(data_path)
        name = data_path.stem.lower()
        collection = db.get_collection(name)

        # create unique index to avoid duplicates of vacancies in collection
        if vacancy_unique_index not in collection.index_information():
            collection.create_index('vacancy.link', unique=True, name=vacancy_unique_index)
        collection.insert_many(json.loads(data_path.read_text()), ordered=False)

    except BulkWriteError as e:
        print("Warning: Possible duplicates found; See duplicates.log")
        with open('duplicates.log', 'w') as dupl:
            pprint(e.details, stream=dupl)

    except Exception as e:
        print(e)
        return False

    print('Imported successfully')
    return True


def _find_vacancies(find):

    vacancies_formatted = []

    collections = db.collection_names(include_system_collections=False)

    for coll in collections:
        vacancies_list = db.get_collection(coll).find({'salary.min': {'$gt': find}})
        for vacancy_info in vacancies_list:
            vacancies_formatted.append({'name': vacancy_info['vacancy']['name'],
                                        'link': vacancy_info['vacancy']['link'],
                                        'salary': vacancy_info['salary']['min'],
                                        'employer': vacancy_info['employer']['name']})

    if not vacancies_formatted:
        print(f'There are no vacancies with satary greater than {find}')
    else:
        print(f'{len(vacancies_formatted)} vacancies found')

        for vac in vacancies_formatted:
            print('-' * 30)
            pprint(vac)
            print('-' * 30)
            inp = input('Press Enter to continue or insert "q" to exit... ')
            if inp == 'q':
                break

    return True


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-i', '--import-data', metavar='<path to *.json>',
                        type=pathlib.Path, help="Path to imported data")
    parser.add_argument('-f', '--find', type=int, metavar='<int>',
                        help="Find vacancies with salary greater than inserted (RUB); "
                             "Salary with foreign currency or empty salary will be ignored")

    args = parser.parse_args()

    is_ok = False

    if args.import_data:
        is_ok = _import_data_from_json(args.import_data)
    elif args.find:
        # Salary with foreign currency or empty salary will be ignored
        is_ok = _find_vacancies(args.find)
    else:
        parser.print_help()

    exit(not is_ok)


if __name__ == '__main__':
    main()
