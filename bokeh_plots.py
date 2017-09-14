from bokeh.plotting import figure, ColumnDataSource
from bokeh.models import HoverTool
from datetime import datetime as dt

# Multiple Output in a Notebook Cell
#from IPython.core.interactiveshell import InteractiveShell
#InteractiveShell.ast_node_interactivity = "all"

from bokeh.layouts import gridplot, layout
from bokeh.plotting import figure, show
# from bokeh.plotting import figure, show, output_file
from bokeh.models import Span, Label, ColumnDataSource, HoverTool, Toggle, CustomJS, CheckboxGroup, LabelSet, CategoricalColorMapper

# Utility
def bokeh_time(dtstr):
   return pd.to_datetime(dtstr).value / 1e6


def scatter_with_hover(source, x, y,
                       fig=None, cols=None, name=None, marker='o',
                       fig_width=500, fig_height=500, **kwargs):
    """
    Plots an interactive scatter plot of `x` vs `y` using bokeh, with automatic
    tooltips showing columns from `df`.
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing the data to be plotted
    x : str
        Name of the column to use for the x-axis values
    y : str
        Name of the column to use for the y-axis values
    fig : bokeh.plotting.Figure, optional
        Figure on which to plot (if not given then a new figure will be created)
    cols : list of str
        Columns to show in the hover tooltip (default is to show all)
    name : str
        Bokeh series name to give to the scattered data
    marker : str
        Name of marker to use for scatter plot
    **kwargs
        Any further arguments to be passed to fig.scatter
    Returns
    -------
    bokeh.plotting.Figure
        Figure (the same as given, or the newly created figure)
    Example
    -------
    fig = scatter_with_hover(df, 'A', 'B')
    show(fig)
    fig = scatter_with_hover(df, 'A', 'B', cols=['C', 'D', 'E'], marker='x', color='red')
    show(fig)
    Author
    ------
    Nicola Mularoni
    With thanks to Robin Wilson & Max Albert for original code example
    """

    # If we haven't been given a Figure obj then create it with default
    # size etc.
    if fig is None:
        fig = figure(width=fig_width, height=fig_height, tools=['box_zoom', 'reset'])



    # We need a name so that we can restrict hover tools to just this
    # particular 'series' on the plot. You can specify it (in case it
    # needs to be something specific for other reasons), otherwise
    # we just use 'main'
    if name is None:
        name = 'main'

    #print(source.data)  # '#ffa51d' weak orange
    color_mapper = CategoricalColorMapper(factors=["0 - Off", "1 - On", None], palette=['#ffbe5b', '#672483', '#1d9b8e'])
    # Actually do the scatter plot - the easy bit
    # (other keyword arguments will be passed to this function)
    fig.scatter(x, y, source=source, name=name, marker=marker, size=8,fill_color={'field': 'LAMP_NAME', 'transform': color_mapper}, line_alpha=0,
                **kwargs)

    # Now we create the hover tool, and make sure it is only active with
    # the series we plotted in the previous line
    hover = HoverTool(names=[name])

    if cols is None:
        # Display *all* columns in the tooltips
        hover.tooltips = [(c, '@' + c) for c in source.columns]
    else:
        # Display just the given columns in the tooltips
        hover.tooltips = [(c, '@' + c) for c in cols]

    hover.tooltips.append(('index', '$index'))

    # Finally add/enable the tool
    fig.add_tools(hover)

    return fig