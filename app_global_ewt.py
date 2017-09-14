import math
import yaml
import pandas as pd
import numpy as np
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




# Utility function
def bokeh_time(dtstr):
    return pd.to_datetime(dtstr).value / 1e6

def modify_doc(doc):
    part = doc.session_context.request.arguments['part_number'][0]
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