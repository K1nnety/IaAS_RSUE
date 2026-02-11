import streamlit as st
import pandas as pd
import plotly.express as px
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
    if not isinstance(val, (int, float)):
        return ""
    if val >= 85:
        return "color: #2ecc71; font-weight: bold"
    if val >= 70:
        return "color: #f39c12; font-weight: bold"
    return "color: #e74c3c; font-weight: bold"


def get_flow_id(row):
    """
    Уникальный ID образовательной траектории:
    направление + номер группы + год поступления
    """
    dir_code = row["Группа"].split("-")[0]
    group_num = row["Группа"][-1]
    start_year = int(row["Учебный_год"][:4]) - (row["Курс"] - 1)
    return f"{dir_code}-{group_num}-{start_year}"


#Генерация пустого шаблона в памяти
def generate_empty_template():
    cols = [
        "Направление",
        "Учебный_год",
        "Курс",
        "Группа",
        "Студент",
        "Предмет",
        "Итоговая_оценка",
    ]
    df_empty = pd.DataFrame(columns=cols)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_empty.to_excel(writer, index=False)
    output.seek(0)
    return output


#Интерфейс
st.title("📊 ИАС обеспечения качества образования в учебных подразделениях РГЭУ РИНХ")
st.markdown("---")

uploaded_file = st.sidebar.file_uploader("📥 Загрузите файл Excel (.xlsx)", type=["xlsx"])

#Заполненный шаблон
if st.sidebar.button("✨ Сгенерировать пример данных", type="primary"):
    generate_university_data("university_grades.xlsx") #Создание в папке проекта
    with open("university_grades.xlsx", "rb") as f:
        st.sidebar.download_button(
            "⬇️ Скачать university_grades.xlsx",
            data=f.read(),
            file_name="university_grades.xlsx",
        )

#Генерация пустого шаблона
st.sidebar.markdown("---")
st.sidebar.caption("Для преподавателей")

if st.sidebar.button("📋 Создать пустой шаблон"):
    st.sidebar.download_button(
        "⬇️ Скачать template.xlsx",
        data=generate_empty_template(),
        file_name="template.xlsx",
    )


if not uploaded_file:
    st.info("👋 Загрузите Excel-файл для начала анализа")
    st.stop()



df = pd.read_excel(uploaded_file)
df.columns = df.columns.str.strip()
year_col = "Учебный_год"

df["FlowID"] = df.apply(get_flow_id, axis=1)


#Вкладки
tab_data, tab_dash, tab_trends, tab_student = st.tabs(
    [
        "📁 Исходные данные",
        "📈 Мониторинг успеваемости",
        "📉 Анализ трендов и падений",
        "👤 Анализ по студенту",
    ]
)


#Просмотр исходных данных
with tab_data:
    st.dataframe(df, use_container_width=True, height=500)



#Мониторинг успевемости
with tab_dash:
    st.subheader("Текущие показатели подразделений")
    
    #Фильтры
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        y_select = st.selectbox("Учебный год", sorted(df[year_col].unique(), reverse=True), key="dash_y")
    with c2:
        f_select = st.selectbox("Направление", sorted(df[df[year_col]==y_select]["Направление"].unique()), key="dash_f")
    with c3:
        c_select = st.selectbox("Курс", sorted(df[(df[year_col]==y_select) & (df["Направление"]==f_select)]["Курс"].unique()), key="dash_c")
    with c4:
        # Фильтр по группам
        avail_gr = sorted(df[(df[year_col]==y_select) & (df["Направление"]==f_select) & (df["Курс"]==c_select)]["Группа"].unique())
        g_select = st.selectbox("Группа", ["Все группы"] + avail_gr, key="dash_g")
    
    
    mask = (df[year_col] == y_select) & (df["Направление"] == f_select) & (df["Курс"] == c_select)
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
    st.subheader("📉 Анализ трендов и падений")

    fc1, fc2 = st.columns(2)

    with fc1:
        tr_year = st.selectbox(
            "Учебный год",
            sorted(df[year_col].unique(), reverse=True),
            key="tr_year",
        )
    with fc2:
        tr_dir = st.selectbox(
            "Направление",
            sorted(df[df[year_col] == tr_year]["Направление"].unique()),
            key="tr_dir",
        )
    tr_course = None
    tr_group = "Все группы"

    
    trend = (
        df[df["Направление"] == tr_dir]
        .groupby(["FlowID", "Группа", "Курс", year_col])["Итоговая_оценка"]
        .mean()
        .reset_index()
        .sort_values(["FlowID", "Курс"])
    )

    
    trend = trend[
        trend[year_col].str[:4].astype(int) <= int(tr_year[:4])
    ]

    
    trend["Prev"] = trend.groupby("FlowID")["Итоговая_оценка"].shift(1)
    trend["Δ"] = trend["Итоговая_оценка"] - trend["Prev"]

    #таблица падений
    drops = trend[
        (trend[year_col] == tr_year) & (trend["Δ"] < 0)
    ]

    st.subheader("Выявление зон снижения качества обучения")
    st.dataframe(
        drops[["Группа", "Курс", "Итоговая_оценка", "Δ"]]
        .sort_values("Δ")
        .style.background_gradient(subset=["Δ"], cmap="Reds_r"),
        use_container_width=True,
    )

    
    plot_df = trend.copy()

    if tr_group != "Все группы":
        fid = plot_df[plot_df["Группа"] == tr_group]["FlowID"].iloc[0]
        plot_df = plot_df[plot_df["FlowID"] == fid]

    
    last_names = (
        plot_df.sort_values("Курс")
        .groupby("FlowID")["Группа"]
        .last()
        .to_dict()
    )
    plot_df["Наименование группы"] = plot_df["FlowID"].map(last_names)

    st.subheader("Образовательные траектории (динамика групп)")
    fig = px.line(
        plot_df,
        x="Курс",
        y="Итоговая_оценка",
        color="Наименование группы",
        markers=True,
    )
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(range=[60, 100])
    st.plotly_chart(fig, use_container_width=True)

