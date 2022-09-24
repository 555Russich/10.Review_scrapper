import json
import csv
import os.path
import re
import traceback
from time import sleep

import undetected_chromedriver.v2 as uc
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def create_txt(filepath='output.txt'):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('Программа обработки отзывов\n')


def append_dict_to_txt(reviews_info: dict, filepath='output.txt'):
    url = list(reviews_info.keys())[0]
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(f'url:\n{url}\n')
        for i, d in reviews_info[url].items():
            f.write(f'id: {i}\n')
            for k, v in d.items():
                if k in ('positive', 'negative'):
                    f.write(f'type: {k}\nreview: {v}\n')
                else:
                    f.write(f'{k}: {v}\n')


class Scrapper:
    def __init__(self):
        self.driver = None
        self.page_load_time_out = 20

    def get_driver(self):
        # options = webdriver.ChromeOptions()
        options = uc.ChromeOptions()
        # fake user agent
        options.add_argument(
            f'user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        )
        # headless mode
        options.headless = True
        # maximized window
        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        chrome_service = Service(ChromeDriverManager().install())
        driver = uc.Chrome(
            options=options,
            version_main=104,
            service=chrome_service
        )
        try:
            from subprocess import CREATE_NO_WINDOW
            driver.service.creationflags = CREATE_NO_WINDOW
        except ImportError:
            pass
        self.driver = driver
        print(self.driver.service.creationflags)

    def get_page_with_retries(self, url, retries_get_page=3):
        i = 0
        while True:
            i += 1
            self.get_driver()
            print(self.driver.service.creationflags)
            self.driver.set_page_load_timeout(self.page_load_time_out)
            try:
                print(f'Страница загружается... {url=}')
                self.driver.get(url)
                break
            except TimeoutException:
                if retries_get_page == i:
                    print(f'Страница не загрузилась после {i} попыток')
                    return
                else:
                    print(f'Страница не загрузилась с таймаутом {self.page_load_time_out}.'
                          f' Попыток осталось: {retries_get_page - i}')
                    self.driver.quit()

    def open_google_translate_tab(self):
        og_tab = self.driver.current_window_handle
        assert len(self.driver.window_handles) == 1
        self.driver.switch_to.new_window('tab')
        url = 'https://translate.google.com/?sl=auto&tl=ru'
        print(f'Открываем переводчик')
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.number_of_windows_to_be(2)
        )
        sleep(1)
        print(f'Переводчик открылся')
        self.driver.switch_to.window(og_tab)

    def translate_to_ru(self, text):
        try:
            og_tab = self.driver.current_window_handle
            assert len(self.driver.window_handles) == 2
            translate_tab = self.driver.window_handles[1]
            self.driver.switch_to.window(translate_tab)
            text_input = self.driver.find_element(By.XPATH, '//textarea[@aria-label="Исходный текст"]')
            text_input.clear()
            sleep(1)
            js_add_text_to_input = """
              var elm = arguments[0], txt = arguments[1];
              elm.value += txt;
              elm.dispatchEvent(new Event('change'));
            """
            self.driver.execute_script(js_add_text_to_input, text_input, text)
            text_input.send_keys(' ')
            sleep(1)
            text_output = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[@lang="ru"]/span/span'))
            ).text
            self.driver.switch_to.window(og_tab)
            print(f'Текст: "{text}" переведен как: "{text_output}"')
            return text_output
        except:
            return None

    def scrap_page(self, url, filepath='output.txt'):
        try:
            create_txt(filepath)
            self.get_page_with_retries(url, 3)
            self.open_google_translate_tab()

            # accept cookies
            try:
                self.driver.find_element(By.XPATH, '//button[@id="onetrust-accept-btn-handler"]').click()
                sleep(1)
            except NoSuchElementException:
                pass

            self.driver.find_element(By.XPATH, '//div[@class="hp-featured_reviews-bottom"]/button').click()
            counter = 0
            reviews_info = {url: {}}
            while True:
                # wait until loading finished
                while True:
                    try:
                        self.driver.find_element(
                            By.XPATH, '//div[@id="review_list_page_container"][@style="display: block;"]'
                        )
                        break
                    except NoSuchElementException:
                        continue
                sleep(1)

                count_reviews_on_page = len(self.driver.find_elements(
                    By.XPATH, '//div[@class="c-review-block"]'
                ))
                for i in range(1, count_reviews_on_page + 1):
                    nickname, date, review_title, review_info = None, None, None, None
                    positive, negative = '', ''
                    translated, translate_error = False, False
                    div_review = self.driver.find_element(
                        By.XPATH, f'(//div[@class="c-review-block"])[{i}]'
                    )
                    ActionChains(self.driver).scroll_to_element(div_review).perform()

                    # Press translate button if it exists
                    try:
                        div_review.find_element(
                            By.XPATH, './/a[text()="Показать перевод"]'
                        ).click()
                        while translated is False and translate_error is False:
                            try:
                                div_review.find_element(
                                    By.XPATH, './/span[@style="display: inline;"]/'
                                              'span[normalize-space(text())="Переведено"]'
                                )
                                translated = True
                            except NoSuchElementException:
                                pass
                            try:
                                div_review.find_element(
                                    By.XPATH, './/span[@style="display: inline;"][contains(text(), "Не удалось перевести")]'
                                )
                                translate_error = True
                            except NoSuchElementException:
                                pass
                    except NoSuchElementException:
                        pass

                    nickname = div_review.find_element(
                        By.CLASS_NAME, 'bui-avatar-block__title'
                    ).text
                    date = div_review.find_element(
                        By.XPATH, './/div[@class="c-review-block__row"]/span[@class="c-review-block__date"]'
                    ).text.replace('Время отзыва: ', '')

                    if not translate_error:
                        positives = div_review.find_elements(
                            By.XPATH, './/span[text()="Понравилось"]/parent::span/following-sibling::'
                                      'span[contains(@class, "c-review__body")]'
                        )
                    else:
                        positives = div_review.find_elements(
                            By.XPATH, './/span[@class="c-review__prefix c-review__prefix--color-green"]'
                                      '/following-sibling::span[@lang]'
                        )
                    match positives:
                        case []:
                            positive = ''
                        case [arg]:
                            positive = arg.text
                        case [*args]:
                            positive = [p for p in args if p.get_attribute('style') == 'display: inline;'][0].text
                    if positive:
                        if translate_error or not re.search(r'[А-я]', positive):
                            positive = self.translate_to_ru(positive)

                    if not translate_error:
                        negatives = div_review.find_elements(
                            By.XPATH, './/span[text()="Не понравилось"]/parent::span'
                                      '/following-sibling::span[contains(@class, "c-review__body")]'
                        )
                    else:
                        negatives = div_review.find_elements(
                            By.XPATH, './/span[@class="c-review__prefix"]/following-sibling::span[@lang]'
                        )
                    match negatives:
                        case []:
                            negative = ''
                        case [arg]:
                            negative = arg.text
                        case [*args]:
                            negative = [p for p in args if p.get_attribute('style') == 'display: inline;'][0].text
                    if negative:
                        if translate_error or not re.search(r'[А-я]', negative):
                            negative = self.translate_to_ru(negative)

                    counter += 1
                    review_info = {
                        'author': nickname,
                        'date': date,
                        'positive': positive,
                        'negative': negative
                    }

                    if negative or positive:
                        reviews_info[url][len(reviews_info[url]) + 1] = review_info
                        print(f'№: {counter}, {review_info}')
                    else:
                        print(f'№: {counter}, В отзыве отсутствуют негативные или положительные комментарии')

                try:
                    self.driver.find_element(By.XPATH, '//a[@class="pagenext"]').click()
                except NoSuchElementException:
                    break

            append_dict_to_txt(reviews_info, filepath)
            # with open('reviews_example.json', 'w') as f:
            #     json.dump(reviews_info, f, indent=4, ensure_ascii=False)

            # columns = ('url', 'id', 'author', 'date', 'positive', 'negative')
            # with open('reviews_example.csv', 'a', encoding='utf-8') as f:
            #     writer = csv.writer(f, delimiter=';')
            #     writer.writerow(columns)
            #     for i, d in reviews_info[url].items():
            #         if i == 1:
            #             row_data = [url, i]
            #         else:
            #             row_data = [None, i]
            #         for column in columns[2:]:
            #             if v := d.get(column):
            #                 row_data.append(v)
            #             else:
            #                 row_data.append(None)
            #         writer.writerow(row_data)
        except:
            print(traceback.format_exc())
        finally:
            self.driver.quit()


def main():
    Scrapper().scrap_page('https://www.booking.com/hotel/it/residenza-gonfalone.ru.html?label=gen173nr-1DCAEoggI46AdIM1gEaMIBiAEBmAEhuAEZyAEM2AED6AEBiAIBqAIDuALty5KYBsACAdICJDQwZWM2YmZhLTU5NDItNDgxMi05M2I5LTUyMmExNjhhNDBjZNgCBOACAQ&sid=74e702f2aee6c0eeab7fc4bc642824cd&aid=304142&ucfs=1&arphpl=1&dest_id=-126693&dest_type=city&group_adults=2&req_adults=2&no_rooms=1&group_children=0&req_children=0&hpos=4&hapos=4&sr_order=popularity&srpvid=5c0666a902dd010a&srepoch=1661956563&from=searchresults#hotelTmpl')
    pass


if __name__ == '__main__':
    main()
