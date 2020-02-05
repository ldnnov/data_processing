import json
import re
import requests
from bs4 import BeautifulSoup as bs


class JobFinder:
    vacancies = []

    def __init__(self, job):
        self._job = job
        self._main_url = None
        self._request_tpl = None
        self._html = None
        self._first_page = 0
        self._max_pages = 0

    def _append_vacancy(self, vacancy_name, vacancy_link, employer_name, employer_link,
                        salary_min=None, salary_max=None, currency=None):

        self.vacancies.append({
            'vacancy': {
                'name': vacancy_name,
                'link': vacancy_link
            },
            'salary': {
                'min': int(salary_min) if salary_min else None,
                'max': int(salary_max) if salary_max else None,
                'currency': currency if currency else None
            },
            'employer': {
                'name': employer_name,
                'link': employer_link
            },
            'source': self._main_url
        })

    def _load_html(self, request=''):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
        }

        response = requests.get(self._main_url + request, headers=headers)
        if response.ok:
            self._html = bs(response.content.decode('UTF-8'), 'html.parser')
        else:
            raise NotImplementedError('Page was not loaded')

    def _update_page(self, page=None):

        if not page:
            page = self._first_page

        page_text = f'Page {page}/{self._max_pages-1}'

        if page == self._max_pages - 1:
            print(f'\r{page_text}')
        else:
            print(f'\r{page_text}', end='')

        req = self._request_tpl.format(self._job, page)
        self._load_html(req)

    def _parse_current_page(self):
        raise NotImplementedError('Method is not implemented')

    def _set_max_pages(self):
        raise NotImplementedError('Method is not implemented')

    def parse_pages(self):
        print(f'Parse from {self._main_url}')
        self._update_page()
        self._parse_current_page()
        self._set_max_pages()

        for page in range(self._first_page + 1, self._max_pages):
            self._update_page(page)
            self._parse_current_page()

    @classmethod
    def upload_to(cls, json_file):
        with open(f'{json_file}.json', 'w') as file:
            file.write(json.dumps(cls.vacancies, indent=4, ensure_ascii=False))


class HeadHunterFinder(JobFinder):
    def __init__(self, job):
        super().__init__(job)
        self._main_url = 'https://nn.hh.ru'
        self._request_tpl = '/search/vacancy?L_is_autosearch=false&area=113&clusters=true&enable_snippets=true&text={}&page={}'

    def _parse_current_page(self):
        vacancies_block = self._html.find('div', attrs={'class': 'vacancy-serp'})
        vacancies = vacancies_block.findAll('div', attrs={'class': 'vacancy-serp-item'}, recursive=False)

        for vacancy in vacancies:
            salary_min = None
            salary_max = None
            currency = None

            vacancy_info = vacancy.find('a', attrs={'data-qa': 'vacancy-serp__vacancy-title'})
            employer = vacancy.find('div', attrs={'class': 'vacancy-serp-item__meta-info'}).find('a')
            salary = vacancy.find('div', attrs={'data-qa': 'vacancy-serp__vacancy-compensation'})

            if salary:
                salary_txt = salary.text.encode('utf-8').replace(b'\xc2\xa0', b'').decode('utf-8')
                match = re.search(r'(от )?(\d*)((-|до )?(\d*))? (\D*)$', salary_txt)
                if match:
                    salary_min = match.group(2)
                    salary_max = match.group(5)
                    currency = match.group(6)

            self._append_vacancy(
                vacancy_name=vacancy_info.text,
                vacancy_link=vacancy_info['href'],
                employer_name=employer.text,
                employer_link=self._main_url + employer['href'],
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency
            )

    def _set_max_pages(self):

        pager = self._html.findAll('a', attrs={
            'class': ['bloko-button', 'HH-Pager-Control'],
            'data-qa': 'pager-page'})

        if pager:
            page_num = pager[-1]['data-page']
            if page_num.isdigit():
                self._max_pages = int(page_num) + 1


class SuperJobFinder(JobFinder):
    def __init__(self, job):
        super().__init__(job)
        self._main_url = 'https://nn.superjob.ru'
        self._request_tpl = '/vacancy/search/?keywords={}&geo%5Bc%5D%5B0%5D=1&page={}'
        self._first_page = 1

    def _parse_current_page(self):

        vacancies_block = self._html.find('div', attrs={'class': '_1ID8B'})
        vacancies = vacancies_block.findAll('div', attrs={'class': 'f-test-vacancy-item'})

        for vacancy in vacancies:
            salary_min = None
            salary_max = None
            currency = None

            vacancy_info = vacancy.find('a', attrs={'class': '_1QIBo'})
            employer = vacancy.find('a', attrs={'class': ['icMQ_', '_205Zx', '_25-u7'], 'target': '_self'})
            salary = vacancy.find('span', attrs={'class': 'f-test-text-company-item-salary'})

            if salary:
                salary_txt = salary.text.encode('utf-8').replace(b'\xc2\xa0', b'').decode('utf-8')

                if not salary_txt == 'По договорённости':
                    match = re.search(r'(от)?(\d*)((-|—|до)?(\d*))?(\D*)$', salary_txt)
                    if match:
                        salary_min = match.group(2)
                        salary_max = match.group(5)
                        currency = match.group(6)

            self._append_vacancy(
                vacancy_name=vacancy_info.text,
                vacancy_link=self._main_url + vacancy_info['href'],
                employer_name=employer.text if employer else None,
                employer_link=(self._main_url + employer['href']) if employer else None,
                salary_min=salary_min,
                salary_max=salary_max,
                currency=currency
            )

    def _set_max_pages(self):

        pager_block = self._html.find('div', attrs={'class': 'L1p51'})

        if pager_block:
            pages = pager_block.findAll('span', attrs={'class': '_3IDf-'})
            page_num = pages[-2].text
            if page_num.isdigit():
                self._max_pages = int(page_num) + 1


if __name__ == '__main__':
    vacancy = input('Insert vacancy: ')

    hh = HeadHunterFinder(vacancy)
    hh.parse_pages()

    sj = SuperJobFinder(vacancy)
    sj.parse_pages()

    JobFinder.upload_to(vacancy.replace(' ', '_'))

