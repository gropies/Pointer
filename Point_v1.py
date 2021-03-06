import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import numpy as np
import plotly.graph_objs as go
import plotly

import glassdoor
import heinz_course_api
import smartevals
import geo
import rent

from sklearn import feature_extraction
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer

"""
this is the main function
"""

CONSULTING_FILE = "data/consultant.csv"
SDE_FILE = "data/sde.csv"
DS_FILE = "data/ds.csv"
COURSE_EVL_FILE = "data/course_evl.csv"
COURSE_INFO_FILE = "data/course_info.csv"
COMPANY_LOC_FILE = "data/company_loc.csv"
RENT_FILE = "data/rent_price.csv"


# test file is less than 100 item, used for debug
# CONSULTING_FILE = "data/consultant_test.csv"
# SDE_FILE = "data/sde_test.csv"
# DS_FILE = "data/ds_test.csv"


class Person:
    def __init__(self, career, location=None):
        self.career = career
        self.location = location

    def recommend_course_onskills(skillsinput, data):
        # skillsinput is the skills user want to learn, input seperated by space
        coursedes = list(data.course_df['description'])
        courseout = list(data.course_df['learning_outcome'])
        course = []
        for i in range(len(courseout)):
            if type(coursedes[i]) != str:
                coursedes[i] = str(coursedes[i])  # make sure data type are string
            if type(courseout[i]) != str:
                courseout[i] = str(courseout[i])  # make sure data type are string
            course.append(coursedes[i] + courseout[i])  # combine description and outcome together

        # deal with stopwords
        stop = open('corenlp_stopwords.txt', encoding='utf-8')
        st = stop.readlines()
        for i in range(len(st)):
            st[i] = st[i].strip('\n')  # delete '\n' in each word
        st.extend(
            ['allow', 'outcomes', 'some', 'mini', 'another', 'student', 'in', 'or', 'either', 'final', 'exam', 'mid',
             'by',
             'areas', 'also', 'today', 'course', 'Outcomes:', 'will', 'Work', 'Students', 'The', 'It', 'us', 'class',
             'Learning',
             'course,'])
        for i in range(len(course)):
            out = ''
            for word in course[i].split(' '):
                if word not in st:
                    out = out + word + ' '
            course[i] = out

        # get tfidf and extract key words
        vectorizer = CountVectorizer()  #
        transformer = TfidfTransformer()  # 词语的tf-idf权值
        tfidf = transformer.fit_transform(vectorizer.fit_transform(course))  # calculate tf-idf
        word = vectorizer.get_feature_names()  # all words in the word bag
        weight = tfidf.toarray()  # get matrix of tfidf
        key = []
        for i in range(len(weight)):
            doc = {}
            t = np.argsort(-weight[i])
            s = ''
            for j in range(40):
                # print(word[t[j]], ':', weight[i][t[j]])
                s = s + ' ' + word[t[j]]
            key.append(s)

        # print recommended courses based on skill sets matched  
        recommended = []
        for i in range(len(key)):
            for word in skillsinput.split(' '):
                if word in key[i]:
                    recommended.append(
                        data.course_df['course_id'][i] + ':' + data.course_df['names'][i] + ',course rate:' + '%.2f' % (
                            data.course_df['Overall course rate'][i]))
        print("COURSES RECOMMENDED:")
        for i in recommended:
            print(i)

    def recommend_course(self, data):

        if self.career == 'data science':
            job = data.ds_df
        elif self.career == 'sde':
            job = data.sde_df
        elif self.career == 'consultant':
            job = data.consulting_df

        desc = []
        for i in range(len(job)):
            if self.location in str(job['location'][i]):
                desc.append(job['description'][i].replace(',', ' '))

        coursedes = list(data.course_df['description'])
        courseout = list(data.course_df['learning_outcome'])

        course = []
        for i in range(len(courseout)):
            if type(coursedes[i]) != str:
                coursedes[i] = str(coursedes[i])  # make sure data type are string
            if type(courseout[i]) != str:
                courseout[i] = str(courseout[i])  # make sure data type are string
            course.append(coursedes[i] + courseout[i])  # combine description and outcome together

        # deal with stopwords
        stop = open('corenlp_stopwords.txt', encoding='utf-8')
        st = stop.readlines()
        for i in range(len(st)):
            st[i] = st[i].strip('\n')  # delete '\n' in each word
        st.extend(
            ['allow', 'outcomes', 'some', 'mini', 'another', 'student', 'in', 'or', 'either', 'final', 'exam', 'mid',
             'by', 'areas', 'also', 'today', 'course', 'Outcomes:', 'will', 'Work', 'Students', 'The', 'It', 'us',
             'class', 'Learning', 'course,', ' ', 'try', 'on', 'results', 'how', 'what', 'he', 'she', 'courses',
             'professor', 'their', 'one', 'two', 'develop', 'problem', 'problems', 'perform', 're', 'job', 'ed', 'edu',
             'many', 'year', 'years', 'multi','become', 'use', 'homework', 'come', 'came', 'three', 'skills', 'art',
             'life', 'success', 'now', 'career', 'students', 'short', 'long', 'able', 'professional', 'arts', 'master',
             'across', 'field', 'target', 'using', 'cut'])
        for i in range(len(course)):
            out = ''
            for word in course[i].split(' '):
                if word not in st:
                    out = out + word + ' '
            course[i] = out

        vectorizer = CountVectorizer()  #
        transformer = TfidfTransformer()  # 词语的tf-idf权值
        tfidf = transformer.fit_transform(vectorizer.fit_transform(course))  # calculate tf-idf
        word = vectorizer.get_feature_names()  # all words in the word bag
        weight = tfidf.toarray()  # get matrix of tfidf
        key = []
        for i in range(len(weight)):
            doc = {}
            t = np.argsort(-weight[i])
            s = ''
            for j in range(40):
                # print(word[t[j]], ':', weight[i][t[j]])
                if word[t[j]] not in st:
                    s = s + ' ' + word[t[j]]
            key.append(s)
        count = []
        for i in range(len(key)):
            c = 0
            for word in key[i].split(' '):
                if word != '':
                    for j in desc:
                        a = j.count(word)
                        # print('a;:::::::::::' + str(a)+ word )
                        c += a
                print('c::::::::::;' + str(c) + word)
            count.append(c)
        recommended = set()
        for i in np.argsort(count)[-4:]:

            recommended.add(data.course_df['course_id'][i] + ": " + data.course_df['names'][i] + ',course rate:' +
                            '%.2f' % data.course_df['Overall course rate'][i])
        print("COURSES RECOMMENDED:")
        for i in recommended:
            print(i)
        pass

    def recommend_job(self, jobs_df):
        pass


