import dash
from dash import html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# Expose the server variable for gunicorn
server = app.server

# ---------------- DATA ----------------
# Load data using relative paths for deployment
df_m12 = pd.read_csv("Load In Line12.csv", on_bad_lines='skip')
df_alarm = pd.read_csv("Logging_M12 Alarm.csv", on_bad_lines='skip')

# Data Processing (same as before)
df_m12["DATE"] = pd.to_datetime(df_m12["DATE"], dayfirst=True, errors="coerce")
df_m12 = df_m12.dropna(subset=["DATE"])
df_m12["PROGRAM NAME"] = df_m12["PROGRAM NAME"].astype(str).str.strip()
df_m12["MODE"] = df_m12["MODE"].astype(str).str.strip()
df_m12["PROGRAM NAME"] = df_m12["PROGRAM NAME"].replace("BUA1801A-18O2A", "BUA1801A-1802A")

# Time Features
month_order = [f"{i:02d}. {m}" for i, m in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], 1)]
weekday_order = [f"{i}. {d}" for i, d in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], 1)]

df_m12["Year"] = df_m12["DATE"].dt.year
df_m12["Month"] = pd.Categorical(df_m12["DATE"].dt.strftime("%m. %b"), categories=month_order, ordered=True)
df_m12["Week"] = df_m12["DATE"].dt.day.apply(lambda x: f"W{(x - 1)//7 + 1}")
df_m12["Day"] = df_m12["DATE"].dt.day
df_m12["Weekday"] = pd.Categorical(df_m12["DATE"].dt.strftime("%a"), categories=[d.split(". ")[1] for d in weekday_order], ordered=True)
df_m12["Weekday_Label"] = df_m12["Weekday"].cat.codes + 1
df_m12["Weekday"] = df_m12["Weekday_Label"].astype(str) + ". " + df_m12["DATE"].dt.strftime("%a")
df_m12["YYYYMM"] = df_m12["DATE"].dt.strftime("%Y%m")
df_m12["Weekday_Combo"] = df_m12["Weekday"]

# Alarm Data Processing
df_alarm["DATE"] = pd.to_datetime(df_alarm["DATE"], dayfirst=True, errors="coerce")
df_alarm = df_alarm.dropna(subset=["DATE", "DURATION(min)", "FAULT_CODE"])

df_alarm["Year"] = df_alarm["DATE"].dt.year
df_alarm["Month"] = pd.Categorical(df_alarm["DATE"].dt.strftime("%m. %b"), categories=month_order, ordered=True)
df_alarm["Week"] = df_alarm["DATE"].dt.day.apply(lambda x: f"W{(x - 1)//7 + 1}")
df_alarm["Day"] = df_alarm["DATE"].dt.day
df_alarm["Weekday"] = pd.Categorical(df_alarm["DATE"].dt.strftime("%a"), categories=[d.split(". ")[1] for d in weekday_order], ordered=True)
df_alarm["Weekday_Label"] = df_alarm["Weekday"].cat.codes + 1
df_alarm["Weekday"] = df_alarm["Weekday_Label"].astype(str) + ". " + df_alarm["DATE"].dt.strftime("%a")


