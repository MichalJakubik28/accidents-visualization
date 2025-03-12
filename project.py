import geopandas as gpd
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, State, dash_table, callback_context
import textwrap

print(f"Data preprocessing (may take a few seconds)")

file_path = 'assets/nehody.csv'
accidents = pd.read_csv(file_path)
acc = pd.read_csv(file_path)
accidents = accidents[["zuj", "alkohol_vinik", "hlavni_pricina", "nasledky", "pricina", "pneumatiky", "pohlavi", "alkohol", "den_v_tydnu", "mesic_t", "alkohol_chodec", "nasledek", "smrt", "usmrceno_os", "mesic", "x", "y", "rok", "den", "hmotna_skoda"]]
accidents["reason"] = accidents["hlavni_pricina"] + " - " + accidents["pricina"]

map_json = gpd.read_file("assets/brno_casti.geojson")

years = accidents["rok"].unique()
districts = accidents["zuj"].unique()
reasons = accidents["reason"].unique()
months = [i for i in range(1, 13)]
day = [i for i in range(1, 8)]

# Create a DataFrame with all possible combinations of years and districts
all_combinations = pd.MultiIndex.from_product([districts, years, reasons, months, day], names=["zuj", "rok", "reason", "mesic", "den"])
all_combinations_df = pd.DataFrame(index=all_combinations).reset_index()

# Group by year and district to count accidents
accident_counts = accidents.groupby(["zuj", "rok", "reason", "mesic", "den"]).size().reset_index(name="accident_count")

# Merge the complete set of combinations with the grouped counts
accidents_all = all_combinations_df.merge(accident_counts, on=["zuj", "rok", "reason", "mesic", "den"], how="left")

accidents_yearly = accidents_all.groupby(["zuj", "rok", "reason"], as_index=False)["accident_count"].sum()

# Fill missing accident counts with 0
accidents_yearly["accident_count"] = accidents_yearly["accident_count"].fillna(0).astype(int)

accidents_yearly = accidents_yearly.sort_values(by="rok", ascending=True)

accidents_monthly = accidents_all.groupby(["zuj", "reason", "rok", "mesic"], as_index=False)["accident_count"].sum()

accidents_daily = accidents_all.groupby(["zuj", "reason", "rok", "den"], as_index=False)["accident_count"].sum()

damages = acc[["zuj", "hmotna_skoda"]]
damages = damages.groupby(["zuj"], as_index=False)["hmotna_skoda"].mean()
damages["hmotna_skoda"] = damages["hmotna_skoda"].astype(int)

deaths = acc[["zuj", "usmrceno_os"]]
deaths = deaths.groupby(["zuj"], as_index=False)["usmrceno_os"].sum()


## Dash page ##

app = Dash(__name__)

#*******APP LAYOUT**************

