from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import sqlite3
import pandas as pd
import os
import numpy as np
# Опционально - визуализация
import matplotlib.pyplot as plt

# Ваш DataFrame
# Пример: df содержит все данные, включая фичи и целевую переменную
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'ml_data.db')
# Подключаемся к базе данных
conn = sqlite3.connect(db_path)
# SQL-запрос для извлечения всех данных из таблицы trades
query = "SELECT * FROM trading_data_ml"
# Загружаем данные в DataFrame
df = pd.read_sql_query(query, conn)
conn.close()
df.drop('id', axis=1, inplace=True)
# Закрываем соединение
target_column = 'target'  # Замените на название вашего столбца с результатами
features = df.drop(columns=[target_column])
labels = df[target_column]

# Разделение данных
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)
print(f"Train size: {len(X_train)}")

# Обучение модели
model = CatBoostClassifier(
    iterations=500,
    learning_rate=0.1,
    depth=6,
    loss_function='MultiClass',
    eval_metric='MultiClass',
    random_seed=42,
    verbose=1000  # Логи обучения каждые 100 итераций
)

model.fit(X_train, y_train)

# Предсказания
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)

# Метрики
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Buy', 'Sell', 'Ignore']))

# После fit и до classification_report
y_pred_proba = model.predict_proba(X_test)
threshold = 0.6

# Конвертируем в числовые метки
y_test_numeric = pd.Categorical(y_test).codes
confident_predictions = []

for probs in y_pred_proba:
    max_prob = max(probs)
    if max_prob >= threshold:
        confident_predictions.append(np.argmax(probs))
    else:
        confident_predictions.append(2)  # Ignore если неуверены

print("\nClassification Report (with confidence threshold):")
print(classification_report(y_test_numeric, confident_predictions, target_names=['Buy', 'Sell', 'Ignore']))

# Статистика по уверенным предсказаниям
confident_trades = [i for i, probs in enumerate(y_pred_proba) if max(probs) >= threshold]
print(f"\nNumber of confident predictions: {len(confident_trades)} out of {len(y_test)}")
# print("\nConfusion Matrix:")
# print(confusion_matrix(y_test, y_pred))
#
# # Пример вероятностей для первых 5 предсказаний
# print("\nExample probabilities for the first 5 predictions:")
# print(y_proba[:5])

# После обучения модели добавьте:
feature_importance = pd.DataFrame({
   'feature': features.columns,
   'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\nTop 20 Important Features:")
print(feature_importance.head(20))