# ---------------- CSS ----------------
app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>SMT Smart Data System</title>
    {%favicon%}
    {%css%}
    <style>
        body { background-color: #2e2e2e; color: white; font-family: Arial; }
        .layout-container { display: flex; flex-direction: column; gap: 15px; }
        .layout-row { display: flex; align-items: center; gap: 10px; }
        .row-label { width: 50px; color: #00BFFF; font-weight: bold; text-align: right; margin-right: 10px; }
        .grid-row { display: grid; grid-template-columns: repeat(6, 80px); gap: 10px; }
        .cell { text-align: center; }
        .btn-grid { width: 80px; height: 40px; font-weight: bold; }
        .blinking-text {
            animation: blink 2s infinite;
            color: #0033CC;
            font-weight: bold;
            font-size: 28px;
            text-align: center;
        }
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .top-buttons {
            display: flex; justify-content: space-between; margin-bottom: 10px;
        }
        .dash-dropdown div[class*="control"],
        .dash-dropdown div[class*="menu"],
        .dash-dropdown div[class*="singleValue"],
        .dash-dropdown div[class*="placeholder"] {
            color: #00008B !important; /* Dark blue text color for dropdown options */
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
'''

# ---------------- Page Layout (same as before) ----------------

# หน้า 1: Layout Mounter
mounter_layout = {
    "12B": ["M11", "M12", "M24", "M16", "M13", "M17"],
    "21B": ["M1", "M2", "M23", "M18", "M05", "M03"],
    "22B": ["M10", "M9", "M8", "M7", "M6", "M4"],
    "43A": ["M22", "M21", "M20", "M15", "M14", "M19"],
}
layout_rows = []
for label, machines in mounter_layout.items():
    layout_rows.append(
        html.Div([
            html.Div(label, className="row-label"),
            html.Div([
                html.Div(dbc.Button(m, id=m, color="primary", className="btn-grid", href=f"/{m}"), className="cell")
                for m in machines
            ], className="grid-row")
        ], className="layout-row")
    )

index_page = html.Div([
    html.H2("SMT Smart Data System", style={"color": "#00BFFF", "marginBottom": "20px"}),
    html.H5("Summarize Layout By Mounter no.", style={"color": "#FF1493", "marginBottom": "30px"}),
    html.Div(layout_rows, className="layout-container")
], style={"padding": "50px"})

# หน้า 2: Dashboard Insert / Pass
m12_dashboard_layout = html.Div([
    html.Div(className="top-buttons", children=[
        html.A("🏠 Home", href="/", style={"fontWeight": "bold", "fontSize": "20px", "color": "white"}),
        html.Div("Mounter LoadIN #12 Insert / Pass Mode Dashboard", className="blinking-text"),
        html.A("📊 OEE", href="/M12/oee", style={"fontWeight": "bold", "fontSize": "20px", "color": "white"})
    ]),
    html.Div([
        dcc.Dropdown(sorted(df_m12["Year"].dropna().unique()), id="year", multi=True, placeholder="เลือกปี", className="dash-dropdown"),
        dcc.Dropdown(month_order, id="month", multi=True, placeholder="เลือกเดือน", className="dash-dropdown"),
        dcc.Dropdown(sorted(df_m12["Week"].dropna().unique()), id="week", multi=True, placeholder="เลือกสัปดาห์", className="dash-dropdown"),
        dcc.Dropdown(weekday_order, id="weekday", multi=True, placeholder="เลือกวันในสัปดาห์", className="dash-dropdown"),
        dcc.Dropdown(sorted(df_m12["Day"].dropna().unique()), id="day", multi=True, placeholder="เลือกวันที่", className="dash-dropdown"),
        dcc.Dropdown(sorted(df_m12["PROGRAM NAME"].dropna().unique()), id="model", multi=True, placeholder="เลือก MODEL", className="dash-dropdown"),
    ], style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "10px", "marginBottom": "20px"}),
    html.Div([
        dcc.Graph(id="bar_horizontal"),
        dcc.Graph(id="bar_month"),
        dcc.Graph(id="bar_weekday"),
        dcc.Graph(id="bar_weekday_ym"),
        dcc.Graph(id="pie_chart"),
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px"}),
    html.H4("📊 Summary Table", style={"marginTop": "30px", "color": "#00BFFF"}),
    dash_table.DataTable(id="summary_table", page_size=20, style_table={"overflowX": "auto"},
                         style_header={"backgroundColor": "#333", "color": "white", "fontWeight": "bold"},
                         style_data={"backgroundColor": "#444", "color": "white"},
                         style_cell={"textAlign": "left", "padding": "10px"})
], style={"padding": "20px"})

# หน้า 3: Dashboard OEE
m12_oee_dashboard_layout = html.Div([
    html.Div(className="top-buttons", children=[
        html.A("🏠 Home", href="/", style={"fontWeight": "bold", "fontSize": "20px", "color": "white"}),
        html.Div("M12 OEE Dashboard", className="blinking-text"),
        html.A("⬅️ Dashboard", href="/M12", style={"fontWeight": "bold", "fontSize": "20px", "color": "white"})
    ]),
    html.Div([
        dcc.Graph(id="mttr_daily"),
        dcc.Graph(id="mttr_weekly"),
        dcc.Graph(id="mttr_monthly"),
        dcc.Graph(id="mttr_yearly"),
        dcc.Graph(id="pie_fault"),
    ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"})
])

# ---------------- App Layout ----------------
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# ---------------- Routing (same as before) ----------------
@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def render_page(pathname):
    if pathname == "/M12": return m12_dashboard_layout
    elif pathname == "/M12/oee": return m12_oee_dashboard_layout
    else: return index_page

# ---------------- Callbacks (same as before) ----------------
@app.callback(
    Output("bar_horizontal", "figure"),
    Output("bar_month", "figure"),
    Output("bar_weekday", "figure"),
    Output("bar_weekday_ym", "figure"),
    Output("pie_chart", "figure"),
    Output("summary_table", "data"),
    Output("summary_table", "columns"),
    Input("year", "value"),
    Input("month", "value"),
    Input("week", "value"),
    Input("weekday", "value"),
    Input("day", "value"),
    Input("model", "value")
)
def update_m12_dashboard_graphs(year, month, week, weekday, day, model):
    dff = df_m12.copy()
    if year: dff = dff[dff["Year"].isin(year)]
    if month: dff = dff[dff["Month"].isin(month)]
    if week: dff = dff[dff["Week"].isin(week)]
    if weekday: dff = dff[dff["Weekday"].isin(weekday)]
    if day: dff = dff[dff["Day"].isin(day)]
    if model: dff = dff[dff["PROGRAM NAME"].isin(model)]

    bar = dff.groupby(["PROGRAM NAME", "MODE"]).size().unstack(fill_value=0).reset_index()
    bar.columns = bar.columns.str.strip()
    bar = bar.rename(columns={col: col for col in bar.columns if col in ["INSERT", "PASS MODE"]})
    bar["TOTAL"] = bar.get("INSERT", 0) + bar.get("PASS MODE", 0)
    bar = bar.sort_values("TOTAL", ascending=False)

    fig1 = go.Figure()
    fig1.add_bar(y=bar["PROGRAM NAME"], x=bar.get("INSERT", [0]*len(bar)), name="INSERT", orientation="h", marker_color="#CCFF00", text=bar.get("INSERT", [0]*len(bar)), textposition="auto")
    fig1.add_bar(y=bar["PROGRAM NAME"], x=bar.get("PASS MODE", [0]*len(bar)), name="PASS MODE", orientation="h", marker_color="#FFA500", text=bar.get("PASS MODE", [0]*len(bar)), textposition="auto")
    fig1.update_layout(barmode="stack", title="Insert vs Pass by Model", template="plotly_dark")

    m = dff.groupby(["Month", "MODE"]).size().reset_index(name="count")
    fig2 = px.bar(m, x="Month", y="count", color="MODE", text="count", color_discrete_map={"INSERT": "#CCFF00", "PASS MODE": "#FFA500"}, title="Monthly Count", template="plotly_dark")
    fig2.update_traces(textposition="outside")

    w = dff.groupby(["Weekday", "MODE"]).size().reset_index(name="count")
    w["Weekday"] = pd.Categorical(w["Weekday"], categories=weekday_order, ordered=True)
    w = w.sort_values("Weekday")
    fig3 = px.bar(w, x="Weekday", y="count", color="MODE", text="count", color_discrete_map={"INSERT": "#CCFF00", "PASS MODE": "#FFA500"}, title="Weekday Count", template="plotly_dark")
    fig3.update_traces(textposition="outside")

    wm = dff.groupby(["Weekday_Combo", "YYYYMM"]).size().reset_index(name="count")
    wm["Weekday_Combo"] = pd.Categorical(wm["Weekday_Combo"], categories=weekday_order, ordered=True)
    wm = wm.sort_values(["Weekday_Combo", "YYYYMM"])
    fig4 = px.bar(wm, x="Weekday_Combo", y="count", color="YYYYMM", barmode="group", text="count", title="Compare Weekday by Month", template="plotly_dark")
    fig4.update_traces(textposition="outside")

    pie = dff["MODE"].value_counts().reset_index()
    pie.columns = ["MODE", "count"]
    fig5 = px.pie(pie, values="count", names="MODE", color="MODE", color_discrete_map={"INSERT": "#CCFF00", "PASS MODE": "#FFA500"}, title="MODE Distribution", template="plotly_dark")

    t = dff.groupby(["PROGRAM NAME", "MODE"]).size().unstack(fill_value=0).reset_index()
    t.columns = t.columns.str.strip()
    t = t.rename(columns={col: col for col in t.columns if col in ["INSERT", "PASS MODE"]})
    t = t.rename(columns={"INSERT": "INSERT COUNT", "PASS MODE": "PASS MODE COUNT"})
    t["TOTAL"] = t.get("INSERT COUNT", 0) + t.get("PASS MODE COUNT", 0)
    t = t.sort_values("TOTAL", ascending=False)

    return fig1, fig2, fig3, fig4, fig5, t.to_dict("records"), [{"name": i, "id": i} for i in t.columns]


@app.callback(
    Output("mttr_daily", "figure"),
    Output("mttr_weekly", "figure"),
    Output("mttr_monthly", "figure"),
    Output("mttr_yearly", "figure"),
    Output("pie_fault", "figure"),
    Input("url", "pathname")
)
def update_oee_dashboard_graphs(pathname):
    if pathname != "/M12/oee":
        return {}, {}, {}, {}, {}

    df_group = df_alarm.copy()

    daily = df_group.groupby("Day")["DURATION(min)"].mean().reset_index()
    fig1 = px.bar(daily, x="Day", y="DURATION(min)", title="MTTR by Day", text="DURATION(min)", template="plotly_dark")
    fig1.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig1.update_layout(yaxis_title="Duration (min)")

    weekly = df_group.groupby("Week")["DURATION(min)"].mean().reset_index()
    fig2 = px.bar(weekly, x="Week", y="DURATION(min)", title="MTTR by Week", text="DURATION(min)", template="plotly_dark")
    fig2.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig2.update_layout(yaxis_title="Duration (min)")

    monthly = df_group.groupby("Month")["DURATION(min)"].mean().reset_index()
    fig3 = px.bar(monthly, x="Month", y="DURATION(min)", title="MTTR by Month", text="DURATION(min)", template="plotly_dark")
    fig3.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig3.update_layout(yaxis_title="Duration (min)")

    yearly = df_group.groupby("Year")["DURATION(min)"].mean().reset_index()
    fig4 = px.bar(yearly, x="Year", y="DURATION(min)", title="MTTR by Year", text="DURATION(min)", template="plotly_dark")
    fig4.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig4.update_layout(yaxis_title="Duration (min)")

    pie = df_group["FAULT_CODE"].value_counts().reset_index()
    pie.columns = ["FAULT_CODE", "count"]
    fig5 = px.pie(pie, values="count", names="FAULT_CODE", title="Fault Code Distribution", template="plotly_dark")

    return fig1, fig2, fig3, fig4, fig5

# No app.run() block needed for deployment with gunicorn