app.layout = html.Div(
    style={'backgroundColor':'#323130',
        'height': '100%',
        'color': 'white',
        'margin': 0,
        'padding': '15px',
        'padding-left': '50px'
    },     
    
    children=[
        #****************************HEADER*************************************
        html.H1(children='Dopravní nehody v Brně', style={"font-family": "Helvetica"}),

        # dcc.Markdown('### Vizualizace dopravních nehod v městských částech Brna', style={"font-family": "Helvetica"}),
    
        html.Hr(),
    
        #****************************Map*************************************   
        
        html.Div(
            dcc.Graph(id='map'), 
            style={'width': '40%', 'display': 'inline-block'}
        ),

        html.Div(style={'width' : '10%', 'display' : 'inline-block'}),
    
        #****************************Timeline*************************************   
        
        html.Div(
            [dcc.Graph(id='timeline')], 
            style={'width': '50%', 'display': 'inline-block'}),
        
        html.Div([
            html.Button('Městská část - zrušit filtr', id='district-button', n_clicks=0, style={
                "background-color": "#6200EE",  # Primary Material color
                "color": "white",
                "border": "none",
                "padding": "12px 24px",
                "font-size": "16px",
                "font-weight": "500",
                "letter-spacing": "1px",
                "border-radius": "4px",
                "outline": "none",
                
            }),
            ],
            style={'width': '40%', 'display': 'inline-block', "font-family": "Helvetica", 'text-align': 'right'}
        ),

        html.Div(style={'width' : '53%', 'display' : 'inline-block'}),

        html.Div(children=[
            'Granularita:', 
            dcc.RadioItems(['Měsíce', 'Dny'], #options
                           'Měsíce', #
                           id='granularity',
                           inline=False, style={"font-weight": "normal"})],
            style={'width': '7%', 'display': 'inline-block', 'text-align': 'left', "font-family": "Helvetica", "font-weight": "bold"},
        ),

        html.H2('Nejčastější příčiny nehod', style={"font-family": "Helvetica", "margin-top": "40px"}),
        html.Div(
            [dcc.Graph(id='reasons')], 
            style={'width': '100%', 'display': 'inline-block'}),
    
        html.Div([
            html.Button('Příčina - zrušit filtr', id='reason-button', n_clicks=0, style={
                "background-color": "#6200EE",  # Primary Material color
                "color": "white",
                "border": "none",
                "padding": "12px 24px",
                "font-size": "16px",
                "font-weight": "500",
                "letter-spacing": "1px",
                "border-radius": "4px",
                "outline": "none",
            }),
            ],
            style={'width': '100%', 'display': 'inline-block', "margin-top": "0", "margin-bottom": "0px", 'text-align': 'right'}
        ),
    
        #****************************Slider*************************************   
        html.H2('Rok', style={"font-family": "Helvetica"}),
        html.Div([
            dcc.Slider(2010, 2023, step = 1, id='slider',
                    marks={i: f"{i}" for i in range(2010,2024,1)},
                    tooltip={'placement': 'bottom', 'always_visible': True})
            ], 
            style={'width': '100%', 'display': 'inline-block', "font-size": "20px"}),

        html.Div([
            html.Button('Rok - zrušit filtr', id='year-button', n_clicks=0, style={
                    "background-color": "#6200EE",  # Primary Material color
                    "color": "white",
                    "border": "none",
                    "padding": "12px 24px",
                    "font-size": "16px",
                    "font-weight": "500",
                    "letter-spacing": "1px",
                    "border-radius": "4px",
                    "outline": "none"
                })], style={
                    "margin-top": "30px",
                    'margin-bottom': "10px",
                    'text-align': 'right'
                })
    ],
 )


#**************FUNCTIONS*****************************

def get_map(year, reason):
    if year:
        stats_map = accidents_yearly[accidents_yearly["rok"] == year]
    else:
        stats_map = accidents_yearly.groupby(["zuj", "reason"], as_index=False)["accident_count"].sum()
    
    if reason:
        stats_map = stats_map[stats_map["reason"] == reason.replace("<br>", " ")]
    else:
        stats_map = stats_map.groupby("zuj", as_index=False)["accident_count"].sum()
    
    stats_map['skoda'] = damages['hmotna_skoda']
    stats_map['smrt'] = deaths["usmrceno_os"]

    if not stats_map.empty:
        range_max = int(stats_map.nlargest(2, 'accident_count').iloc[1]['accident_count'])
        fig=px.choropleth(stats_map, #data
                    geojson=map_json,
                    featureidkey='properties.nazev', #property in geojson
                    locations='zuj',#column in dataframe matching featureidkey
                    color= 'accident_count',  #dataframe
                    hover_data=['accident_count'],
                    range_color=(0, range_max), 
                    color_continuous_scale='Viridis',
                    projection='mercator', 
                    title='',
                    custom_data=['skoda', 'smrt'],
                    labels={'accident_count':'Počet nehod'}
        )
    
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0},
                          geo_bgcolor="#323130",
                          plot_bgcolor= "#323130",
                          paper_bgcolor= "#323130",
                          font_color="white",
        )
        fig.update_geos(fitbounds="locations", visible=False)

        fig.update_traces(
            hovertemplate="<b>Městská část:</b> %{location}<br>" + 
                        "<b>Počet nehod:</b> %{z}<br>" +  
                        "<b>Průměrná škoda:</b> %{customdata[0]} Kč<br>" +  
                        "<b>Usmrceno osob:</b> %{customdata[1]}<br>" +  
                        "<extra></extra>",  # Removes extra hover box info
        )
        return fig


