import joblib
import pandas as pd
import numpy as np
from haversine import haversine


class Regressor(object):

    """Airbnb price regression class."""

    def __init__(self) -> None:
        """Intializer of the class Regressor."""

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
        self.london_center = (51.5073219, -0.1276474)

    @staticmethod
    def load_pickles() -> list:
        """Load all pickle files."""
        files = []
        imp = joblib.load('./pickles/imp.pkl')
        files.append(imp)
        scaler = joblib.load('./pickles/scaler.pkl')
        files.append(scaler)
        ord_bed = joblib.load('./pickles/ord_bed.pkl')
        files.append(ord_bed)
        ord_pol = joblib.load('./pickles/ord_pol.pkl')
        files.append(ord_pol)
        ord_room = joblib.load('./pickles/ord_room.pkl')
        files.append(ord_room)
        ohe_neigh = joblib.load('./pickles/ohe_neigh.pkl')
        files.append(ohe_neigh)
        ohe_property = joblib.load('./pickles/ohe_property.pkl')
        files.append(ohe_property)
        model = joblib.load('./pickles/model.pkl')
        files.append(model)

        return files

    def preprocessing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Feature preprocessing with pre-trained transformers
        to get numerical feature representation for the regression model.

        :param df: - pandas.Dataframe, dataframe with the entered data.
        :return df: - pandas.DataFrame, dataframe with transformed data.
        """
        # process text
        df.drop(columns=['name', 'description'], inplace=True)

        # host_since
        start_date = pd.to_datetime('2018-11-04')
        func = lambda x: max(0, (start_date - pd.to_datetime(x)).days)
        df['host_since'] = df.host_since.apply(func)

        # binary columns
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
        new_clmns = [f'P_{i}' for i in range(len(self.ohe_property.categories_[0]))]
        one = pd.DataFrame(trans.toarray(), columns=new_clmns)
        df = pd.concat((df, one.reindex(df.index)), axis=1)
        df = df.drop(columns=['property_type'])

        # neighbourhood_cleansed
        trans = self.ohe_neigh.transform(df.neighbourhood_cleansed.values.reshape(-1, 1))
        new_clmns = [f'N_{i}' for i in range(len(self.ohe_neigh.categories_[0]))]
        one = pd.DataFrame(trans.toarray(), columns=new_clmns)
        df = pd.concat((df, one.reindex(df.index)), axis=1)
        df = df.drop(columns=['neighbourhood_cleansed'])

        # fill missing values
        df.loc[:, :] = self.imp.transform(df)

        # scaling
        df.loc[:, self.scale_col] = self.scaler.transform(df[self.scale_col])

        return df

    def predict(self, df: pd.DataFrame) -> float:
        """Make a prediction.

        :param df: - pandas.Dataframe, dataframe with the entered data.
        :return: - float, predicted price.
        """
        try:
            df = self.preprocessing(df)
            price = self.model.predict(df)[0]
            return np.exp(price)
        except:
            return None
