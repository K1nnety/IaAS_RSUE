import pandas as pd
import numpy as np
import random

def generate_university_data(filename="university_grades.xlsx"):
    directions = {
        "Прикладная информатика": "ПИ",
        "Информационная безопасность": "ИБ",
        "Информационные системы и технологии": "ИСТ"
    }
    
    course_subjects = {
        1: ["Математика", "История", "Информатика"],
        2: ["Программирование", "Физика", "Дискретная математика"],
        3: ["Базы данных", "Сети и телекоммуникации", "Операционные системы"],
        4: ["Методы минимизации рисков", "Проектирование ИС", "Защита данных"]
    }
    
    surnames = ["Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Васильев", "Павлов", "Соколов", "Михайлов", "Белов", "Чернов", "Новиков", "Козлов", "Морозов"]
    chars = "АБВГДЕИКЛМНОПРСТ"

    all_data = []
    
    START_YEAR = 2022
    END_YEAR = 2025 

    for dir_name, dir_code in directions.items():
        for group_num in [1, 2]:
            
            for start_year in range(START_YEAR, END_YEAR + 1):
                num_students = random.randint(15, 21)
                student_list = [f"{random.choice(surnames)} {random.choice(chars)}.{random.choice(chars)}." for _ in range(num_students)]
                
                
                for level in range(1, 5):
                    current_academic_year_start = start_year + level - 1
                    
                    
                    if current_academic_year_start > END_YEAR:
                        continue
                        
                    academic_year = f"{current_academic_year_start}/{current_academic_year_start + 1}"
                    group_id = f"{dir_code}-{level}0{group_num}"
                    subjects = course_subjects[level]
                    
                    for student in student_list:
                        for sub in subjects:
                            grade = random.randint(75, 98)
                            
                            
                            if dir_code == "ИБ" and level >= 2:
                                grade -= (level * 5) + random.randint(0, 5)
                            
                            all_data.append([
                                dir_name, 
                                academic_year, 
                                level, 
                                group_id, 
                                student, 
                                sub, 
                                max(grade, 40)
                            ])

    df = pd.DataFrame(all_data, columns=["Направление", "Учебный_год", "Курс", "Группа", "Студент", "Предмет", "Итоговая_оценка"])
    df = df.drop_duplicates()
    df = df.sort_values(["Учебный_год", "Курс", "Группа"])
    
    df.to_excel(filename, index=False)
    print(f"✅ Файл '{filename}' готов!")
    print(f"Записей: {len(df)}")
    print(f"Текущий срез (25/26): {len(df[df['Учебный_год']=='2025/2026'])} записей.")

if __name__ == "__main__":

    generate_university_data()
