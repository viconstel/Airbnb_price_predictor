import joblib
import streamlit as st
import pandas as pd
import numpy as np
import nltk
from scipy.sparse import hstack
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
import re
from haversine import haversine

nltk.download('stopwords')

stemmer = SnowballStemmer("english")


class Regressor(object):

    def __init__(self):
        (self.imp, self.scaler, self.ord_bed,
         self.ord_pol, self.ord_room, self.ohe_neigh,
         self.ohe_property, self.model) = self.load_pickles()

        self.binary_columns = ['host_is_superhost', 'host_has_profile_pic',
                               'host_identity_verified', 'is_location_exact']

        self.scale_col = ['frequency', 'to_center', 'host_since',
                          'room_type', 'bathrooms', 'beds', 'bed_type',
                          'amenities', 'guests_included', 'extra_people',
                          'minimum_nights', 'cancellation_policy']

        self.distance = None
        self.london_center = [51.5073219, -0.1276474]

    def load_pickles(self):
        ans = []
        imp = joblib.load('./pickles/imp.pkl')
        ans.append(imp)
        scaler = joblib.load('./pickles/scaler.pkl')
        ans.append(scaler)
        ord_bed = joblib.load('./pickles/ord_bed.pkl')
        ans.append(ord_bed)
        ord_pol = joblib.load('./pickles/ord_pol.pkl')
        ans.append(ord_pol)
        ord_room = joblib.load('./pickles/ord_room.pkl')
        ans.append(ord_room)
        ohe_neigh = joblib.load('./pickles/ohe_neigh.pkl')
        ans.append(ohe_neigh)
        ohe_property = joblib.load('./pickles/ohe_property.pkl')
        ans.append(ohe_property)
        model = joblib.load('./pickles/model.pkl')
        ans.append(model)

        return ans

    def preproc(self, df):
        # Process text
        df.drop(columns=['name', 'description'], inplace=True)

        # host_since
        df['host_since'] = df.host_since.apply(
            lambda x: max(0, (pd.to_datetime('2018-11-04') - pd.to_datetime(x)).days))
        # true/false columns
        df.loc[:, self.binary_columns] = df.loc[:, self.binary_columns].replace([True, False], [1, 0])
        # lat/lon

        df.loc[0, 'to_center'] = haversine((df.lat, df.lon), self.london_center)
        df = df[['to_center'] + list(df.columns)[:-1]]
        df = df.drop(columns=['lat', 'lon'])
        self.distance = df.to_center.values[0]
        df.to_center = df.to_center.apply(np.log)
        # room_type
        room_types = list(self.ord_room.categories_[0])
        df.room_type = room_types.index(df.room_type[0])

        # bed_type
        bed_types = list(self.ord_bed.categories_[0])
        df.bed_type = bed_types.index(df.bed_type[0])

        # cancellation_policy
        cancel = list(self.ord_pol.categories_[0])
        df.cancellation_policy = cancel.index(df.cancellation_policy[0])

        # property_type
        trans = self.ohe_property.transform(df.property_type.values.reshape(-1, 1))
        one = pd.DataFrame(trans.toarray(),
                           columns=[f'P_{i}' for i in range(len(self.ohe_property.categories_[0]))])
        df = pd.concat((df, one.reindex(df.index)), axis=1)
        df = df.drop(columns=['property_type'])

        # neighbourhood_cleansed
        trans = self.ohe_neigh.transform(df.neighbourhood_cleansed.values.reshape(-1, 1))
        one = pd.DataFrame(trans.toarray(),
                           columns=[f'N_{i}' for i in range(len(self.ohe_neigh.categories_[0]))])
        df = pd.concat((df, one.reindex(df.index)), axis=1)
        df = df.drop(columns=['neighbourhood_cleansed'])

        # fill missing values
        df.loc[:, :] = self.imp.transform(df)

        # scaling
        df.loc[:, self.scale_col] = self.scaler.transform(df[self.scale_col])

        return df

    def predict(self, df):
        try:
            df = self.preproc(df)
            price = self.model.predict(df)[0]
            return np.exp(price)
        except:
            return None, None

    @staticmethod
    def text_preproc(sentence):
        cleaned = re.sub(r'[?|!|\'|"|#]', r'', sentence)
        cleaned = re.sub(r'[.|,|)|(|\|/]', r' ', cleaned)
        cleaned = cleaned.strip()
        sentence = cleaned.replace("\n", " ")

        alpha_sent = ""
        for word in sentence.split():
            alpha_word = re.sub('[^a-z A-Z]+', ' ', word)
            alpha_sent += alpha_word
            alpha_sent += " "
        sentence = alpha_sent.strip()

        stop_words = set(stopwords.words('english'))
        re_stop_words = re.compile(r"\b(" + "|".join(stop_words) + ")\\W", re.I)
        sentence = re_stop_words.sub(" ", sentence)

        # stemSentence = ""
        # for word in sentence.split():
        #     stem = stemmer.stem(word)
        #     stemSentence += stem
        #     stemSentence += " "
        # sentence = stemSentence.strip()

        return sentence
