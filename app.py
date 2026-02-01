import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io

from generate_students import generate_university_data


#Конфигурация страницы
st.set_page_config(
    page_title="ИАС Успеваемость - Аналитическая система", 
    layout="wide",
    initial_sidebar_state="expanded"
)

#Вспомогательные функции
def grade_color(val):
    """Цветовая индикация баллов в таблицах"""
    if not isinstance(val, (int, float)): return ""
    if val >= 85: return 'color: #2ecc71; font-weight: bold'
    if val >= 70: return 'color: #f39c12; font-weight: bold'
    return 'color: #e74c3c; font-weight: bold'

def get_base_group(group_name):
    """Связывает ПИ-101 и ПИ-201 как один поток обучения"""
    try:
        parts = group_name.split('-')
        if len(parts) == 2:
            
            return f"{parts[0]}-{parts[1][1:]}"
        return group_name
    except:
        return group_name

#Генерация пустого шаблона в памяти
def generate_empty_template():
    columns = [
        "Факультет",
        "Учебный_год",
        "Курс",
        "Группа",
        "Студент",
        "Предмет",
        "Итоговая_оценка"
    ]
    df_empty = pd.DataFrame(columns=columns)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_empty.to_excel(writer, index=False, sheet_name="Шаблон")
    output.seek(0)
    return output


#Интерфейс
st.title("📊 ИАС обеспечения качества образования в учебных подразделениях РГЭУ РИНХ")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("📥 Загрузите файл Excel (.xlsx)", type=["xlsx"])


#Заполненный шаблон
if st.sidebar.button("✨ Сгенерировать пример данных", type="primary"):
    with st.sidebar.spinner("Генерация данных..."):
        try:
            filename = "university_grades.xlsx"
            generate_university_data(filename)  #Создание в папке проекта
            
           
            with open(filename, "rb") as f:
                file_bytes = f.read()
            
            #Кнопка скачивания
            st.sidebar.download_button(
                label="⬇️ Скачать university_grades.xlsx",
                data=file_bytes,
                file_name="university_grades.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_generated_file"
            )
            
            st.sidebar.success("Данные сгенерированы! Нажмите кнопку выше, чтобы скачать файл.")
            st.sidebar.info("Файл не сохраняется автоматически — скачайте его вручную.")
            
        except Exception as e:
            st.sidebar.error(f"Ошибка: {e}")


#Генерация пустого шаблона
st.sidebar.markdown("---")
st.sidebar.caption("Для преподавателей")

if st.sidebar.button("📋 Создать пустой шаблон", type="secondary"):
    with st.sidebar.spinner("Подготовка шаблона..."):
        try:
            template_bytes = generate_empty_template()
            
            st.sidebar.download_button(
                label="⬇️ Скачать пустой шаблон (.xlsx)",
                data=template_bytes,
                file_name="template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_empty_template"
            )
            
            st.sidebar.success("Шаблон готов!")
            st.sidebar.info("Скачайте файл и заполните его оценками студентов.")
            
        except Exception as e:
            st.sidebar.error(f"Не удалось создать шаблон: {e}")


if not uploaded_file:
    st.info("👋 Добро пожаловать! Пожалуйста, загрузите сгенерированный Excel-файл через боковую панель для начала анализа.")
    st.stop()


try:
    df = pd.read_excel(uploaded_file, engine="openpyxl")
    df.columns = df.columns.str.strip()
    
    
    year_col = "Учебный_год" if "Учебный_год" in df.columns else "Учебный_года"
    
    if year_col not in df.columns:
        st.error(f"Критическая ошибка: Колонка '{year_col}' не найдена в Excel. Проверьте генератор данных.")
        st.stop()
        
    st.sidebar.success("✅ Данные успешно загружены")
except Exception as e:
    st.sidebar.error(f"Ошибка чтения: {e}")
    st.stop()

#Вкладки
tab_data, tab_dash, tab_trends, tab_student = st.tabs([
    "📁 Исходные данные",
    "📈 Мониторинг успеваемости", 
    "📉 Анализ трендов и падений", 
    "👤 Анализ по студенту"
])

#Просмотр исходных данных
with tab_data:
    st.subheader("Просмотр импортированной базы данных")
    st.dataframe(df, use_container_width=True, height=500)

