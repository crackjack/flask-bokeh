import math
import yaml
import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
from dateutil.parser import parse
from bokeh.models import Span, LabelSet, CategoricalColorMapper, TapTool, GMapPlot, GMapOptions, DataRange1d, PanTool, WheelZoomTool, ColumnDataSource
from bokeh.layouts import column, layout
from bokeh.plotting import figure
from bokeh.themes import Theme
from bokeh.models.glyphs import Circle
from bokeh.models.widgets import RadioButtonGroup, Div, DataTable,DateFormatter, TableColumn, NumberFormatter
from bokeh.models.ranges import FactorRange
# from bokeh.models.widgets.inputs import Slider
# Local imports
import load_data
import bokeh_plots

# disable pandas chained warning
pd.options.mode.chained_assignment = None
pd.set_option('display.max_colwidth', -1)
pd.options.display.max_columns = 999

def columnsToDate(df, column_dic, date_format):
    for column in column_dic:
        df[column] = pd.to_datetime(df[column], format=date_format, errors='coerce')




# Utility function
def bokeh_time(dtstr):
    return pd.to_datetime(dtstr).value / 1e6

def modify_doc(doc):
    dtc = doc.session_context.request.arguments['dtc'][0].decode('utf-8')
    time_start = doc.session_context.request.arguments['time_start'][0].decode('utf-8')
    time_end = doc.session_context.request.arguments['time_end'][0].decode('utf-8')
    model = doc.session_context.request.arguments['model'][0].decode('utf-8')
    #print(time_start)
    if dtc is '':
        #print("hello")
        time_start = parse(time_start)
        time_end = parse(time_end)
        data_sqdf = load_data.load_sqdf_dtc_all(start=time_start, end=time_end)
    elif (time_start is not '') and (time_end is not ''):
        time_start = parse(time_start)
        time_end = parse(time_end)
        data_sqdf = load_data.load_sqdf_dtc(dtc,time_start ,time_end)
    elif time_start is not '':
        time_start = parse(time_start)
        data_sqdf = load_data.load_sqdf_dtc(dtc, start=time_start)
    elif time_end is not '':
        time_end = parse(time_end)
        data_sqdf = load_data.load_sqdf_dtc(dtc, end=time_end)
    else:
        data_sqdf = load_data.load_sqdf_dtc(dtc)
    #ewt_column_dates = ["REPAIR-DT"]
    sqdf_column_dates_type2 = ["EVENT_OCCURRED"]

    #date_format_type1 = "%Y-%m-%d"
    date_format_type2 = "%Y-%m-%d %H:%M:%S"
    columnsToDate(data_sqdf, sqdf_column_dates_type2, date_format_type2)

    #print(data_sqdf)

    density_time_val = data_sqdf["EVENT_OCCURRED"].dropna().values.astype(np.int64)
    density_time = gaussian_kde(density_time_val,bw_method='silverman')
    density_time_interval = np.arange(density_time_val.min(), density_time_val.max(),
                                 (density_time_val.max() - density_time_val.min()) / 200)
    density_plot_data = density_time(density_time_interval)
    density_interval = pd.to_datetime(density_time_interval, format=date_format_type2, errors='coerce')
    #print(density_interval)

    plot_dtc_density = figure(plot_width=400, plot_height=400,x_axis_type = "datetime",title="Error codes with respect to time")

    #############3 Error codes with respect to mileage
    density_mile_val = data_sqdf["ODO_MILES"].dropna()
    density_mile = gaussian_kde(density_mile_val,bw_method=0.01)
    cutoff = 60000
    density_mile_interval = np.arange(density_mile_val.min(), cutoff,
                                 (cutoff - density_mile_val.min()) / 200)
    density_mile_plot_data = density_mile(density_mile_interval)
    plot_mile_density = figure(plot_width=400, plot_height=400,
                              title="Error codes with respect to mileage")



    # add a line renderer
    plot_dtc_density.line(density_interval, density_plot_data, color='#ff9900')
    plot_mile_density.line(density_mile_interval, density_mile_plot_data, color='#ff9900')



    def style_my_plots(fig):
        fig.background_fill_color = "white"  # "#f8f8f8"
        fig.background_fill_alpha = 0
        fig.xgrid.grid_line_color = None
        fig.ygrid.grid_line_color = None
        fig.xaxis.major_label_orientation = math.pi / 2
        fig.xaxis.major_label_text_color = '#7f7f7f'
        fig.yaxis.major_label_text_color = '#7f7f7f'
        fig.xaxis.minor_tick_line_color = '#7f7f7f'
        fig.yaxis.minor_tick_line_color = '#7f7f7f'
        fig.xaxis.major_tick_line_color = '#7f7f7f'
        fig.yaxis.major_tick_line_color = '#7f7f7f'
        fig.xaxis.axis_line_color = '#7f7f7f'
        fig.yaxis.axis_line_color = '#7f7f7f'
        fig.title.text_color = '#ff9900'
        fig.title.text_font_size = '14pt'
        fig.width=700

    style_my_plots(plot_dtc_density)
    plot_dtc_density.yaxis.major_label_text_font_size = '0pt'
    plot_dtc_density.yaxis.major_tick_line_color = None
    plot_dtc_density.yaxis.minor_tick_line_color = None
    style_my_plots(plot_mile_density)
    plot_mile_density.yaxis.major_label_text_font_size = '0pt'
    plot_mile_density.yaxis.major_tick_line_color = None
    plot_mile_density.yaxis.minor_tick_line_color = None

    doc.add_root(layout([
    [plot_dtc_density,plot_mile_density]
    ]))

    doc.theme = Theme(json=yaml.load("""
        attrs:
            Figure:
                background_fill_color: "#DDDDDD"
                outline_line_color: white
                toolbar_location: above
                height: 500
                width: 800
            Grid:
                grid_line_dash: [6, 4]
                grid_line_color: white
    """))