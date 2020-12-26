import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from predictor import Regressor
from OSMPythonTools.overpass import Overpass
from streamlit_folium import folium_static
import folium

plt.style.use('seaborn')
TITLE_TEXT = """
This app helps you set a competitive rental price for your Airbnb property in London.
"""
ADDITIONAL = '<span style="font-size:1.5em">{0}</span>'
BREAK = '<br>'
DEFAULT_TEXT = 'Enter your text here...'
amenities = ["Ironing Board", 'Gym', "Safety card", 'Microwave', 'Printer',
             "Family/kid friendly", "Smart lock",
             "Bath towel", "Projector and screen", "Breakfast table", "Bed linens",
             'TV', 'Other', "Hair dryer", "Dishes", "Patio or balcony", "Shower",
             'Toilet', 'Washer', "Heated floors", "Extra pillows and blankets",
             "Wheelchair accessible", 'Internet', 'Pool', 'Breakfast', "Outdoor parking",
             'Wi-Fi', "Table corner guards", "BBQ grill", "24-hour check-in",
             "Air conditioning", 'Refrigerator', 'Elevator', "Smoking allowed",
             'Dishwasher', "Long term stays allowed", "Pets allowed", 'Kitchen',
             "Suitable for events", "Smoke detector", 'Bidet', 'Netflix'
             ]
MATCH_NEIRBOORHOOD = {'Richmond upon Thames': 151795, 'Camden': 170683,
                      'Kensington and Chelsea': 51793, 'Westminster': 51781, 'Hammersmith and Fulham': 184484,
                      'Lambeth': 184710, 'Southwark': 8450265, 'Haringey': 51814, 'Tower Hamlets': 51805,
                      'Hackney': 51806, 'Merton': 51905, 'Hounslow': 51848, 'Newham': 185505,
                      'Brent': 75767, 'Barking and Dagenham': 185483, 'Kingston upon Thames': 51909,
                      'Sutton': 17529, 'Bexley': 51903, 'Hillingdon': 183779, 'Greenwich': 51902,
                      'Waltham Forest': 65595, 'Croydon': 51907, 'Redbridge': 65598, 'City of London': 4001857,
                      'Bromley': 152126, 'Harrow': 181292, 'Havering': 185478}

regressor = Regressor()

st.markdown("# 🇬🇧 Airbnb price predictor" + BREAK, unsafe_allow_html=True)
st.markdown(ADDITIONAL.format(TITLE_TEXT) + 2 * BREAK, unsafe_allow_html=True)
st.markdown(ADDITIONAL.format('**Set info about your property:**'), unsafe_allow_html=True)

# Name
name = st.text_area('Name of property:', value=DEFAULT_TEXT)
# Description
description = st.text_area('Description:', value=DEFAULT_TEXT)

col1, col2 = st.beta_columns(2)
with col1:
    # Property type
    property_type = st.selectbox('Property type:', options=list(regressor.ohe_property.categories_[0]))
with col2:
    # Room type
    room_type = st.selectbox('Room type:', options=list(regressor.ord_room.categories_[0]))

col1, col2, col3 = st.beta_columns(3)
with col1:
    # Beds
    beds = st.number_input('Number of beds:', min_value=0, step=1, value=0, format='%i')
with col2:
    # Bed type
    bed_type = st.selectbox('Bed type:', options=list(regressor.ord_bed.categories_[0]))
with col3:
    # Bathrooms
    baths = st.number_input('Number of bathrooms:', min_value=0, step=1, value=0, format='%i')