#Персональный анализ
with tab_student:
    st.subheader("👤 Персональный мониторинг студента")

    
    #Фильтры выбора
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        selected_year = st.selectbox(
            "Учебный год",
            options=sorted(df[year_col].unique(), reverse=True),
            key="student_year"
        )

    with col2:
        available_directions = df[df[year_col] == selected_year]["Направление"].unique()
        selected_direction = st.selectbox(
            "Направление",
            options=sorted(available_directions),
            key="student_direction"
        )

    with col3:
        available_courses = df[
            (df[year_col] == selected_year) &
            (df["Направление"] == selected_direction)
        ]["Курс"].unique()
        selected_course = st.selectbox(
            "Курс",
            options=sorted(available_courses),
            key="student_course"
        )

    with col4:
        available_groups = df[
            (df[year_col] == selected_year) &
            (df["Направление"] == selected_direction) &
            (df["Курс"] == selected_course)
        ]["Группа"].unique()
        selected_group = st.selectbox(
            "Группа",
            options=sorted(available_groups),
            key="student_group"
        )

    
    #Выбор студента
    student_mask = (
        (df[year_col] == selected_year) &
        (df["Группа"] == selected_group)
    )
    available_students = sorted(df[student_mask]["Студент"].unique())

    if len(available_students) == 0:
        st.warning("В выбранной группе нет студентов за указанный год.")
    else:
        selected_student = st.selectbox(
            "Выберите студента",
            options=available_students,
            index=0
        )

        if selected_student:
            #Данные по выбранному студенту за всё время обучения
            student_data = df[df["Студент"] == selected_student].sort_values(year_col)

            
            col_left, col_right = st.columns([1, 2])

            with col_left:
                st.markdown(f"**Оценки студента {selected_student} за всё время обучения**")
                st.dataframe(
                    student_data[[year_col, "Курс", "Предмет", "Итоговая_оценка"]]
                    .style.applymap(grade_color, subset=["Итоговая_оценка"])
                    .format({"Итоговая_оценка": "{:.0f}"}),
                    use_container_width=True,
                    hide_index=True
                )

            with col_right:
                #Средний балл по годам
                yearly_avg = (
                    student_data.groupby(year_col, as_index=False)
                    ["Итоговая_оценка"]
                    .mean()
                )

                fig = px.line(
                    yearly_avg,
                    x=year_col,
                    y="Итоговая_оценка",
                    markers=True,
                    text="Итоговая_оценка",
                    title=f"Траектория успеваемости — {selected_student}",
                )

                fig.update_traces(
                    textposition="top center",
                    marker=dict(size=10),
                    line=dict(width=2.5)
                )
                fig.update_yaxes(
                    range=[0, 105],
                    title="Средний балл",
                    dtick=10
                )
                fig.update_xaxes(title="Учебный год")

                st.plotly_chart(fig, use_container_width=True)

    
    st.markdown("---")
    st.caption("Система разработана для анализа качества образования РГЭУ РИНХ 2026 г.")
