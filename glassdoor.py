from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import StaleElementReferenceException
import time
import pandas as pd
from selenium.webdriver.chrome.options import Options
from multiprocessing import Pool
import os
from functools import partial

MAX_PAGE = 15  # max crawling page


def crawl(file, job, level="entrylevel", max_page=MAX_PAGE):

    with Pool(os.cpu_count()) as p:
        partial_crawl_page = partial(crawl_page,  job, level)
        page_list = p.map(partial_crawl_page, [page_num for page_num in range(1, max_page + 1)])

    total = pd.DataFrame()
    for page_df in page_list:
        total = total.append(page_df, ignore_index=True)

    print("finish crawling " + str(total.shape[0]) + " items")
    total.to_csv(file, index=False)


# single thread function
def crawl_page(job, level, page_num):
    start_url = "https://www.glassdoor.com/Job/" + job + "-jobs-SRCH_KO0, 10_IP" + str(page_num) + ".htm?jobType=" + level
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(start_url)

    names = []
    companies = []
    company_reviews = []
    locations = []
    est_salaries = []
    descriptions = []

    cnt = 0

    for job in driver.find_elements_by_css_selector('#MainCol > div > ul > li'):
        try:
            job.click()
            time.sleep(3)
        except WebDriverException:
            driver.find_elements_by_css_selector(
                "#JAModal > div > div.prettyEmail.modalContents > div.xBtn")[0].click()
            print("successfully close popup")

        try:
            name = driver.find_elements_by_css_selector("#HeroHeaderModule > div.empWrapper > div.header > h1")[
                0].text
            company = driver.find_elements_by_css_selector(
                "#HeroHeaderModule > div.empWrapper > div.compInfo > a")[0].text
            try:
                company_review = \
                    driver.find_elements_by_css_selector("div.compInfo > span.compactRating.lg.margRtSm")[0].text

            except IndexError:
                company_review = None
                pass
            try:
                est_salary = driver.find_elements_by_css_selector("div.salaryRow > div > span")[0].text
            except IndexError:
                est_salary = None
                pass
            try:
                location = driver.find_elements_by_css_selector(
                    "#HeroHeaderModule > div.empWrapper > div.compInfo > span:nth-child(3)")[0].text
            except IndexError:
                location = None
                pass
            description = driver.find_elements_by_css_selector("#JobDescriptionContainer")[0].text

            names.append(name)
            companies.append(company)
            company_reviews.append(company_review)
            est_salaries.append(est_salary)
            locations.append(location)
            descriptions.append(description)

            cnt += 1
            print("finish crawling item ", cnt, " on page ", page_num)

        except StaleElementReferenceException:
            print("StaleElementReferenceException, Pass")
            pass
        except IndexError:
            driver.find_elements_by_css_selector("#JAModal > div > div.prettyEmail.modalContents > div.xBtn")[
                0].click()  # close popup
            print("successfully close popup")

    driver.close()
    print("finish page ", page_num)

    page = pd.DataFrame({"name": names, "company": companies, "company_review": company_reviews,
                         "est_salary": est_salaries, "location": locations, "description": descriptions})

    # clean
    page['company_review'] = page['company_review'].replace('★', '', regex=True)
    page['company_review'].fillna("", inplace=True)
    page['est_salary'].fillna("", inplace=True)
    salary_range = page['est_salary'].str.split("-", n=1, expand=True)
    page['salary_low'] = salary_range[0].map(min_salary)
    page['salary_high'] = salary_range[1].map(max_salary)

    names.clear()
    companies.clear()
    company_reviews.clear()
    locations.clear()
    est_salaries.clear()
    descriptions.clear()

    return page


def min_salary(amount):
    if amount.endswith("k"):
        if amount.startswith("Employer Provided Salary:$"):
            return int(amount[len("Employer Provided Salary:$"):-1]) * 1000
        else:
            return int(amount[1:-1]) * 1000
    elif amount.startswith("Employer Provided Salary:$"):
        return int(amount[amount.rfind("$") + 1:]) * 8 * 40 * 52
    elif amount[1:].isnumeric():
        return int(amount[1:]) * 8 * 40 * 52
    else:
        return amount


def max_salary(amount):
    if not amount:
        return ""
    elif amount.endswith("k(Glassdoor est.)") or amount.endswith("k(Employer est.)"):
        pos = amount.find("k")
        return int(amount[1:pos]) * 1000
    elif amount.endswith("Per Hour(Glassdoor est.)"):
        pos = amount.find("Per")
        return int(amount[1:pos]) * 8 * 40 * 52
    elif amount.endswith("k") and amount.startswith("$"):
        return int(amount[1:-1]) * 1000
    elif amount.endswith("Per Hour"):
        return int(amount[1:amount.find("Per Hour")]) * 8 * 40 * 52
    else:
        return amount


# for test purpose
if __name__ == "__main__":
    crawl("data/test.csv", "consultant", max_page=3)