def get_district_graph(district, year, reason, granularity):
    if granularity == "Měsíce":
        accidents = accidents_monthly
        accidents["granularity"] = accidents["mesic"]
    else:
        accidents = accidents_daily
        accidents["granularity"] = accidents["den"]

    if year:
        accidents = accidents[accidents['rok'] == year]
    else:
        accidents = accidents.groupby(["zuj", "reason", "granularity"], as_index=False)["accident_count"].sum()

    if reason:
        accidents = accidents[accidents["reason"] == reason.replace("<br>", " ")]
    else:
        accidents = accidents.groupby(["zuj", "granularity"], as_index=False)["accident_count"].sum()
    
    if district:
        accidents = accidents[accidents["zuj"] == district]
    else:
        accidents = accidents.groupby(["granularity"], as_index=False)["accident_count"].sum()
        district = "všechny městské části"
            
    bars = px.line(accidents,
                    x="granularity",
                    y=["accident_count"],
                    title="Časová os: " + district,
                    )
    bars.update_layout(plot_bgcolor= "#323130",
                       paper_bgcolor= "#323130",
                       font_color="white",
                       showlegend=False,
                       xaxis_title="Měsíc" if granularity == "Měsíce" else "Den v týdnu",
                       yaxis_title="Počet nehod",
                       xaxis_title_font={"size": 20},  # Change font size of x-axis label
                       yaxis_title_font={"size": 20},   # Change font size of y-axis label
                       xaxis=dict(
                           tickfont=dict(size=15),  # Change font size of x-axis tick labels
                           ticklabelstandoff=10
                       ),
                       yaxis=dict(
                           tickfont=dict(size=15),  # Change font size of y-axis tick labels
                           range=[0, None],
                       )
    )
    
    if granularity == "Měsíce":
        bars.update_layout(
                xaxis=dict(
                        tickmode="array",
                        tickvals=list(range(1, 13)),  # Custom tick values
                        ticktext=[str(i) for i in range(1, 13)]  # Ensure labels are correctly formatted
                    )
        )
    else:
        bars.update_layout(
                xaxis=dict(
                        tickmode="array",
                        tickvals=list(range(1, 8)),  # Custom tick values
                        ticktext=["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]  # Ensure labels are correctly formatted
                    )
        )
    return bars

def get_reasons(year, district, reason):
    accidents = accidents_yearly
    if year:
        accidents = accidents[accidents['rok'] == year]
    else:
        accidents = accidents.groupby(["zuj", "reason"], as_index=False)["accident_count"].sum()
    
    if district:
        accidents = accidents[accidents["zuj"] == district]
    else:
        accidents = accidents.groupby(["reason"], as_index=False)["accident_count"].sum()
    
    if reason:
        accidents = accidents[accidents["reason"] == reason.replace("<br>", " ")]
    
    accidents = accidents.nlargest(5, 'accident_count').sort_values(by='accident_count')

    accidents["reason_wrapped"] = accidents["reason"].apply(
        lambda x: "<br>".join(textwrap.wrap(x, 50))
    )
    
    bars = px.bar(
        accidents,
        y="reason_wrapped",
        x="accident_count",
        title="Accident causes: ",
        orientation="h"
    )

    bars.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        geo_bgcolor="#323130",
        plot_bgcolor= "#323130",
        paper_bgcolor= "#323130",
        font_color="white",
        xaxis_title="Počet nehod",
        yaxis_title="Příčina",
        xaxis_title_font={"size": 20},  # Change font size of x-axis label
        yaxis_title_font={"size": 20},   # Change font size of y-axis label
        xaxis=dict(
            tickfont=dict(size=15),  # Change font size of x-axis tick labels
            ticklabelstandoff=10
        ),
        yaxis=dict(
            tickfont=dict(size=15),
            ticklabelstandoff=20
        ),
        title=''
    )
    return bars