class Data:
    def __init__(self, consulting_file, sde_file, ds_file, course_evl_file, course_info_file, company_loc_file,
                 rent_file):
        self.consulting_df = pd.read_csv(consulting_file)
        self.sde_df = pd.read_csv(sde_file)
        self.ds_df = pd.read_csv(ds_file)

        course_evl_df = pd.read_csv(course_evl_file)
        course_info_df = pd.read_csv(course_info_file)

        course_evl_df = course_evl_df.drop(
            ['Hrs Per Week 8', 'Interest in student learning', 'Clearly explain course requirements',
             'Clear learning objectives & goals', 'Instructor provides feedback to students to improve',
             'Demonstrate importance of subject matter', 'Explains subject matter of course',
             'Show respect for all students', 'Possible Respondents', 'Num Respondents',
             'Response Rate %', 'Hrs Per Week 5'], axis=1)

        course_evl_df = course_evl_df[course_evl_df['Level'] == 'Graduate']

        course_evl_combine_df = pd.DataFrame(
            course_evl_df.groupby('Course ID')['Overall course rate'].mean()).reset_index()

        self.course_df = course_evl_combine_df.merge(course_info_df, how="outer", left_on="Course ID",
                                                     right_on="course_id")
        self.company_loc_df = pd.read_csv(company_loc_file)
        self.rent_df = pd.read_csv(rent_file)

    @staticmethod
    def update(filename):
        print("Updating " + filename)
        if filename == CONSULTING_FILE:
            glassdoor.crawl(file, "consultant", "entrylevel", max_page=19)
        elif filename == SDE_FILE:
            glassdoor.crawl(file, "software engineer", "entrylevel", max_page=29)
        elif filename == DS_FILE:
            glassdoor.crawl(file, "data scientist", "entrylevel", max_page=10)
        elif filename == COURSE_EVL_FILE:
            heinz_course_api.crawl(file)
        elif filename == COURSE_INFO_FILE:
            print("We need your andrew ID and password to log in smartevls.com to get course evaluation data")
            smartevals.crawl(file, input("Please enter your andrew ID:"), input("Please enter your password"))
        elif filename == COMPANY_LOC_FILE:
            geo.crawl(COMPANY_LOC_FILE)
        elif filename == RENT_FILE:
            rent.download(file)

    def hist_salary(self, career):
        if career == "data scientist":
            df = self.ds_df
        elif career == 'software engineer developer':
            df = self.sde_df
        else:  # career == 'consultant'
            df = self.consulting_df

        df = df.loc[:, ["name", 'salary_low', 'salary_high']]
        df['avg_salary'] = df.mean(axis=1)
        boot_df = df['avg_salary'].sample(frac=10, replace=True)  # bootstrap to increase sample
        boot_df = boot_df[np.abs(boot_df - boot_df.mean()) <= (3 * boot_df.std())]  # remove outlier (>3sigma)
        fig, ax = plt.subplots()
        boot_df.plot.kde(ax=ax, legend=False, title='Salary for Data Scientist')
        boot_df.plot.hist(density=True, ax=ax)
        ax.grid(axis='y')
        ax.set_facecolor('#d8dcd6')
        plt.show()

    def hist_review(self, career):
        if career == "data scientist":
            df = self.ds_df
        elif career == 'software engineer developer':
            df = self.sde_df
        else:  # career == 'consultant':
            df = self.consulting_df

        fig, ax = plt.subplots()
        df['company_review'].plot.kde(ax=ax, legend=False, title='Company Review Score for Data Scientist')
        df['company_review'].plot.hist(density=True, ax=ax, color='skyblue')
        ax.grid(axis='y')
        ax.set_facecolor('#d8dcd6')
        plt.show()

    def job_wc(self, career):
        if career == "data scientist":
            df = self.ds_df
            new_words = ['experience', 'entry', 'level', 'position', 'work', 'Job', 'will', 'required', 'requirement',
                         'team', 'project', 'provide', 'knowledge']
        elif career == 'software engineer developer':
            df = self.sde_df
            new_words = ['experience', 'entry', 'level', 'position', 'work', 'Job', 'will', 'required', 'requirement',
                         'team', 'project', 'provide', 'knowledge', 'Jobs']
        else:  # career == 'consultant':
            df = self.consulting_df
            new_words = ['experience', 'entry', 'level', 'position', 'work', 'Job', 'will', 'required', 'requirement',
                         'team', 'project', 'provide', 'knowledge', 'Jobs']

        your_list = []
        for i in df['description']:
            your_list.append(i + ' ')
        s = ''.join(your_list)
        stopwords = set(STOPWORDS)

        # append new words to the stopwords list
        new_stopwords = stopwords.union(new_words)
        wc = WordCloud(background_color="white",
                       width=800, height=600, margin=2,
                       stopwords=new_stopwords
                       )
        wc.generate(s)
        plt.figure(figsize=(10, 10))
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")

    def job_map(self, career):
        if career == 'data scientist':
            df = self.ds_df
        elif career == 'software engineer developer':
            df = self.sde_df
        else:  # career == 'consultant':
            df = self.consulting_df

        # count job num
        df = df.dropna().groupby(['state'], as_index=False)['state'].agg({'cnt': 'count'})
        df = df.iloc[1:]
        df['cnt'] = pd.to_numeric(df['cnt']).astype(float)

        # draw map
        map_data = dict(type='choropleth',
                        colorscale='Viridis',
                        locations=df['state'],
                        z=df['cnt'],
                        locationmode='USA-states',
                        marker=dict(line=dict(color='rgb(255,255,255)', width=2)),
                        colorbar={'title': "Count of jobs"}
                        )

        layout = dict(title='Consultant Job Distribution around US',
                      geo=dict(scope='usa', showlakes=True))
        choromap = go.Figure(data=[map_data], layout=layout)
        plotly.offline.plot(choromap, filename='image/job_map.html')

    def rent_map(self):
        map_data = dict(type='choropleth',
                        colorscale='Viridis',
                        reversescale=True,
                        locations=self.rent_df['state'],
                        z=self.rent_df['rent'],
                        locationmode='USA-states',
                        text=self.rent_df['Region Name'],
                        marker=dict(line=dict(color='rgb(255,255,255)', width=1)),
                        colorbar={'title': "Rent(yearly)"})
        layout = dict(title='Rent Distribution around US',
                      geo=dict(scope='usa',
                               showlakes=True))

        choromap = go.Figure(data=[map_data], layout=layout)
        plotly.offline.plot(choromap, filename='image/rent_map.html')


if __name__ == "__main__":
    # TODO some fancy welcome message

    # instantiate Data
    # check if exist
    files_list = [CONSULTING_FILE, SDE_FILE, DS_FILE, COURSE_EVL_FILE, COURSE_INFO_FILE, COMPANY_LOC_FILE, RENT_FILE]
    for file in files_list:
        if not Path(file).is_file():
            Data.update(file)

    database = Data(*files_list)

    # instantiate Person
    # person = Person(input("Please enter your career:").lower(), input("Please enter your location:").lower())
    person = Person("consultant", "New York")

    # recommend
    # person.recommend_job()
    # person.recommend_course()
    # database.hist_salary(person.career)
    # database.hist_review(person.career)
    # database.job_wc(person.career)
    # database.heat_map(person.career)
