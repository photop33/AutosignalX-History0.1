
import pickle
import lightgbm as lgb

import os

BASE_DIR = r"C:\Users\LiorSw\PycharmProjects\AutosignalX-history\ML\log"
MODEL_FILE = os.path.join(BASE_DIR, "lgbm_model.txt")
FEATURES_FILE = os.path.join(BASE_DIR, "model_features.pkl")

def train_or_load_model(X_train, y_train, X_test, y_test):
    features_current = list(X_train.columns)

    if os.path.exists(MODEL_FILE) and os.path.exists(FEATURES_FILE):
        with open(FEATURES_FILE, "rb") as f:
            features_saved = pickle.load(f)
        if features_saved == features_current:
            print("⚡️ טוען מודל שמור מהקובץ...")
            clf = lgb.Booster(model_file=MODEL_FILE)
            return clf, X_test, y_test
        else:
            print("⚠️ רשימת הפיצ'רים השתנתה - מאמן מודל חדש")
    else:
        print("🚀 מאמן מודל חדש...")

    clf = lgb.LGBMClassifier(n_estimators=100, class_weight='balanced')
    clf.fit(X_train, y_train)

    clf.booster_.save_model(MODEL_FILE)
    with open(FEATURES_FILE, "wb") as f:
        pickle.dump(features_current, f)
    print(f"✅ שמרתי מודל לקובץ: {MODEL_FILE} ו-FEATURES")

    return clf, X_test, y_test
