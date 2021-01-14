import datetime

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import folium
from OSMPythonTools.overpass import Overpass
from streamlit_folium import folium_static

from predictor import Regressor
plt.style.use('seaborn')


NEIGHBOURS_PATH = './mean_neighbourhood.csv'
TITLE_TEXT = """This app helps you set a competitive rental price for your 
Airbnb property in London. """
WRAPPER = '<span style="font-size:1.5em">{0}</span>'
BREAK = '<br>'
DEFAULT_TEXT = 'Enter your text here...'
AMENITIES = ["Ironing Board", "Gym", "Safety card", "Microwave", "Printer",
             "Family/kid friendly", "Smart lock", "Bath towel",
             "Projector and screen", "Breakfast table", "Bed linens",
             "TV", "Other", "Hair dryer", "Dishes", "Patio or balcony",
             "Shower", "Toilet", "Washer", "Heated floors",
             "Extra pillows and blankets", "Wheelchair accessible",
             "Internet", "Pool", "Breakfast", "Outdoor parking",
             "Wi-Fi", "Table corner guards", "BBQ grill", "24-hour check-in",
             "Air conditioning", "Refrigerator", "Elevator", "Smoking allowed",
             "Dishwasher", "Long term stays allowed", "Pets allowed", "Kitchen",
             "Suitable for events", "Smoke detector", "Bidet", "Netflix"
             ]
NEIGH_CODES = {'Richmond upon Thames': 151795, 'Camden': 170683,
               'Kensington and Chelsea': 51793, 'Westminster': 51781,
               'Hammersmith and Fulham': 184484, 'Lambeth': 184710,
               'Southwark': 8450265, 'Haringey': 51814, 'Tower Hamlets': 51805,
               'Hackney': 51806, 'Merton': 51905, 'Hounslow': 51848,
               'Newham': 185505, 'Brent': 75767, 'Barking and Dagenham': 185483,
               'Kingston upon Thames': 51909, 'Sutton': 17529, 'Bexley': 51903,
               'Hillingdon': 183779, 'Greenwich': 51902,
               'Waltham Forest': 65595, 'Croydon': 51907, 'Redbridge': 65598,
               'City of London': 4001857, 'Bromley': 152126,
               'Harrow': 181292, 'Havering': 185478
               }
NEIGHS_WITHOUT_CODE = ['Barnet', 'Ealing', 'Enfield',
                       'Islington', 'Lewisham', 'Wandsworth'
                       ]
MAP_CENTER = [51.5073219, -0.1276474]


def local_css(file_name: str) -> None:
    """Setup CSS style."""
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


def create_map(lat: float, lon: float, neigh: str, center: tuple) -> None:
    """Create a map of London and add elements to it."""
    api = Overpass()
    map_london = folium.Map(location=MAP_CENTER, zoom_start=10)

    # Bound of neighbourhood
    if neigh not in NEIGHS_WITHOUT_CODE:
        request = 'rel(' + str(NEIGH_CODES[neigh]) + '); out geom;'
        response = api.query(request)
        geom = response.elements()[0]
        bound = [(i[-1], i[0]) for i in geom.geometry()['coordinates'][0]]
        folium.Polygon(bound, popup=f'Bound of {neigh}').add_to(map_london)

    # Add markers
    folium.Marker([lat, lon], popup="Apartment", tooltip="Apartment",
                  icon=folium.Icon(icon='home', prefix='fa')).add_to(map_london)
    folium.Marker(center, popup="Center of London",
                  tooltip="Center of London",
                  icon=folium.Icon(color='lightred', icon='flag',
                                   prefix='fa')).add_to(map_london)
    folium_static(map_london)


