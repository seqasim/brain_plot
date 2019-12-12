from flask import Flask, render_template, request
from nilearn import plotting, datasets
from nilearn.plotting.js_plotting_utils import mesh_to_plotly
import json
from string import Template
import os
import joblib
import glob


class BrainNetwork(Flask):
    """
    Let's load data and set some parameters here
    """

    def __init__(self, *args, **kwargs):
        super(BrainNetwork, self).__init__(*args, **kwargs)

        # Set some connectome viz parameters:
        self.linewidth = None
        self.colorbar = None
        self.colorbar_height = None
        self.colorbar_fontsize = None
        self.node_size = 30

        # Set some threshold
        # self.edge_threshold - "99%"


app = BrainNetwork(__name__)


###### DEFINE HELPER FUNCTIONS HERE:

# Based on user selections, get/filter an adjacency matrix
def get_adjacency(patient, frequency):
    """
    Basically, each patient should have a datafile. Within that datafile should be each kind of adjacency matrix:
     various brain frequencies, as well as node coords and region labels

    Then in the code I can filter by region.
    :return:
    """

    data_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'data', '{}_data.p'.format(patient))
    data = joblib.load(data_path)

    adjacency_matrix = data['adjacency_matrix_{}'.format(frequency)]

    node_coords = data['node_coords']

    return adjacency_matrix, node_coords


def get_html_template(template_name):
    """Get an HTML file from package data"""

    # Todo: ensure that os.path is pointing to the right place

    template_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'templates', template_name)
    with open(template_path, 'rb') as f:
        return Template(f.read().decode('utf-8'))


# @app.route('/', methods=['GET'])
# def dropdown():
#    colours = ['Red', 'Blue', 'Black', 'Orange']
#    return render_template('dropdown.html', colours=colours)


@app.route('/')
def main():
    """
    This function enables the user to filter the brain plotting by patient and frequency band
    :return:
    """
    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    patients = []
    for file in glob.glob('{}/*_data.p'.format(data_path)):
        file = file.split('/')[-1]
        patient = file[:-7]
        patients.append(patient)

    frequencys = ['1-5Hz', '5-10Hz']

    #TODO: What other filters or features might be nice to add?

    return render_template('dropdown.html',
                           patients=patients,
                           frequencys=frequencys)

@app.route("/result", methods=['GET', 'POST'])
def brain_plot():
    '''
    Make an HTML brain plot:
    Which nodes show the greatest change in PR Centrality for remembered vs. non-remembered items
    Plot the edges in the graph that CHANGE the most for this contrast, thereby contributing to change in centrality
    :return:
    '''

    patient = str(request.form.get('patient'))
    frequency = str(request.form.get('frequency'))

    adjacency_matrix, node_coords = get_adjacency(patient=patient,
                                                  frequency=frequency)

    connectome_info = plotting.html_connectome._get_connectome(
        adjacency_matrix, node_coords,
        threshold="99%", symmetric_cmap=False)

    # Todo: Figure out how to input all these params in the most sensible way

    connectome_info['line_width'] = app.linewidth
    connectome_info['colorbar'] = app.colorbar
    # connectome_info['cbar_height'] = app.colorbar_height
    # connectome_info['cbar_fontsize'] = app.colorbar_fontsize
    connectome_info['title'] = patient  # title
    # connectome_info['title_fontsize'] = None #title_fontsize

    # make connectome (plotly)
    plot_info = {"connectome": connectome_info}
    mesh = datasets.fetch_surf_fsaverage()
    for hemi in ['pial_left', 'pial_right']:
        plot_info[hemi] = mesh_to_plotly(mesh[hemi])

    # dump the plot to JSON
    graphJSON = json.dumps(plot_info)

    # Get the js libs
    js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'js')
    with open(os.path.join(js_dir, 'surface-plot-utils.js')) as f:
        js_utils = f.read()

    # if I want to embed the js libraries:
    #    with open(os.path.join(js_dir, 'jquery.min.js')) as f:
    #        jquery = f.read()
    #    with open(os.path.join(js_dir, 'plotly-gl3d-latest.min.js')) as f:
    #        plotly = f.read()

    js_lib = """
        <script>
        {}
        </script>
        """.format(js_utils)

    html = get_html_template(
        'connectome_plot_template.html').safe_substitute(
        {'INSERT_CONNECTOME_JSON_HERE': graphJSON,
         'INSERT_JS_LIBRARIES_HERE': js_lib})

    # save out the html document to the html folder
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates',
                           '{}_connectome_plot.html'.format(patient)), "w") as file:
        file.write(html)

    return render_template('{}_connectome_plot.html'.format(patient))

if __name__ == "__main__":
    app.run(debug=True)
