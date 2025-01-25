from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import sqlite3
import pandas as pd
import os
import numpy as np
# Опционально - визуализация
import matplotlib.pyplot as plt

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'ml_data.db')
conn = sqlite3.connect(db_path)
query = "SELECT * FROM trading_data_ml"
df = pd.read_sql_query(query, conn)
conn.close()

# Обработка данных
df.drop('id', axis=1, inplace=True)
target_column = 'target'  # Столбец с метками
df[target_column] = df[target_column].apply(lambda x: 1 if x == "Buy" else 0)  # Бинаризация таргета

class_counts = df[target_column].value_counts()
class_0_count = class_counts[0]
class_1_count = class_counts[1]

# Уравнивание классов путем удаления избыточных "0"
if class_0_count > class_1_count:
    # Отбираем только необходимое количество записей класса "0"
    df_class_0 = df[df[target_column] == 0].sample(n=class_1_count, random_state=42)
    # Берем все записи класса "1"
    df_class_1 = df[df[target_column] == 1]
    # Объединяем в один сбалансированный DataFrame
    df_balanced = pd.concat([df_class_0, df_class_1])
else:
    # Если вдруг "1" больше, повторяем для "1"
    df_class_1 = df[df[target_column] == 1].sample(n=class_0_count, random_state=42)
    df_class_0 = df[df[target_column] == 0]
    df_balanced = pd.concat([df_class_0, df_class_1])

# Перемешиваем данные для случайного распределения
df_balanced = df_balanced.sample(frac=1, random_state=42).reset_index(drop=True)
df = df_balanced.copy()
print(len(df))

features = df.drop(columns=[target_column])
labels = df[target_column]

# Удаление признаков, начинающихся с '_1' и '_3'
columns_to_remove = [col for col in features.columns if col.startswith('_1')]
features_reduced = features.drop(columns=columns_to_remove)
features = features_reduced

# Разделение данных на тренировочный и тестовый наборы
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# Обучение модели
# model = CatBoostClassifier(
#     iterations=3000,
#     learning_rate=0.05,
#     depth=10,
#     loss_function='Logloss',
#     eval_metric='AUC',
#     random_seed=42,
#     verbose=100
# )

# model = CatBoostClassifier(
#     iterations=1000,
#     learning_rate=0.05,
#     depth=8,
#     loss_function='Logloss',
#     eval_metric='AUC',
#     random_seed=42,
#     l2_leaf_reg=3,
#     verbose=100,
#     early_stopping_rounds=50
# )

model = CatBoostClassifier(
    iterations=1500,
    learning_rate=0.01,
    depth=10,
    loss_function='Logloss',
    eval_metric='Precision',
    random_seed=42,
    early_stopping_rounds=50
)

model.fit(X_train, y_train, verbose=100)

y_pred = model.predict(X_test)

print("Classification Report перед удалением :")
print(classification_report(y_test, y_pred, target_names=['Not Buy', 'Buy']))


# Предсказания с учетом вероятности
y_proba = model.predict_proba(X_test)
threshold = 0.7  # Порог вероятности
y_pred = np.where(y_proba[:, 1] > threshold, 1, 0)

# Метрики
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=['Not Buy', 'Buy']))
