import pandas as pd

def create_empty_university_template(filename="university_grades_template.xlsx"):
    """
    Создаёт пустой шаблон Excel-файла с той же структурой,
    что и в generate_university_data.py
    """
    
    columns = [
        "Направление",
        "Учебный_год",
        "Курс",
        "Группа",
        "Студент",
        "Предмет",
        "Итоговая_оценка"
    ]
    
    
    df_empty = pd.DataFrame(columns=columns)
    
    
    df_empty.to_excel(filename, index=False)
    
    print(f"✅ Пустой шаблон сохранён в файл: '{filename}'")
    print(f"Структура таблицы (столбцы):")
    for col in columns:
        print(f"  • {col}")
    print("\nФайл готов к заполнению преподавателем с нуля.")


if __name__ == "__main__":
    create_empty_university_template()

    
