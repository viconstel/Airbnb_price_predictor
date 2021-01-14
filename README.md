## 🇬🇧 Airbnb price predictor

This app helps you set a competitive rental 
price for your Airbnb property in London.

**LGBMRegressor** is used as a regression model 
with pre-trained feature transformers and replacement 
of missing values with a median strategy.
During training, the **MAPE** metric is optimized. 
Since this metric does not coincide with 
the loss function of most algorithms, 
it's optimization is reduced to optimizing 
the **MAE** metric by taking the logarithm of the 
target values.

Demo of this app is available by the link
(*if it didn't load quickly, you need to
 wait a little, Heroku needs to wake up*):\
[Airbnb price predictor](https://nameless-oasis-11721.herokuapp.com/)