#*************CALLBACKS*****************************************
@app.callback(
        Output('slider', 'value'),
        Input('year-button', 'n_clicks'),
        Input('slider', 'value')
)
def year_reset(button, slider):
    ctx = callback_context
    return None if ctx.triggered[0]["prop_id"] == "year-button.n_clicks" else slider
    

@app.callback(
        Output('reasons', 'clickData'),
        Input('reason-button', 'n_clicks'),
        Input('reasons', 'clickData')
)
def reason_reset(button, reason):
    ctx = callback_context
    return None if ctx.triggered[0]["prop_id"] == "reason-button.n_clicks" else reason

@app.callback(
        Output('map', 'clickData'),
        Input('district-button', 'n_clicks'),
        Input('map', 'clickData')
)
def district_reset(button, district):
    ctx = callback_context
    return None if ctx.triggered[0]["prop_id"] == "district-button.n_clicks" else district

#radio/slider/fix->map
@app.callback(
    Output('map', 'figure'),
    Input('reasons', 'clickData'),
    Input('slider', 'value'),
    Input('reason-button', 'n_clicks'),
    Input('year-button', 'n_clicks'),
)
def update_map(reasonData, year, reason_clicks, year_clicks):
    ctx = callback_context

    if ctx.triggered[0]["prop_id"] == "year-button.n_clicks":
        year = None
    
    if ctx.triggered[0]["prop_id"] == "reason-button.n_clicks":
        reason = None

    if reasonData:
        reason = reasonData['points'][0]["y"]
    else:
        reason = None

    fig = get_map(year, reason)
    return fig

@app.callback(
    Output('reasons', 'figure'),
    Input('slider', 'value'),
    Input('map', 'clickData'),
    Input('reasons', 'clickData'),
    Input('reason-button', 'n_clicks'),
    Input('year-button', 'n_clicks'),
    Input('district-button', 'n_clicks'),
)
def update_reasons(year, clickDataMap, clickDataReasons, reason_clicks, year_clicks, district_clicks):
    ctx = callback_context

    if ctx.triggered[0]["prop_id"] == "year-button.n_clicks":
        year = None

    
    if ctx.triggered[0]["prop_id"] == "reason-button.n_clicks":
        reason = None
    if not clickDataReasons:
        reason = None
    else:
        reason = clickDataReasons['points'][0]["y"]

    if ctx.triggered[0]["prop_id"] == "district-button.n_clicks":
        district = None
    if not clickDataMap:
        district = None
    else:
        district = clickDataMap['points'][0]["location"]

    fig = get_reasons(year, district, reason)
    return fig

#map->bars
@app.callback(
    Output('timeline', 'figure'),
    Input('map', 'clickData'),
    Input('slider', 'value'),
    Input('reasons', 'clickData'),
    Input('reason-button', 'n_clicks'),
    Input('year-button', 'n_clicks'),
    Input('district-button', 'n_clicks'),
    Input('granularity', 'value')
)
def update_timeline(clickDataMap, year, clickDataReasons, reason_clicks, year_clicks, district_clicks, granularity):
    ctx = callback_context

    if ctx.triggered[0]["prop_id"] == "year-button.n_clicks":
        year = None

    
    if ctx.triggered[0]["prop_id"] == "reason-button.n_clicks":
        reason = None
    if not clickDataReasons:
        reason = None
    else:
        reason = clickDataReasons['points'][0]["y"]


    if ctx.triggered[0]["prop_id"] == "district-button.n_clicks":
        district = None
    if not clickDataMap:
        district = None
    else:
        district = clickDataMap['points'][0]["location"]
    
    bars = get_district_graph(district, year, reason, granularity)
    return bars

#********RUNNING THE APP*************************************************
if __name__ == '__main__':
    app.run_server(jupyter_mode="external", debug=False)
