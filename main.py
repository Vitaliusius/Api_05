import requests
import json

from environs import env
from dotenv import load_dotenv
from terminaltables import AsciiTable

load_dotenv()
LANGUAGES = env.list('LANGUAGES')


def get_vacancies_sj(language, secret_key, page=0):
    headers = {
        "X-Api-App-Id": secret_key
    }
    payload = {
        "town": "Москва",
        "count": 100,
        "page": page,
        "keyword": f"Программист {language}"
    }
    response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers, params=payload)
    response.raise_for_status()
    return response.json()


def get_vacancies_hh(language, page=0):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 YaBrowser/25.12.0.0 Safari/537.36',
    }
    payload = {
        'text': f'Программист {language}',
        'area': 1,
        'page': page,
        'per_page': 100
    }
    response = requests.get('https://api.hh.ru/vacancies', headers=headers, params=payload)
    response.raise_for_status()
    return response.json()


def get_vacancies_salaries_sj(language, secret_key):
    page = 0
    salaries_sj = []
    while True:
        vacancies_sj = get_vacancies_sj(language, secret_key, page)
        for vacancy_sj in vacancies_sj.get('objects'):
            vacancy_salary_sj = get_predict_rub_salary(
                vacancy_sj.get('payment_from'),
                vacancy_sj.get('payment_to'),
                vacancy_sj.get('currency')
            )
            if vacancy_salary_sj:
                salaries_sj.append(vacancy_salary_sj)
        if not vacancies_sj.get('more'):
            break
        page += 1
    vacancies_found_sj = vacancies_sj.get("total")
    return salaries_sj, vacancies_found_sj


def get_vacancies_salaries_hh(language):
    salaries_hh = []
    page = 0
    while True:
        vacancies_hh = get_vacancies_hh(language, page)
        for vacancy_hh in vacancies_hh.get('items'):
            salary_hh = vacancy_hh.get('salary')
            vacancy_salary_hh = None
            if salary_hh:
                vacancy_salary_hh = get_predict_rub_salary(
                    salary_hh.get('from'),
                    salary_hh.get('to'),
                    salary_hh.get('currency')
                )
            if vacancy_salary_hh:
                salaries_hh.append(vacancy_salary_hh)
            if page >= vacancies_hh.get('pages'):
                break
        page += 1
    vacancies_found_hh = vacancies_hh.get("found")
    return salaries_hh, vacancies_found_hh


def get_predict_rub_salary(salary_from, salary_to, salary_currency):
    currencies = ['RUR', 'rub']
    if salary_currency not in currencies:
        return None
    elif salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_to:
        return salary_to * 0.8
    elif salary_from:
        return salary_from * 1.2
    return None


def get_statistics(vacancies_found, salaries):
    average_salary, vacancies_processed = get_average_salary(salaries)
    statistics = {
        "vacancies_found": vacancies_found,
        "vacancies_processed": vacancies_processed,
        "average_salary": average_salary
    }
    return statistics


def get_average_salary(salaries):
    if salaries:
        average_salary = int(sum(salaries) / len(salaries))
        vacancies_processed = len(salaries)
        return average_salary, vacancies_processed
    else:
        return 0, 0
    return average_salary, vacancies_processed


def print_table(statistics, name_site):
    title = f"{name_site} Moscow"
    table_parameters = [
        [
            "Язык программирования",
            "Вакансий найдено",
            "Вакансий обработано",
            "Средняя зарплата"
        ]
    ]
    for language in LANGUAGES:
        vacancy_parameters = list(statistics.get(language).values())
        vacancy_parameters.insert(0, language)
        table_parameters.append(vacancy_parameters)
    table = AsciiTable(table_parameters, title)
    print(table.table)


def main():
    load_dotenv()
    secret_key_sj = env.str("SECRET_KEY_SJ")
    statistics_sj = {}
    statistics_hh = {}
    for language in LANGUAGES:
        salaries_hh, vacancies_found_hh = get_vacancies_salaries_hh(language)       
        statistics_hh[language] = get_statistics(vacancies_found_hh, salaries_hh)
        salaries_sj, vacancies_found_sj = get_vacancies_salaries_sj(language, secret_key_sj)
        statistics_sj[language] = get_statistics(vacancies_found_sj, salaries_sj)
    print_table(statistics_hh, "SuperJob")
    print()
    print_table(statistics_hh, "HeadHunter")
    

if __name__ == "__main__":
    main()