#Мониторинг успевемости
with tab_dash:
    st.subheader("Текущие показатели подразделений")
    
    #Фильтры
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        y_select = st.selectbox("Учебный год", sorted(df[year_col].unique(), reverse=True), key="dash_y")
    with c2:
        f_select = st.selectbox("Направление", sorted(df[df[year_col]==y_select]["Факультет"].unique()), key="dash_f")
    with c3:
        c_select = st.selectbox("Курс", sorted(df[(df[year_col]==y_select) & (df["Факультет"]==f_select)]["Курс"].unique()), key="dash_c")
    with c4:
        # Фильтр по группам
        avail_gr = sorted(df[(df[year_col]==y_select) & (df["Факультет"]==f_select) & (df["Курс"]==c_select)]["Группа"].unique())
        g_select = st.selectbox("Группа", ["Все группы"] + avail_gr, key="dash_g")
    
    
    mask = (df[year_col] == y_select) & (df["Факультет"] == f_select) & (df["Курс"] == c_select)
    if g_select != "Все группы":
        mask = mask & (df["Группа"] == g_select)
        
    df_curr = df[mask]
    
    if not df_curr.empty:
        #KPI
        m1, m2, m3 = st.columns(3)
        m1.metric("Средний балл", f"{df_curr['Итоговая_оценка'].mean():.2f}")
        m2.metric("Качество обучения (>=75)", f"{(df_curr['Итоговая_оценка'] >= 75).mean()*100:.1f}%")
        m3.metric("Записей в выборке", len(df_curr))
        
        st.markdown("---")
        
        #График успеваемости по предметам
        subj_avg = df_curr.groupby("Предмет")["Итоговая_оценка"].mean().reset_index()
        fig = px.bar(subj_avg, x="Предмет", y="Итоговая_оценка", 
                     color="Итоговая_оценка", color_continuous_scale="RdYlGn", 
                     text_auto=".1f", title=f"Средний балл по дисциплинам: {g_select}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Данные по указанным фильтрам отсутствуют.")

#Анализ трендов
with tab_trends:
    st.subheader("📉 Выявление зон снижения качества обучения")
    
    
    gr_trends = df.groupby(['Факультет', 'Группа', 'Курс', year_col])['Итоговая_оценка'].mean().reset_index()
    gr_trends['BaseID'] = gr_trends['Группа'].apply(get_base_group)
    gr_trends = gr_trends.sort_values(['BaseID', year_col])
    
    #Сравнение с прошлым учебным годом
    gr_trends['Prev_Score'] = gr_trends.groupby('BaseID')['Итоговая_оценка'].shift(1)
    gr_trends['Динамика'] = gr_trends['Итоговая_оценка'] - gr_trends['Prev_Score']
    
    #Анализ последнего выбранного года
    latest_y = y_select
    drops = gr_trends[(gr_trends[year_col] == latest_y) & (gr_trends['Динамика'] < 0)].dropna()
    
    if not drops.empty:
        st.error(f"Выявлено снижение успеваемости в {len(drops)} группах в периоде {latest_y}")
        
        st.dataframe(
            drops[['Факультет', 'Группа', 'Курс', 'Итоговая_оценка', 'Динамика']]
            .sort_values('Динамика')
            .style.background_gradient(subset=['Динамика'], cmap='Reds_r'), 
            use_container_width=True
        )
        
        
        st.subheader("Образовательные траектории (динамика потоков)")
        fig_lines = px.line(gr_trends, x=year_col, y='Итоговая_оценка', color='BaseID', 
                            markers=True, title="Изменение успеваемости потоковых групп по годам")
        st.plotly_chart(fig_lines, use_container_width=True)
        
        
        worst = drops.sort_values('Динамика').iloc[0]
        st.warning(f"**Аналитический вывод:** Группа **{worst['Группа']}** ({worst['Факультет']}) демонстрирует наибольшее падение балла ({worst['Динамика']:.2f}). Требуется аудит учебного процесса.")
    else:
        st.success(f"В периоде {latest_y} критических падений успеваемости не зафиксировано.")

#Персональный анализ
with tab_student:
    st.subheader("👤 Персональный мониторинг студента")
    
    
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        st_y = st.selectbox("Год обучения", sorted(df[year_col].unique(), reverse=True), key="st_y")
    with sc2:
        st_f = st.selectbox("Направление ", sorted(df[df[year_col]==st_y]["Факультет"].unique()), key="st_f")
    with sc3:
        st_c = st.selectbox("Курс ", sorted(df[(df[year_col]==st_y) & (df["Факультет"]==st_f)]["Курс"].unique()), key="st_c")
    with sc4:
        st_g = st.selectbox("Группа ", sorted(df[(df[year_col]==st_y) & (df["Факультет"]==st_f) & (df["Курс"]==st_c)]["Группа"].unique()), key="st_g")
    
    #Список студентов только выбранной группы
    avail_students = sorted(df[(df[year_col]==st_y) & (df["Группа"]==st_g)]["Студент"].unique())
    selected_st = st.selectbox("Выберите студента из списка", avail_students)
    
    if selected_st:
        st_data = df[df["Студент"] == selected_st].sort_values(year_col)
        
        col_left, col_right = st.columns([1, 2])
        
        with col_left:
            st.write(f"**Все оценки за время обучения:**")
            st.dataframe(
                st_data[[year_col, "Курс", "Предмет", "Итоговая_оценка"]]
                .style.applymap(grade_color, subset=["Итоговая_оценка"]), 
                use_container_width=True
            )
        
        with col_right:
            #График прогресса конкретного студента
            st_avg = st_data.groupby(year_col)["Итоговая_оценка"].mean().reset_index()
            fig_st = px.line(st_avg, x=year_col, y="Итоговая_оценка", markers=True, 
                             title=f"Траектория успеваемости: {selected_st}")
            fig_st.update_yaxes(range=[0, 105])
            st.plotly_chart(fig_st, use_container_width=True)


st.markdown("---")
st.caption("Система разработана для анализа качества образования РГЭУ РИНХ 2026 г.")