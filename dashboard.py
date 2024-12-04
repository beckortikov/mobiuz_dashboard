import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import gspread
from read_json import response_json

# Настройка страницы
st.set_page_config(layout="wide")

# Добавляем CSS стили
st.markdown("""
    <style>
        .metric-container {
            background-color: #f0f2f6;
            border-radius: 10px;
            padding: 15px;
            margin: 5px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        }
        .metric-label {
            color: #0f1b2a;
            font-size: 14px;
            font-weight: 500;
        }
        .metric-value {
            color: #1f77b4;
            font-size: 24px;
            font-weight: bold;
        }
        .branch-card {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }
        .branch-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        .branch-name {
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }
        .stats-container {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }
        .stat-item {
            text-align: center;
            flex: 1;
            padding: 0 10px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
        }
        .approved {
            color: #28a745;
        }
        .rejected {
            color: #dc3545;
        }
        .total {
            color: #17a2b8;
        }
        .approval-rate {
            color: #6f42c1;
        }
        .main-header {
            text-align: center;
            padding: 20px 0;
            margin-bottom: 30px;
            background: linear-gradient(90deg, #ff8c00, #ff4500);
            border-radius: 10px;
        }
        .main-header h1 {
            color: white;
            font-size: 32px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            margin: 0;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Определяем цветовую схему
COLOR_SCHEME = {
    "Одобрено": "#28a745",
    "Отказано": "#dc3545"
}

# Все остальные функции из предоставленного кода...
def get_scoring_data():
    """Получение данных из Google Sheets"""
    try:
        response_ = response_json()
        sa = gspread.service_account_from_dict(response_)

        sh = sa.open("MyTasks")
        worksheet = sh.worksheet("Scoring")

        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # Переименовываем столбцы для соответствия данным
        column_mapping = {
            'Менежер': 'Manager',
            'Филиал': 'Region',
            'Телефон номер': 'Phone',
            'Имя': 'Name',
            'Фамилия': 'Surname',
            'Возраст': 'Age',
            'Пол': 'Gender',
            'Сумма кредита': 'Amount',
            'Период': 'Duration',
            'Семейное положение': 'MaritalStatus',
            'Доход': 'Income',
            'Иждевенцы': 'Dependants',
            'Сфера занятости': 'OccupationBranch',
            'Роль': 'Occupation',
            'Стаж работы': 'ExpCat',
            'Результат': 'Result',
            'Вероятность возврата': 'Probability',
            'Дата': 'Date',
            'Номер документа': 'DocumentNumber'
        }
        df = df.rename(columns=column_mapping)

        # Преобразуем дату
        df['Date'] = pd.to_datetime(df['Date'])

        return df
    except Exception as e:
        st.error(f"Ошибка при загрузке данных: {str(e)}")
        return pd.DataFrame()

def get_status_metrics(data):
    """Расчет метрик по статусам"""
    total = len(data)
    approved = len(data[data['Result'] == 'Одобрено'])
    rejected = len(data[data['Result'] == 'Отказано'])
    approval_rate = (approved / total * 100) if total > 0 else 0

    return {
        'total': total,
        'approved': approved,
        'rejected': rejected,
        'approval_rate': approval_rate
    }

def create_status_pie_chart(data):
    """Создание круговой диаграммы"""
    status_counts = data['Result'].value_counts()
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Распределение статусов заявок",
        color_discrete_map=COLOR_SCHEME
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def create_bar_chart(data, x_column, title):
    """Создание столбчатой диаграммы"""
    status_data = pd.crosstab(data[x_column], data['Result'])
    fig = px.bar(
        status_data,
        barmode='group',
        title=title,
        color_discrete_map=COLOR_SCHEME
    )
    fig.update_layout(
        xaxis_title=x_column,
        yaxis_title="Количество заявок"
    )
    return fig

def create_time_series(data):
    """Создание графика временного ряда"""
    daily_status = data.groupby([data['Date'].dt.date, 'Result']).size().unstack(fill_value=0)
    fig = px.line(
        daily_status,
        title="Динамика заявок по дням",
        color_discrete_map=COLOR_SCHEME
    )
    fig.update_layout(
        xaxis_title="Дата",
        yaxis_title="Количество заявок"
    )
    return fig

def display_branch_cards(data, title):
    st.subheader(title)
    if len(data) == 0:
        st.info(f"Нет данных {title.lower()}")
        return

    for branch in data['Region'].unique():
        branch_data = data[data['Region'] == branch]
        metrics = get_status_metrics(branch_data)

        st.markdown(f"""
            <div class="branch-card">
                <div class="branch-name">{branch}</div>
                <div class="stats-container">
                    <div class="stat-item">
                        <div class="stat-value total">{metrics['total']}</div>
                        <div class="stat-label">ВСЕГО ЗАЯВОК</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value approved">{metrics['approved']}</div>
                        <div class="stat-label">ОДОБРЕНО</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value rejected">{metrics['rejected']}</div>
                        <div class="stat-label">ОТКАЗАНО</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value approval-rate">{metrics['approval_rate']:.1f}%</div>
                        <div class="stat-label">ПРОЦЕНТ ОДОБРЕНИЯ</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

def main():
    st.markdown('<div class="main-header"><h1>Дашборд скоринга MobiCenter</h1></div>', unsafe_allow_html=True)

    try:
        # Получаем данные
        df = get_scoring_data()

        if df.empty:
            st.error("Не удалось загрузить данные")
            return

        # Определяем временные периоды
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Создаем фильтры для разных периодов
        today_data = df[df['Date'].dt.date == today]
        yesterday_data = df[df['Date'].dt.date == yesterday]
        week_data = df[df['Date'].dt.date >= week_ago]
        month_data = df[df['Date'].dt.date >= month_ago]

        # Получаем метрики
        metrics_data = {
            "Сегодня": get_status_metrics(today_data),
            "Вчера": get_status_metrics(yesterday_data),
            "За неделю": get_status_metrics(week_data),
            "За месяц": get_status_metrics(month_data)
        }

        # Отображаем метрики в 4 колонках
        cols = st.columns(4)
        for col, (period, metrics) in zip(cols, metrics_data.items()):
            with col:
                st.markdown(f"""
                    <div class="metric-container">
                        <h3>{period}</h3>
                        <div class="metric-value">Всего: {metrics['total']}</div>
                        <div style="color: {COLOR_SCHEME['Одобрено']}">Одобрено: {metrics['approved']}</div>
                        <div style="color: {COLOR_SCHEME['Отказано']}">Отказано: {metrics['rejected']}</div>
                        <div class="metric-label">Процент одобрения: {metrics['approval_rate']:.1f}%</div>
                    </div>
                """, unsafe_allow_html=True)

        # Графики
        st.markdown("<hr>", unsafe_allow_html=True)

        # Добавляем селектор периода
        col_period_selector, _ = st.columns([1, 3])
        with col_period_selector:
            period = st.radio(
                "Период статистики:",
                ["За месяц", "За неделю"],
                horizontal=True,
                key="period_selector"
            )

        selected_data = month_data if period == "За месяц" else week_data
        period_suffix = "за месяц" if period == "За месяц" else "за неделю"

        col_left, col_right = st.columns(2)

        with col_left:
            st.plotly_chart(create_status_pie_chart(selected_data), use_container_width=True)
            st.plotly_chart(create_bar_chart(selected_data, 'Manager',
                                           f"Статистика по менеджерам {period_suffix}"), use_container_width=True)

        with col_right:
            st.plotly_chart(create_bar_chart(selected_data, 'Region',
                                           f"Статистика по филиалам {period_suffix}"), use_container_width=True)
            st.plotly_chart(create_time_series(selected_data), use_container_width=True)

        # Добавляем детальную статистику по филиалам за сегодня и вчера
        st.markdown("<hr>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            display_branch_cards(today_data, "Статистика по филиалам за сегодня")

        with col2:
            display_branch_cards(yesterday_data, "Статистика по филиалам за вчера")

        # Добавляем сравнительный анализ
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("Сравнение с предыдущим днем")

        for branch in set(today_data['Region'].unique()) | set(yesterday_data['Region'].unique()):
            today_metrics = get_status_metrics(today_data[today_data['Region'] == branch])
            yesterday_metrics = get_status_metrics(yesterday_data[yesterday_data['Region'] == branch])

            change = today_metrics['total'] - yesterday_metrics['total']
            change_color = 'green' if change > 0 else 'red' if change < 0 else '#666'
            change_symbol = '↑' if change > 0 else '↓' if change < 0 else '='

            st.markdown(f"""
                <div class="branch-card">
                    <div class="branch-name">{branch}</div>
                    <div class="stats-container">
                        <div class="stat-item">
                            <div class="stat-value total">{today_metrics['total']}</div>
                            <div class="stat-label">СЕГОДНЯ (ВСЕГО)</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value total">{yesterday_metrics['total']}</div>
                            <div class="stat-label">ВЧЕРА (ВСЕГО)</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value" style="color: {change_color}">{change_symbol} {abs(change)}</div>
                            <div class="stat-label">ИЗМЕНЕНИЕ</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value approval-rate">{today_metrics['approval_rate']:.1f}%</div>
                            <div class="stat-label">СЕГОДНЯ (% ОДОБРЕНИЯ)</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value approval-rate">{yesterday_metrics['approval_rate']:.1f}%</div>
                            <div class="stat-label">ВЧЕРА (% ОДОБРЕНИЯ)</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Произошла ошибка при загрузке данных: {str(e)}")
        st.error("Пожалуйста, проверьте подключение к Google Sheets и формат данных.")

if __name__ == "__main__":
    main()