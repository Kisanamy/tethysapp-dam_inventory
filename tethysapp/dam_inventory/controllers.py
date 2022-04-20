from tkinter.tix import Tree
from tethys_sdk.permissions import login_required,permission_required,has_permission
from tethys_sdk.gizmos import *
from django.shortcuts import reverse, redirect, render
from django.contrib import messages
from tethys_sdk.workspaces import app_workspace, user_workspace
from .model import Dam
from .app import DamInventory as app
from .model import *
from .helpers import create_hydrograph
from django.utils.html import format_html
import os

WORKSPACE = 'geoserver_app'
GEOSERVER_URI = 'http://localhost:8000/apps/geoserver-app'
selected_layer = ''
selected_workspace = ''
options = []
workspaces = []
@app_workspace
@login_required()
def home(request, app_workspace):
    """
    Controller for the app home page.
    """
    geoserver_engine = app.get_spatial_dataset_service(name='main_geoserver', as_engine=True)

    options = []
    response = geoserver_engine.list_layers(with_properties=False)
    responseWorkspaces = geoserver_engine.list_workspaces()

    if response['success']:
        for layer in response['result']:
            options.append((layer.title(), layer))
    
    if responseWorkspaces['success']:
        for workspace in responseWorkspaces['result']:
            workspaces.append(workspace)

    select_options = SelectInput(
        display_text='Choose Layer',
        name='layer',
        multiple=False,
        options=options
    )

    select_workspaces = SelectInput(
        display_text='Choose Workspace',
        name='workspace',
        multiple=False,
        options=workspaces
    )

    if request.POST and 'select_workspace' in request.POST:
        selected_layer = request.POST['layer']
        legend_title = selected_layer.title()

        # geoserver_layer = MVLayer(
        #     source='ImageWMS',
        #     options={
        #         'url': 'http://localhost:8080/geoserver/wms',
        #         'params': {'LAYERS': selected_layer},
        #         'serverType': 'geoserver'
        #     },
        #     legend_title=legend_title,
        #     legend_extent=[-114, 36.5, -109, 42.5],
        #     legend_classes=[
        #         MVLegendClass('polygon', 'County', fill='#999999'),
        # ])

        # map_layers.append(geoserver_layer)

    map_layers = []

    selected_layer = options[0][1]
    selected_workspace = workspaces[0][1]


    # Define base map options
    esri_layer_names = [
        'NatGeo_World_Map',
        'Ocean_Basemap',
        'USA_Topo_Maps',
        'World_Imagery',
        'World_Physical_Map',
        'World_Shaded_Relief',
        'World_Street_Map',
        'World_Terrain_Base',
        'World_Topo_Map',
    ]
    esri_layers = [{'ESRI': {'layer': l}} for l in esri_layer_names]
    
    basemaps = [
        'Stamen',
        {'Stamen': {'layer': 'toner', 'control_label': 'Black and White'}},
        {'Stamen': {'layer': 'watercolor'}},
        'OpenStreetMap',
        'CartoDB',
        {'CartoDB': {'style': 'dark'}},
        {'CartoDB': {'style': 'light', 'labels': False, 'control_label': 'CartoDB-light-no-labels'}},
        {'XYZ': {'url': 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png', 'control_label': 'Wikimedia'}},
        'ESRI'
    ]

    basemaps.extend(esri_layers)
    
    dam_inventory_map = MapView(
        height='100%',
        width='100%',
        layers=map_layers,
        # layers=[dams_layer],
        # basemap=basemaps,
        # view=view_options,
        controls=[
            'ZoomSlider',
            'Rotate',
            'FullScreen',
            {'ZoomToExtent': {'projection': 'EPSG:4326', 'extent': [-100, 25, -65, 55]}}
        ],
        legend=False,
    )

    prev_layer_button = Button(
        name='prev_layer_button',
        icon='glyphicon glyphicon-chevron-left',
        attributes={
            'onclick':'prevLayer()',
        },
    )

    next_layer_button = Button(
        name='next_layer_button',
        icon='glyphicon glyphicon-chevron-right',
        attributes={
            'onclick':'nextLayer()',
        }
    )

    auto_layer_button = Button(
        name='auto_layer_button',
        icon='glyphicon glyphicon-play',
        attributes={
            'onclick':'autoLayer()'
        }
    )

    pause_auto_layer_button = Button(
        name = 'pause_auto_layer_button',
        icon = 'glyphicon glyphicon-pause',
        attributes = {
            'onclick':'pauseAutoLayer()',
            'class':'btn btn-default'
        }
    )

    context = {
        'dam_inventory_map': dam_inventory_map,
        'prev_layer_button': prev_layer_button,
        'next_layer_button': next_layer_button,
        'auto_layer_button': auto_layer_button,
        'pause_auto_layer_button': pause_auto_layer_button,
        'options': options,
        'workspaces': workspaces,
        'select_options': select_options,
        'select_workspaces': select_workspaces,
        'selected_layer': selected_layer,
        'selected_workspace': selected_workspace,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    return render(request, 'dam_inventory/home.html', context)

@app_workspace
@login_required()
@permission_required('add_dams')
def add_dam(request,app_workspace):
    """
    Controller for the Add Dam page.
    """

        # Default Values
    name = ''
    owner = 'Reclamation'
    river = ''
    date_built = ''
    location = ''

    # Errors
    name_error = ''
    owner_error = ''
    river_error = ''
    date_error = ''
    location_error = ''

    # Handle form submission
    if request.POST and 'add-button' in request.POST:
        # Get values
        has_errors = False
        name = request.POST.get('name', None)
        owner = request.POST.get('owner', None)
        river = request.POST.get('river', None)
        date_built = request.POST.get('date-built', None)
        location = request.POST.get('geometry', None)

        # Validate
        if not name:
            has_errors = True
            name_error = 'Name is required.'

        if not owner:
            has_errors = True
            owner_error = 'Owner is required.'

        if not river:
            has_errors = True
            river_error = 'River is required.'

        if not date_built:
            has_errors = True
            date_error = 'Date Built is required.'

        if not location:
            has_errors = True
            location_error = 'Location is required.'

        if not has_errors:
                        # Get value of max_dams custom setting
            max_dams = app.get_custom_setting('max_dams')

            # Query database for count of dams
            Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
            session = Session()
            num_dams = session.query(Dam).count()

            # Only add the dam if custom setting doesn't exist or we have not exceed max_dams
            if not max_dams or num_dams < max_dams:
                add_new_dam(location=location, name=name, owner=owner, river=river, date_built=date_built)
            else:
                messages.warning(request, 'Unable to add dam "{0}", because the inventory is full.'.format(name))

            return redirect(reverse('dam_inventory:home'))

        messages.error(request, "Please fix errors.")

    # Define form gizmos
    name_input = TextInput(
        display_text='Name',
        name='name',
        initial=name,
        error=name_error
    )

    owner_input = SelectInput(
        display_text='Owner',
        name='owner',
        multiple=False,
        options=[('Reclamation', 'Reclamation'), ('Army Corp', 'Army Corp'), ('Other', 'Other')],
        initial=owner,
        error=owner_error
    )

    river_input = TextInput(
        display_text='River',
        name='river',
        placeholder='e.g.: Mississippi River',
        initial=river,
        error=river_error
    )

    date_built = DatePicker(
        name='date-built',
        display_text='Date Built',
        autoclose=True,
        format='MM d, yyyy',
        start_view='decade',
        today_button=True,
        initial=date_built,
        error=date_error
    )

    initial_view = MVView(
        projection='EPSG:4326',
        center=[-98.6, 39.8],
        zoom=3.5,
    )

    drawing_options = MVDraw(
        controls=['Modify', 'Delete', 'Move', 'Point'],
        initial='Point',
        output_format='GeoJSON',
        point_color='#FF0000'
    )

    location_input = MapView(
        height='300px',
        width='100%',
        basemap='OpenStreetMap',
        draw=drawing_options,
        view=initial_view
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'form': 'add-dam-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('dam_inventory:home')
    )

    context = {
        'name_input': name_input,
        'owner_input': owner_input,
        'river_input': river_input,
        'date_built_input': date_built,
        'location_input': location_input,
        'location_error': location_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    return render(request, 'dam_inventory/add_dam.html', context)

@app_workspace
@login_required()
def list_dams(request, app_workspace):
    """
    Show all dams in a table view.
    """
    dams = get_all_dams()
    table_rows = []

    for dam in dams:
        hydrograph_id = get_hydrograph(dam.id)
        if hydrograph_id:
            url = reverse('dam_inventory:hydrograph', kwargs={'hydrograph_id': hydrograph_id})
            dam_hydrograph = format_html('<a class="btn btn-primary" href="{}">Hydrograph Plot</a>'.format(url))
        else:
            dam_hydrograph = format_html('<a class="btn btn-primary disabled" title="No hydrograph assigned" '
                                         'style="pointer-events: auto;">Hydrograph Plot</a>')
        delete_button = format_html('<a class="btn btn-danger" href="{}">Delete</a>'.format(
            reverse('dam_inventory:delete_dam', kwargs={'dam_id': dam.id})))

        table_rows.append(
            (
                dam.name, dam.owner,
                dam.river, dam.date_built,
                dam_hydrograph,
                delete_button
            )
        )

    dams_table = DataTableView(
        column_names=('Name', 'Owner', 'River', 'Date Built', 'Hydrograph','Action'),
        rows=table_rows,
        searching=False,
        orderClasses=True,
        lengthMenu=[[10, 25, 50, -1], [10, 25, 50, "All"]],
    )

    context = {
        'dams_table': dams_table,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    return render(request, 'dam_inventory/list_dams.html', context)

@app_workspace
@login_required()
def delete_dam(request, app_workspace, dam_id):
    """
    Delete a dam.
    """
    delete_dam_by_id(dam_id)
    return redirect(reverse('dam_inventory:dams'))

@user_workspace
@login_required()
def assign_hydrograph(request, user_workspace):
    """
    Controller for the Add Hydrograph page.
    """
        # Get dams from database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    all_dams = session.query(Dam).all()

    # Defaults
    dam_select_options = [(dam.name, dam.id) for dam in all_dams]
    selected_dam = None
    hydrograph_file = None

    # Errors
    dam_select_errors = ''
    hydrograph_file_error = ''

    # Case where the form has been submitted
    if request.POST and 'add-button' in request.POST:
        # Get Values
        has_errors = False
        selected_dam = request.POST.get('dam-select', None)

        if not selected_dam:
            has_errors = True
            dam_select_errors = 'Dam is Required.'

        # Get File
        if request.FILES and 'hydrograph-file' in request.FILES:
            # Get a list of the files
            hydrograph_file = request.FILES.getlist('hydrograph-file')

        if not hydrograph_file and len(hydrograph_file) > 0:
            has_errors = True
            hydrograph_file_error = 'Hydrograph File is Required.'

        if not has_errors:
            # Process file here
            hydrograph_file = hydrograph_file[0]
            success = assign_hydrograph_to_dam(selected_dam, hydrograph_file)

            # Remove csv related to dam if exists
            for file in os.listdir(user_workspace.path):
                if file.startswith("{}_".format(selected_dam)):
                    os.remove(os.path.join(user_workspace.path, file))

            # Write csv to user_workspace to test workspace quota functionality
            full_filename = "{}_{}".format(selected_dam, hydrograph_file.name)
            with open(os.path.join(user_workspace.path, full_filename), 'wb+') as destination:
                for chunk in hydrograph_file.chunks():
                    destination.write(chunk)
                destination.close()

            # Provide feedback to user
            if success:
                messages.info(request, 'Successfully assigned hydrograph.')
            else:
                messages.info(request, 'Unable to assign hydrograph. Please try again.')
            return redirect(reverse('dam_inventory:home'))

        messages.error(request, "Please fix errors.")


    dam_select_input = SelectInput(
        display_text='Dam',
        name='dam-select',
        multiple=False,
        options=dam_select_options,
        initial=selected_dam,
        error=dam_select_errors
    )

    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'form': 'add-hydrograph-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('dam_inventory:home')
    )

    context = {
        'dam_select_input': dam_select_input,
        'hydrograph_file_error': hydrograph_file_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    session.close()

    return render(request, 'dam_inventory/assign_hydrograph.html', context)

@login_required()
def hydrograph(request, hydrograph_id):
    """
    Controller for the Hydrograph Page.
    """
    hydrograph_plot = create_hydrograph(hydrograph_id)

    context = {
        'hydrograph_plot': hydrograph_plot,
        'can_add_dams': has_permission(request, 'add_dams')
    }
    return render(request, 'dam_inventory/hydrograph.html', context)

@login_required()
def hydrograph_ajax(request, dam_id):
    """
    Controller for the Hydrograph Page.
    """
    # Get dams from database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    dam = session.query(Dam).get(int(dam_id))

    if dam.hydrograph:
        hydrograph_plot = create_hydrograph(dam.hydrograph.id, height='300px')
    else:
        hydrograph_plot = None

    context = {
        'hydrograph_plot': hydrograph_plot,
    }

    session.close()
    return render(request, 'dam_inventory/hydrograph_ajax.html', context)

@user_workspace
@login_required()
@permission_required('add_dams')
def import_dams(request, user_workspace):
    """
    Controller for the Import Dams page.
    """
    # Get dams from database
    Session = app.get_persistent_store_database('primary_db', as_sessionmaker=True)
    session = Session()
    all_dams = session.query(Dam).all()

    # Defaults
    dam_file = None

    # Errors
    dam_select_errors = ''
    dam_file_error = ''

    # Case where the form has been submitted
    if request.POST and 'add-button' in request.POST:
        # Get Values
        has_errors = False
        # Get File
        if request.FILES and 'dams-file' in request.FILES:
            # Get a list of the files
            dam_file = request.FILES.getlist('dams-file')

        if not dam_file and len(dam_file) > 0:
            has_errors = True
            dam_file_error = 'Dam File is Required.'

        if not has_errors:
            # Process file here
            dam_file = dam_file[0]
            success = import_dams_to_dam(dam_file)

            # Remove csv related to dam if exists
            for file in os.listdir(user_workspace.path):
                if file.startswith("dams_"):
                    os.remove(os.path.join(user_workspace.path, file))

            # Write csv to user_workspace to test workspace quota functionality
            full_filename = "dams_{}".format(dam_file.name)
            with open(os.path.join(user_workspace.path, full_filename), 'wb+') as destination:
                for chunk in dam_file.chunks():
                    destination.write(chunk)
                destination.close()

            # Provide feedback to user
            if success:
                messages.info(request, 'Successfully imported dams.')
            else:
                messages.info(request, 'Unable to import dams. Please try again.')
            return redirect(reverse('dam_inventory:home'))

        messages.error(request, "Please fix errors.")


    add_button = Button(
        display_text='Add',
        name='add-button',
        icon='glyphicon glyphicon-plus',
        style='success',
        attributes={'form': 'import-dams-form'},
        submit=True
    )

    cancel_button = Button(
        display_text='Cancel',
        name='cancel-button',
        href=reverse('dam_inventory:home')
    )

    context = {
        'dams_file_error': dam_file_error,
        'add_button': add_button,
        'cancel_button': cancel_button,
        'can_add_dams': has_permission(request, 'add_dams')
    }

    session.close()

    return render(request, 'dam_inventory/import_dams.html', context)
