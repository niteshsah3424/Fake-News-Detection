import pickle
import re

# load model
model = pickle.load(open("models/model.pkl","rb"))
vectorizer = pickle.load(open("models/vectorizer.pkl","rb"))

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z ]', '', text)
    return text

def predict_news(news):

    news = clean_text(news)
    vector = vectorizer.transform([news])

    prediction = model.predict(vector)
    probability = model.predict_proba(vector)

    fake_prob = probability[0][0]
    real_prob = probability[0][1]

    if prediction[0] == 0:
        return "FAKE NEWS", fake_prob
    else:
        return "REAL NEWS", real_prob


news = input("Enter News Article: ")

result, confidence = predict_news(news)

print("Prediction:", result)
print("Confidence:", round(confidence*100,2), "%")