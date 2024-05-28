import dash
from dash import html, dcc
import sqlite3
from dash.dependencies import Input, Output
from datetime import datetime

DATABASE_NAME = "mqtt_data.db"

def get_latest_values():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    latest_values = {}
    for table in ["ZeroW1", "ZeroW2", "ZeroW3", "ZeroW4"]:
        cursor.execute(f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            readable_timestamp = datetime.fromtimestamp(result[0]).strftime('%Y-%m-%d %H:%M:%S')
            latest_values[table] = {
                "timestamp": readable_timestamp,
                "key": result[1],
                "pm25": result[2],
                "temperature": result[3],
                "humidity": result[4],
                "wifi_strength": result[5],
            }
        else:
            latest_values[table] = {
                "timestamp": "No data",
                "key": None,
                "pm25": None,
                "temperature": None,
                "humidity": None,
                "wifi_strength": None,
            }
    conn.close()
    return latest_values

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Header("MQTT Sensor Dashboard", style={
        'textAlign': 'center', 
        'padding': '20px', 
        'backgroundColor': '#343a40', 
        'color': 'white', 
        'fontSize': '24px'
    }),
    html.Div(id='dashboard', style={
        'display': 'flex',
        'flexWrap': 'wrap',
        'justifyContent': 'center',
        'alignItems': 'center',
        'gap': '30px',
        'padding': '30px'
    }),
    dcc.Interval(
        id='interval-component',
        interval=60*1000,
        n_intervals=0
    ),
    html.Footer("MQTT Dashboard © 2024", style={
        'textAlign': 'center',
        'padding': '10px',
        'backgroundColor': '#343a40',
        'color': 'white',
        'marginTop': 'auto'
    })
], style={
    'fontFamily': 'Arial, sans-serif',
    'backgroundColor': '#f8f9fa',
    'margin': '0',
    'minHeight': '100vh',
    'display': 'flex',
    'flexDirection': 'column'
})

@app.callback(
    Output('dashboard', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    data = get_latest_values()
    cards = []
    for topic, values in data.items():
        card = html.Div([
            html.Div([
                html.H3(topic, style={
                    'textAlign': 'center',
                    'backgroundColor': '#007BFF',
                    'color': 'white',
                    'padding': '10px',
                    'borderRadius': '5px 5px 0 0'
                }),
                html.Div([
                    html.P(f"Timestamp: {values['timestamp']}", style={'margin': '5px 0'}),
                    html.P(f"PM2.5: {values['pm25']}", style={'margin': '5px 0'}),
                    html.P(f"Temperature: {values['temperature']} °F", style={'margin': '5px 0'}),
                    html.P(f"Humidity: {values['humidity']} %", style={'margin': '5px 0'}),
                    html.P(f"Wifi Strength: {values['wifi_strength']}", style={'margin': '5px 0'})
                ], style={
                    'padding': '20px', 
                    'backgroundColor': 'white', 
                    'borderRadius': '0 0 5px 5px'
                })
            ], style={
                'border': '1px solid #ccc',
                'borderRadius': '10px',
                'boxShadow': '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
                'transition': '0.3s',
                'backgroundColor': 'white'
            }),
        ], style={'width': '300px', 'margin': '20px'})
        cards.append(card)
    return cards

if __name__ == '__main__':
    app.run_server(debug=True)





