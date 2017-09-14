from flask import Flask, render_template, request
from tornado.ioloop import IOLoop
from bokeh.application import Application
from bokeh.application.handlers import FunctionHandler
from bokeh.embed import autoload_server
from bokeh.server.server import Server

# Local imports
import app_vin_history
import app_global_ewt
import app_global_sqdf

# TODO Clean and comment code, split pages into different subfiles

# Setting up bokeh and flask server
flask_app = Flask(__name__)
bokeh_app_vin = Application(FunctionHandler(app_vin_history.modify_doc))
bokeh_app_global_ewt = Application(FunctionHandler(app_global_ewt.modify_doc))
bokeh_app_global_sqdf = Application(FunctionHandler(app_global_sqdf.modify_doc))

# Setting up tornado IOLoop
io_loop = IOLoop.current()

# Starting Flack server
server = Server({'/bkapp_vin': bokeh_app_vin,'/bkapp_global_ewt': bokeh_app_global_ewt,'/bkapp_global_sqdf': bokeh_app_global_sqdf}, io_loop=io_loop, allow_websocket_origin=["localhost:8080"])
server.start()


@flask_app.route('/', methods=['GET'])
def bkapp_page():
    # GC300412
    script = autoload_server(url='http://localhost:5006/bkapp_vin')
    script_list = script.split("\n")
    script_list[2] = script_list[2][:-1]
    args = [("VIN", "GC303533")]
    for key, value in args:
        script_list[2] = script_list[2] + "&{}={}".format(key, value)
    script_list[2] = script_list[2] + '"'
    script = "\n".join(script_list)
    return render_template("index.html", script=script, template="Flask")

@flask_app.route('/VIN', methods=['GET'])
def bkapp_page_vin():
    # GC300412

    # Hacky attachment of the GET args to the bokeh script url
    svin = request.args.get('vin')
    #print(svin)
    if svin==None:
        return render_template("vin_empty.html", template="Flask")
    script = autoload_server(url='http://localhost:5006/bkapp_vin')

    script_list = script.split("\n")
    script_list[2] = script_list[2][:-1]
    args = [("VIN", svin)]
    for key, value in args:
        script_list[2] = script_list[2] + "&{}={}".format(key, value)
    script_list[2] = script_list[2] + '"'
    script = "\n".join(script_list)
    return render_template("vin.html", script=script, template="Flask")

@flask_app.route('/GLOBAL', methods=['GET'])
def bkapp_page_global_search():
    part_number = request.args.get('part_number')
    dtc = request.args.get('dtc')
    if (part_number is None) & (dtc is None):
        return render_template("global.html", template="Flask")
    elif part_number is not None:
        script = autoload_server(url='http://localhost:5006/bkapp_global_ewt')
        html_file = "global_ewt.html"
    else:
        script = autoload_server(url='http://localhost:5006/bkapp_global_sqdf')
        html_file = "global_sqdf.html"

    args = request.args
    script_list = script.split("\n")
    script_list[2] = script_list[2][:-1]
    for key,value in args.items():
        #print(key)
        script_list[2] = script_list[2] + "&{}={}".format(key, value)
    script_list[2] = script_list[2] + '"'
    script = "\n".join(script_list)

    return render_template("global_sqdf.html", script=script, template="Flask")

if __name__ == '__main__':
    from tornado.httpserver import HTTPServer
    from tornado.wsgi import WSGIContainer

    print('Starting Flask app with embedded Bokeh application on http://localhost:8080/')

    # This uses Tornado to server the WSGI app that flask provides. Presumably the IOLoop
    # could also be started in a thread, and Flask could server its own app directly
    http_server = HTTPServer(WSGIContainer(flask_app))
    http_server.listen(8080)

    #from bokeh.util.browser import view
    #io_loop.add_callback(view, "http://localhost:8080/")
    io_loop.start()