def main() -> None:
    """Main function of the app."""
    local_css("style.css")
    model = Regressor()
    st.markdown("# 🇬🇧 Airbnb price predictor" + BREAK, unsafe_allow_html=True)
    st.markdown(WRAPPER.format(TITLE_TEXT) + 2 * BREAK, unsafe_allow_html=True)
    st.markdown(WRAPPER.format('**Set info about your property:**'),
                unsafe_allow_html=True)

    # Name
    name = st.text_area('Name of property:', value=DEFAULT_TEXT)
    # Description
    description = st.text_area('Description:', value=DEFAULT_TEXT)

    # Property type and room type
    col1, col2 = st.beta_columns(2)
    with col1:
        prop_type = st.selectbox('Property type:',
                                 options=list(model.ohe_property.categories_[0]))
    with col2:
        room_type = st.selectbox('Room type:',
                                 options=list(model.ord_room.categories_[0]))

    # Beds / Bed type / Bathrooms
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        beds = st.number_input('Number of beds:', min_value=0, step=1,
                               value=0, format='%i')
    with col2:
        bed_type = st.selectbox('Bed type:',
                                options=list(model.ord_bed.categories_[0]))
    with col3:
        baths = st.number_input('Number of bathrooms:', min_value=0, step=1,
                                value=0, format='%i')

    # Amenities
    amenities = st.number_input('Number of amenities:', min_value=0, step=1,
                                value=0, format='%i')
    with st.beta_expander("See possible amenities"):
        col1, col2 = st.beta_columns(2)
        with col1:
            for i in range(len(AMENITIES) // 2):
                st.markdown('+ ' + AMENITIES[i])
        with col2:
            for i in range(len(AMENITIES) // 2, len(AMENITIES)):
                st.markdown('+ ' + AMENITIES[i])
    st.markdown(2 * BREAK, unsafe_allow_html=True)

    # Guest included / Extra people / Minimum nights
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        guests = st.number_input('Guests included:', min_value=0, step=1,
                                 value=0, format='%i')
    with col2:
        extra_people = st.number_input('Extra people:', min_value=0, step=1,
                                       value=0, format='%i')
    with col3:
        min_nights = st.number_input('Minimum nights:', min_value=0, step=1,
                                     value=0, format='%i')

    # Cancellation policy
    policies = list(model.ord_pol.categories_[0])
    new_policies = [i.replace('_', ' ') for i in policies]
    new_policies = [i[0].upper() + i[1:] for i in new_policies]
    pol_dict = {}
    for pol1, pol2 in zip(new_policies, policies):
        pol_dict[pol1] = pol2
    cancel = st.selectbox('Cancellation policy', options=new_policies)
    cancel = pol_dict[cancel]

    # Location
    st.markdown('**Enter location of your property:**')
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        lat = st.number_input('Latitude:', step=1e-6, format='%f')
    with col2:
        lon = st.number_input('Longitude:', step=1e-6, format='%f')
    with col3:
        # Neighbourhood
        neigh = st.selectbox('Neighbourhood cleansed:',
                             options=list(model.ohe_neigh.categories_[0]))
    # Is loc exact
    is_loc_exact = st.checkbox('Location is exact')

    # Frequency
    st.markdown('**Property was exhibited:**')
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        start = st.date_input('Since:', datetime.date.today())
    with col2:
        end = st.date_input('To:', datetime.date.today())
    with col3:
        num_busy = st.number_input('Total number of booking days', min_value=0,
                                   step=1, value=0, format='%i')

    st.markdown(BREAK, unsafe_allow_html=True)
    st.markdown(WRAPPER.format('**Set info about you:**'),
                unsafe_allow_html=True)
    # Host since
    host_since = st.date_input("You are host since:", datetime.date.today())
    # Is superhost
    is_superhost = st.checkbox('I\'m a superhost')
    # Profile pic
    profile_pic = st.checkbox('I have a profile picture')
    # Identity verified
    identity = st.checkbox('My identity is verified')

    button_clicked = st.button('Go!')

    if button_clicked:
        columns = ['name', 'description', 'lat', 'lon', 'frequency',
                   'host_since', 'host_is_superhost', 'host_has_profile_pic',
                   'host_identity_verified', 'is_location_exact', 'room_type',
                   'bathrooms', 'beds', 'bed_type', 'amenities',
                   'guests_included', 'extra_people', 'minimum_nights',
                   'cancellation_policy', 'property_type',
                   'neighbourhood_cleansed'
                   ]

        # Collect input data and make a prediction
        days_amount = (pd.to_datetime(start) - pd.to_datetime(end)).days + 1
        freq = (days_amount - num_busy) / days_amount
        data = [name, description, lat, lon, freq, host_since, is_superhost,
                profile_pic, identity, is_loc_exact, room_type, baths, beds,
                bed_type, amenities, guests, extra_people, min_nights, cancel,
                prop_type, neigh
                ]

        df = pd.DataFrame(data=[data], columns=columns)
        price = model.predict(df)

        if price:
            st.markdown(BREAK, unsafe_allow_html=True)
            text = WRAPPER.format(f'**Recommended price: {round(price, 2)}£**')
            st.markdown(text, unsafe_allow_html=True)
        else:
            st.markdown(WRAPPER.format('Something went wrong...'))

        # Average price plot
        st.markdown(WRAPPER.format('Average price per neighbourhood:'),
                    unsafe_allow_html=True)
        mean_neigh = pd.read_csv(NEIGHBOURS_PATH)
        fig, ax = plt.subplots(figsize=(10, 10))
        neighbours = list(mean_neigh.neighbourhood_cleansed.values)
        colors = ['teal' for _ in range(len(neighbours))]
        colors[neighbours.index(neigh)] = 'maroon'
        ax.barh(mean_neigh.neighbourhood_cleansed.values,
                mean_neigh.price.values, color=colors)
        ax.set_xlabel('Price, £')
        st.pyplot(fig)

        # Display a map
        st.markdown(WRAPPER.format('Map:'), unsafe_allow_html=True)
        create_map(lat, lon, neigh, model.london_center)
        text = WRAPPER.format(f'You entered the coordinates: ({lat}, {lon})')
        st.markdown(text, unsafe_allow_html=True)
        distance = round(model.distance, 3)
        text = WRAPPER.format(f'Distance from center: {distance}km')
        st.markdown(text, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
