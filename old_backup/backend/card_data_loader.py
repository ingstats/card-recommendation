import pandas as pd

def load_card_data(filepath="./backend/data/card_data.csv"):
    df = pd.read_csv(filepath)
    df.fillna("", inplace=True)
    return df