# Amenities
amen = st.number_input('Number of amenities:', min_value=0, step=1, value=0, format='%i')
with st.beta_expander("See possible amenities"):
    col1, col2 = st.beta_columns(2)
    with col1:
        for i in range(len(amenities) // 2):
            st.markdown('+ ' + amenities[i])
    with col2:
        for i in range(len(amenities) // 2, len(amenities)):
            st.markdown('+ ' + amenities[i])
st.markdown(2 * BREAK, unsafe_allow_html=True)

col1, col2, col3 = st.beta_columns(3)
with col1:
    # Guest included
    guests = st.number_input('Guests included:', min_value=0, step=1, value=0, format='%i')
with col2:
    # Extra people
    extra_peop = st.number_input('Extra people:', min_value=0, step=1, value=0, format='%i')
with col3:
    # Minimum nights
    min_nights = st.number_input('Minimum nights:', min_value=0, step=1, value=0, format='%i')
# Cancellation policy
policies = list(regressor.ord_pol.categories_[0])
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
    neigh = st.selectbox('Neighbourhood cleansed:', options=list(regressor.ohe_neigh.categories_[0]))
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
    num_busy = st.number_input('Total number of booking days', min_value=0, step=1, value=0, format='%i')

st.markdown(BREAK, unsafe_allow_html=True)
st.markdown(ADDITIONAL.format('**Set info about you:**'), unsafe_allow_html=True)
# Host since
host_since = st.date_input("You are host since:", datetime.date.today())
# Is superhost
is_superhost = st.checkbox('I\'m a superhost')
# Profile pic
profile_pic = st.checkbox('I have a profile picture')
# Identity verified
identity = st.checkbox('My identity is verified')


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


local_css("style.css")
button_clicked = st.button('Go!')


def create_map(lat, lon):
    api = Overpass()
    # London
    map_london = folium.Map(location=[51.5073219, -0.1276474], zoom_start=10)
    
    if neigh not in ['Barnet', 'Ealing', 'Enfield', 'Islington', 'Lewisham', 'Wandsworth']:
      buff_resp = 'rel(' + str(MATCH_NEIRBOORHOOD[neigh]) + '); out geom;'
      response = api.query(buff_resp)
      geom = response.elements()[0]
      bound = [(i[-1], i[0]) for i in geom.geometry()['coordinates'][0]]
      folium.Polygon(bound, popup=f'Bound of {neigh}').add_to(map_london)
      
    # Add Apart
    folium.Marker([lat, lon], popup="Apartment", tooltip="Apartment",
                  icon=folium.Icon(icon='home', prefix='fa')).add_to(map_london)
    folium.Marker(regressor.london_center, popup="Center of London", tooltip="Center of London",
                  icon=folium.Icon(color='lightred', icon='flag', prefix='fa')).add_to(map_london)
    folium_static(map_london)


if button_clicked:
    columns = ['name', 'description', 'lat', 'lon', 'frequency', 'host_since', 'host_is_superhost',
               'host_has_profile_pic',
               'host_identity_verified', 'is_location_exact', 'room_type', 'bathrooms',
               'beds', 'bed_type', 'amenities', 'guests_included', 'extra_people',
               'minimum_nights', 'cancellation_policy', 'property_type', 'neighbourhood_cleansed'
               ]
    days_amount = (pd.to_datetime(start) - pd.to_datetime(end)).days + 1
    freq = (days_amount - num_busy) / days_amount
    data = [name, description, lat, lon, freq, host_since, is_superhost,
            profile_pic, identity, is_loc_exact, room_type, baths, beds, bed_type,
            amen, guests, extra_peop, min_nights, cancel, property_type, neigh]

    df = pd.DataFrame(data=[data], columns=columns)
    price = regressor.predict(df)

    if price:
        st.markdown(BREAK, unsafe_allow_html=True)
        st.markdown(ADDITIONAL.format(f'**Recommended price: {round(price, 2)}£**'),
                    unsafe_allow_html=True)
    else:
        st.markdown(ADDITIONAL.format('Something went wrong...'))

    st.markdown(ADDITIONAL.format('Average price per neighbourhood:'), unsafe_allow_html=True)
    mean_neigh = pd.read_csv('./mean_neighbourhood.csv')
    fig, ax = plt.subplots(figsize=(10, 10))
    neighs = list(mean_neigh.neighbourhood_cleansed.values)
    colors = ['teal' for _ in range(len(neighs))]
    colors[neighs.index(neigh)] = 'maroon'
    ax.barh(mean_neigh.neighbourhood_cleansed.values,
            mean_neigh.price.values, color=colors)
    ax.set_xlabel('Price, £')
    st.pyplot(fig)
    st.markdown(ADDITIONAL.format('Map:'), unsafe_allow_html=True)
    create_map(lat, lon)
    st.markdown(ADDITIONAL.format(f'You entered the coordinates: ({lat}, {lon})'), unsafe_allow_html=True)
    st.markdown(ADDITIONAL.format(f'Distance from center: {round(regressor.distance, 3)}km'), unsafe_allow_html=True)
