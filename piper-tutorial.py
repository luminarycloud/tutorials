# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
#   kernelspec:
#     display_name: tutorial-june
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Piper Cherokee
# A tutorial for CFD beginners or new-to-Luminary users that walks through setting up an external aerodynamics simulation using the Luminary Cloud Python SDK.
#
# This is a counterpart to the UI tutorial: https://docs.luminarycloud.com/en/articles/10157837-piper-cherokee
#
# ## In this Tutorial
#
# The Piper PA-28 Cherokee is a small single-propeller aircraft intended for flight training and personal use. This tutorial will guide you through an end-to-end workflow for obtaining a solution in Luminary Cloud and viewing its results, all within the SDK.
#
# Follow the steps below to upload a CAD file, generate a computational mesh, and analyze the results. As you complete each step, you will be able to see the results of your work in the Luminary Cloud UI.
#
# <img src="https://storage.googleapis.com/luminarycloud-learning/sample-projects/piper-cherokee/notebook-images/01-piper-cherokee-flow-vectors.png" width=600 />
#

# %% [markdown]
# ### Set your API key in the environment
# The simplest way to use the SDK is to create an API key in the UI and assign it to the environment variable LC_API_KEY before running this notebook.
#
# Alternatively, you can use the python-dotenv python package (see https://pypi.org/project/python-dotenv/) and create a .env file with your API key specified as:
#
# `LC_API_KEY=MY_API_KEY`
#
# Note that if you do not set the API key, you will be asked to authenticate interactively when you make your first SDK request.

# %%
# Uncomment this block to use python-dotenv for loading LC_API_KEY into the environment from a .env file.
# from dotenv import load_dotenv
# load_success=load_dotenv()

# %%
import luminarycloud as lc
import luminarycloud.vis as vis
from luminarycloud.types import Vector3

import threading
import time
from datetime import datetime
from uuid import uuid4

import pandas as pd
import plotly.express as px
from PIL import Image

from IPython.display import display, update_display

# %% [markdown]
# ## Creating a New Project
# We first create a new project to store the geometry, mesh, and simulations we will perform.
# Projects are the logical way of grouping related simulations in Luminary Cloud.

# %%
project = lc.create_project(
    name="Piper Cherokee SDK Tutorial",
    description="This is a demo of the Luminary Cloud SDK with the Piper Cherokee",
)

# %% [markdown]
# Once created, you can view the details of the created project.

# %%
{
    "id": project.id,
    "name": project.name,
    "description": project.description,
    "create_time": project.create_time.isoformat(),
    "update_time": project.update_time.isoformat(),
}

# %% [markdown]
# ## Uploading Geometry (CAD)

# %% [markdown]
# We will now upload the geometry to the project that we would like to simulate. This is a Parasolid CAD file representing the Piper Cherokee.
# Specifying `wait=True` will make the `create_geometry` call block until the geometry is fully loaded and follow-on operations can be performed on it.
#

# %%
cad_file = "./piper-cherokee-tutorial-cad.x_t"
geometry = project.create_geometry(cad_file, name="Piper Cherokee Model", wait=True)

# %% [markdown]
# ## Listing Geometry Entities
# We can also examine the individual components of the geometry by getting its surfaces and volumes.
# Since the CAD file is of the Piper Cherokee, these geometric entities will be surfaces and volumes of the plane.

# %%
plane_surfaces, volumes = geometry.list_entities()

# %% [markdown]
# The CAD file was created with "Tags" for the surfaces and volumes. Tags
# are used to group surfaces and volumes together in a logical way, allowing better reuse of scripts. To learn more about tags, see
# the accompanying documentation: https://docs.luminarycloud.com/en/articles/10084037-geometry-management-with-tags
#
# On this geometry, there exists individual tags grouping the surfaces of the left wing, right wing, horizontal stabilizer, vertical stablizer, and fuselage of the plane.
# There is also a tag for the volume of the plane.

# %%
plane_tags = geometry.list_tags()
for tag in plane_tags:
    print(f"Tag: {tag.name}\nSurfaces: {tag.surfaces}\nVolumes: {tag.volumes}\n\n")


# %% [markdown]
# ## Adding a Farfield
#
# To simulate the geometry, we must first add a Farfield, representing the entire domain of air around the plane we would like to simulate. Here, we use a sphere with a radius of 80 meters.
# When applying a farfield operation, Luminary will automatically create a tag for the farfield surface ("Farfield") and the fluid volume ("Fluid").

# %%
geometry.add_farfield(
    lc.params.geometry.Sphere(
        center=Vector3(x=0.0, y=0.0, z=0.0),
        radius=80.0,
    ),
)

tags = geometry.list_tags()
farfield_tag = [tag for tag in tags if tag.name == "Farfield"][0]
fluid_volume_tag = [tag for tag in tags if tag.name == "Fluid"][0]

# %% [markdown]
# ### Visualizing Imported Geometry
#
# Our geometry is now in the final state needed for simulation.
# To make sure everything looks as expected, we can visualize it using the SDK, making use of the IPython and PIL packages to display the image.
# We do this by creating a Scene object, which controls what will be rendered. We then specify the camera position and view-direction, using it to render the image.

# %%
from luminarycloud.enum import CameraProjection, Representation

scene = vis.Scene(geometry)
# Hide the far field surface to be able to see the plane
scene.tag_visibility(farfield_tag.id, False)
scene.global_display_attrs.representation = Representation.SURFACE_WITH_EDGES

camera = vis.LookAtCamera(
    look_at=[3.5, 0.0, 0.52],
    position=[-9.1, 12.6, 13.1],
    projection=CameraProjection.PERSPECTIVE,
    width=2048,
    height=1024,
)
scene.add_camera(camera)

image_extract = scene.render_images(
    name="piper geometry", description="Piper geometry with the far field hidden."
)
image_extract.wait()

image_buffer, label = image_extract.download_images()[0]
image = Image.open(image_buffer)
display(image)

# %% [markdown]
# ## Loading a Geometry to Setup
#
# This step is needed only if we want to see the model in the UI Setup screen. It will make it so that the geometry will be viewable in the UI's "Setup" tab.
#
# _NOTE: this operation is irreversible and deletes all existing meshes and simulations in the project._

# %%
project.load_geometry_to_setup(geometry)

# %% [markdown]
# ## Generating a Mesh
#
# With the geometry all set, we will now generate a computational mesh to perform the simulation on.
#
# First we'll set up the parameters that are used to generate the mesh. Normally, you'll want to iterate on this process, starting with a coarser mesh and refining it until you are satisfied.
#
# We recommend starting coarser and refining because this will require fewer computational resources in total. In this tutorial, we'll go ahead and generate a single fine mesh, as we already know suitable values.

# %% [markdown]
# ### Defining Mesh Properties
#
# Here we set the meshing parameters that control properties of the mesh.
# These consist of model parameters and boundary layer parameters, which control the mesh size on the surface of the geometry (the plane in this case) and the boundary layer mesh propagating outwards from the surface.


# %%
model_meshing_params = lc.meshing.ModelMeshingParams(
    surfaces=plane_surfaces,
    curvature=4,
    max_size=0.05,
)

boundary_layer_params = lc.meshing.BoundaryLayerParams(
    surfaces=plane_surfaces,
    n_layers=20,
    initial_size=0.00001,
    growth_rate=1.2,
)

# %% [markdown]
# ### Defining the Mesh Sizing Strategy
# Luminary has several mesh sizing strategies, focusing on making meshing a simpler procedure. These strategies are described in the table below.
#
# | Strategy    | Description               | Notes          |
# | :- | :- | :- |
# | lc.meshing.sizing_strategy.Minimal() | Minimal sizing strategy parameters. | If this is used, all other meshing parameters are ignored. |
# | lc.meshing.sizing_strategy.TargetCount(value) | Sizing strategy based on a target number of cells. | To reach a target number of cells, the edge length specifications will be proportionally scaled throughout the mesh. Requested boundary layer profiles will be maintained. |
# | lc.meshing.sizing_strategy.MaxCount(value)   | Sizing strategy based on a maximum number of cells. | If the mesh becomes larger than the max cell count, the mesh will be scaled. Requested boundary layer profiles will be maintained. |

# %% [markdown]
# We will use the target count strategy with a target of 20 million cells for this tutorial.
# For the purposes of this tutorial, this is an adequate amount. In general, this value will change depending on the specific features of the geometry and simulation configuration.
#

# %%
target_count = 20_000_000
sizing_strategy = lc.meshing.sizing_strategy.TargetCount(target_count)

# %% [markdown]
# ### Seting Mesh Parameters
#
# We now create the MeshGenerationParams object which stores all of the information needed to generate the mesh.
# In addition to the geometry and parameters we defined above, we also specify the minimum and maximum mesh cell sizes for the domain.
#

# %%
mesh_params = lc.meshing.MeshGenerationParams(
    geometry_id=geometry.id,
    sizing_strategy=sizing_strategy,
    model_meshing_params=[model_meshing_params],
    boundary_layer_params=[boundary_layer_params],
    min_size=0.005,
    max_size=50,
)

# %% [markdown]
# ### Creating a Mesh
#
# We now start the mesh creation process. This may take several minutes depending on the complexity of the geometry and resolution of the mesh.
# The process is run in a separate thread and we report the status of the mesh creation using a simple polling approach.

# %%
mesh = None


def run_mesh_creation() -> None:
    global mesh
    mesh = project.create_or_get_mesh(mesh_params, name="Piper Cherokee 20M mesh")


thread = threading.Thread(target=run_mesh_creation)
thread.start()

done = False
spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
display(f"Meshng: ⠏", display_id="status_display")
i = 0
while not done:
    meshes = project.list_meshes()
    if len(meshes) > 0 and all(m.status.name == "COMPLETED" for m in meshes):
        update_display(f"Meshing Complete.", display_id="status_display")
        done = True
        break
    i += 1
    update_display(f"Meshing: {spinner[i % len(spinner)]}", display_id="status_display")
    time.sleep(0.5)

# %% [markdown]
# Now that the mesh has been created, we can inspect its properties as we had for the project.

# %%
mesh

# %% [markdown]
# If we have multiple meshes in this project, we can also list all of them.

# %%
meshes = project.list_meshes()
meshes

# %% [markdown]
# ### Analyzing a Surface Mesh
#
# Just as we did for the geometry, we can now visualize the mesh we have created.
# The primary difference here is constructing the Scene object using the created mesh and requesting Representation.SURFACE_WITH_EDGES to be able to view the mesh.
#

# %%
# Check if mesh is None before passing to Scene constructor
scene = vis.Scene(mesh if mesh is not None else geometry)
scene.tag_visibility(farfield_tag.id, False)
scene.global_display_attrs.representation = Representation.SURFACE_WITH_EDGES

camera = vis.LookAtCamera(
    look_at=[3.5, 0.0, 0.52],
    position=[3.5, 0, 12],
    up=[1, 0, 0],
    projection=CameraProjection.PERSPECTIVE,
    width=4096,
    height=4096,
)
scene.add_camera(camera)

image_extract = scene.render_images(name="piper surface mesh", description="Piper surface mesh.")
image_extract.wait()

image_buffer, label = image_extract.download_images()[0]
image = Image.open(image_buffer)
display(image)


# %% [markdown]
# ### Analyzing a Volume Mesh
#
# We can also visualize the mesh in the volume of the domain. Here, we use a PlaneClip to see a cross-section.
#

# %%
# Check if mesh is None before passing to Scene constructor
scene = vis.Scene(mesh if mesh is not None else geometry)
scene.tag_visibility(farfield_tag.id, False)
scene.global_display_attrs.representation = Representation.SURFACE

camera = vis.LookAtCamera(
    look_at=[3.5, 0.0, 0.52],
    position=[3.5, -10.9, 0.5],
    projection=CameraProjection.PERSPECTIVE,
    width=2048,
    height=1024,
)
scene.add_camera(camera)

# Add a clip to visualize the mesh cells.
clip = vis.PlaneClip("x-clip")
clip.plane.normal = [0, 1, 0]
clip.plane.origin = [3.55, 0, 0.52]
clip.display_attrs.representation = Representation.SURFACE_WITH_EDGES
scene.add_filter(clip)

image_extract = scene.render_images(name="piper volume mesh", description="Piper volume mesh.")
image_extract.wait()

image_buffer, label = image_extract.download_images()[0]
image = Image.open(image_buffer)
display(image)

# %% [markdown]
# ## Setting up a Simulation
#
# We will now setup the simulation we want to run on the mesh we just created. This is done by creating individual "Physics" we want to simulate, each with their own set of properties and boundary conditions.
# In this case, we will just have a single physics, Fluid. In a separate tutorial, we will demonstrate how to set up a conjugate heat transfer simulation, which will have both fluid and solid heat transfer physics.
#
# For this case, we will specify that we want to initialize the interior solution using the Farfield boundary condition values, as is typical for external aerodynamics simulations.
#

# %%
from luminarycloud import EntityIdentifier

fluid_flow_physics = lc.params.simulation.Physics()

fluid_flow_physics.physics_identifier = EntityIdentifier(id=str(uuid4()), name="fluid_flow_physics")
fluid_flow_physics.fluid = lc.params.simulation.physics.Fluid()

fluid_flow_physics.fluid.initialization = (
    lc.params.simulation.physics.fluid.initialization.FluidFarfieldValues()
)

# %% [markdown]
# ### Setting Up a Fluid Material
#
# The fluid material is the air surrounding the plane. As such, we will set up a fluid material with the following properties:

# %%

material_model = lc.params.simulation.material.fluid.material_model.IdealGas(
    molecular_weight=28.966,
    specific_heat_cp=1006.4,
)

thermal_conductivity_model = (
    lc.params.simulation.material.fluid.thermal_conductivity_model.PrescribedPrandtlNumber(
        prandtl_number=0.72,
    )
)

viscosity_model = lc.params.simulation.material.fluid.viscosity_model.Sutherland(
    reference_viscosity=1.716e-5,
    reference_temperature=264.37,
    sutherland_constant=110.56,
)

fluid_material = lc.params.simulation.material.MaterialFluid(
    reference_pressure=0,
    material_model=material_model,
    thermal_conductivity_model=thermal_conductivity_model,
    viscosity_model=viscosity_model,
)

air_material = lc.params.simulation.MaterialEntity(
    material_identifier=EntityIdentifier(id=str(uuid4()), name="air_fluid"),
    fluid=fluid_material,
)

# %% [markdown]
# ### Setting Boundary conditions

# %% [markdown]
# #### Defining Wall Boundary Conditions
#
# The wall boundary condition represents a solid, impermeable surface where the flow interacts with a physical object, such as an aircraft fuselage, a car body, or a pipe wall.
# The specific treatment of the boundary depends on whether the flow is no-slip (viscous flow) or slip (inviscid flow).
#
# For this simulation we set a no-slip wall boundary for the surfaces of the plane.
#

# %%
wall_bc = lc.params.simulation.physics.fluid.boundary_conditions.Wall(
    name="Wall",
    surfaces=[tag.id for tag in plane_tags],
    momentum=lc.params.simulation.physics.fluid.boundary_conditions.wall.momentum.NoSlip(),
)

# %% [markdown]
# #### Defining Far Field Boundary Conditions
#
# The farfield boundary defines the atmospheric conditions in which your aircraft is flying. The farfield ensures that disturbances from the aircraft dissipate naturally, preventing artificial reflections.
#
# We set the farfield properties according to a subsonic flow condition for this example.
# We specify direction of the flow using the `direction_specification` parameter and an angle of attack of 2 degrees.
#
# %%
farfield_bc = lc.params.simulation.physics.fluid.boundary_conditions.Farfield(
    name="Farfield",
    surfaces=[farfield_tag.id],
    mach_number=0.216,
    pressure=70100,
    temperature=288.15,
    direction_specification=lc.params.enum.FarFieldFlowDirectionSpecification.FARFIELD_ANGLES,
    angle_alpha=2.0,
    angle_beta=0.0,
)

# %% [markdown]
# ####  Including Boundary Conditions
#
# The far field and wall boundary conditions we defined above are given to the fluid flow physics object to use as its boundary conditions.

# %%
fluid_flow_physics.fluid.boundary_conditions = [farfield_bc, wall_bc]

# %% [markdown]
# ## Creating Simulation Parameters
#
# Up until this point, we have been preparing the individual components of the simulation description, which we refer to as Simulation Parameters (`SimulationParam`).
# By placing these components into a SimulationParam object, and using them for a simulation template in our project, we can reference these settings when performing simulations.
#

# %%
sim_params = lc.SimulationParam()
for volume in fluid_volume_tag.volumes:
    sim_params.assign_material(air_material, volume)
    sim_params.assign_physics(fluid_flow_physics, volume)

simulation_template = project.create_simulation_template(
    name="piper simulation parameters",
    parameters=sim_params,
)

# %% [markdown]
# ### Configuring Outputs

# %% [markdown]
# By default, Luminary records equation residuals and surface-integrated scalar outputs at every iteration on all surfaces, volumes, monitor planes, and monitor points.
# This allows you to extract outputs after running a simulation without requiring you to re-run the simulation.
#
# However, if you’d like to define a stopping condition based on an output, you need to define a specific output first.
# Otherwise, declaring outputs prior to performing the simulation is optional.
#
# Defining outputs can be done as below for lift and drag forces on the plane.
# Note that if you wanted the lift or drag on only a portion of the plane, you could provide that specific tag in the `surfaces` parameter.
#

# %%
from luminarycloud.enum import QuantityType

lift = simulation_template.create_output_definition(
    lc.outputs.ForceOutputDefinition(
        name="Lift",
        quantity=QuantityType.LIFT,
        surfaces=[tag.id for tag in plane_tags],
    )
)

# %%
drag = simulation_template.create_output_definition(
    lc.outputs.ForceOutputDefinition(
        name="Drag",
        quantity=QuantityType.DRAG,
        surfaces=[tag.id for tag in plane_tags],
    )
)

# %% [markdown]
# ### Setting Stopping Conditions

# %% [markdown]
# Stopping Conditions are used to determine when a simulation terminates.
# For this tutorial, we set a stopping condition based on the lift output we just defined.
# Additionally, we'll stop the simulation after a maximum number of iterations, even if the lift-based stopping condition has not been met.

# %%
simulation_template.create_or_update_stopping_condition(
    output_definition_id=lift.id,
    threshold=0.00_01,  # 0.01%
    start_at_iteration=500,
    averaging_iterations=10,
    iterations_to_consider=5,
)
simulation_template.update_general_stopping_conditions(max_iterations=2000)  # type: ignore

# %% [markdown]
# ### Running a Simulation
#
# Now we run the simulation using our created mesh and simulation template.
# `batch_processing` as `True`, will queue the simulation to run as resources become available at Luminary Cloud.
#

# %%
# Check if mesh is None before accessing its id attribute
# We do this incase we have restarted the kernel and the mesh is not yet created.
simulation = project.create_simulation(
    mesh.id if mesh is not None else meshes[0].id,
    name="Piper simulation",
    simulation_template_id=simulation_template.id,
    batch_processing=True,
)
simulation

# %% [markdown]
# Note that the status will be **SIMULATION_STATUS_ACTIVE** (**ACTIVE**) while running. We must wait for the simulation to finish before inspecting its results.
# Again, simple polling on the returned simulation object is used to check its status and wait for completion.
#

# %%
done = False
spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
display(f"Status: {simulation.status.name}⠏", display_id="status_display")
i = 0
while not done:
    sim_status = simulation.refresh().status.name
    if sim_status != "ACTIVE":
        update_display(f"Status: {sim_status}", display_id="status_display")
        done = True
        break
    i += 1
    update_display(f"Status: {sim_status}{spinner[i % len(spinner)]}", display_id="status_display")
    time.sleep(0.5)

# %% [markdown]
# ## Plotting Residuals
#
# With the simulation finished, we would like to view the residuals to make sure the simulation adequately converged.
# To do this, we can download the residuals as a CSV and plot them with the help of the Pandas and Plotly libraries.
# We will plot all residuals on a log scale, as is typical.
# The 'Spalart-Allmaras Variable' from the SA turbulence model is also available for plotting, although here we omit it.

# %%
with simulation.download_global_residuals() as stream:
    # since this is a steady state simulation, we can drop these columns
    residuals_df = pd.read_csv(stream, index_col="Iteration index").drop(
        ["Time step", "Physical time"], axis=1
    )
residuals_df

# %%
fig = px.line(
    residuals_df,
    x=residuals_df.index,
    y=["X-Momentum Residual", "Y-Momentum Residual", "Z-Momentum Residual", "Energy Residual"],
    title="Residuals vs Iteration",
    template="plotly_white",
    log_y=True,
)  # Using log scale for y-axis since these are residuals

fig.update_layout(
    xaxis_title="Iteration",
    yaxis_title="Residual Value",
    width=1000,
    height=600,
    showlegend=True,
    legend_title="Residual Type",
    legend=dict(
        orientation="h",  # horizontal orientation
        yanchor="bottom",
        y=-0.2,  # position below the plot
        xanchor="center",
        x=0.5,  # centered horizontally
    ),
)

# Optional: Update line styles for better visibility
fig.update_traces(mode="lines")

fig.show()

# %% [markdown]
# ## Plotting Residuals
#
# Outputs can also be obtained on the surfaces of the plane, specified below by `target_boundaries`.
# Again, we could inspect these outputs even if they weren't specified previously in the simulation template.
#

# %%
target_boundaries = [tag.id for tag in plane_tags]

# %%
from luminarycloud.enum import CalculationType, QuantityType, ReferenceValuesType
from luminarycloud.reference_values import ReferenceValues

ref_vals = ReferenceValues(
    reference_value_type=ReferenceValuesType.PRESCRIBE_VALUES,
    area_ref=10.0,
    length_ref=10.0,
    p_ref=101325.0,
    t_ref=273.15,
    v_ref=265.05709547039106,
)

# see documentation for more details about optional parameters
with simulation.download_surface_output(
    QuantityType.LIFT,
    target_boundaries,
    reference_values=ref_vals,
    frame_id="body_frame_id",
    calculation_type=CalculationType.AGGREGATE,
) as stream:
    # since this is a steady state simulation, we can drop "Time step" and "Physical time"
    lift_df = pd.read_csv(stream, index_col="Iteration index").drop(
        ["Time step", "Physical time"], axis=1
    )

# %%
lift_df

# %%
fig = px.line(lift_df, y="Lift", title="Lift vs Iteration", template="plotly_white")

fig.update_layout(xaxis_title="Iteration", yaxis_title="Lift", width=800, height=500)

fig.show()

# %%
# see documentation for more details about optional parameters
with simulation.download_surface_output(
    QuantityType.DRAG,
    target_boundaries,
    reference_values=ref_vals,
    frame_id="body_frame_id",
    calculation_type=CalculationType.AGGREGATE,
) as stream:
    # since this is a steady state simulation, we can drop "Time step" and "Physical time"
    drag_df = pd.read_csv(stream, index_col="Iteration index").drop(
        ["Time step", "Physical time"], axis=1
    )

# %%
drag_df

# %%
fig = px.line(drag_df, y="Drag", title="Drag vs Iteration", template="plotly_white")

fig.update_layout(xaxis_title="Iteration", yaxis_title="Drag", width=800, height=500)

fig.show()

# %% [markdown]
# ### Visualizing the Solution
#
# To view quantities on the plane geometry or the surrounding flow field, we can use the Scene object to render images from Luminary Cloud.
# Below, we show how to visualize the velocity field magnitude in the volume surrounding the plane.
#

# %%
from luminarycloud.enum import FieldComponent, VisQuantity

# Pick the last iteration
solution = simulation.list_solutions()[-1]
scene = vis.Scene(solution)
scene.tag_visibility(farfield_tag.id, False)
scene.global_display_attrs.representation = Representation.SURFACE
scene.global_display_attrs.field.quantity = VisQuantity.NONE

camera = vis.LookAtCamera(
    look_at=[4.0, 0.0, 0.0],
    position=[-4.0, -7.0, 7.0],
    projection=CameraProjection.PERSPECTIVE,
    width=2048,
    height=1024,
)
scene.add_camera(camera)

# Add a slice to visualize the volume solution.
slice = vis.Slice("x-slice")
slice.plane.normal = [0, 1, 0]
slice.plane.origin = [3.55, 0, 0.52]
slice.display_attrs.representation = Representation.SURFACE
slice.display_attrs.field.quantity = VisQuantity.VELOCITY
slice.display_attrs.field.component = FieldComponent.MAGNITUDE
scene.add_filter(slice)

image_extract = scene.render_images(
    name="piper volume solution", description="Piper volume solution visualization."
)
image_extract.wait()

image_buffer, label = image_extract.download_images()[0]
image = Image.open(image_buffer)
display(image)


# %% [markdown]
# We can also visualize other representations of the solution, such as the velocity vectors in the volume surrounding the plane.
#

# %%
scene = vis.Scene(solution)
scene.tag_visibility(farfield_tag.id, False)
scene.global_display_attrs.representation = Representation.SURFACE
scene.global_display_attrs.field.quantity = VisQuantity.NONE

camera = vis.LookAtCamera(
    look_at=[4.0, 0.0, 0.0],
    position=[-4.0, -7.0, 7.0],
    projection=CameraProjection.PERSPECTIVE,
    width=2048,
    height=1024,
)
scene.add_camera(camera)

# Add a slice to visualize the volume solution.
glyph = vis.FixedSizeVectorGlyphs("glyphs")
glyph.field.quantity = VisQuantity.VELOCITY
glyph.sampling_rate = 1000
glyph.size = 0.2
glyph.display_attrs.representation = Representation.SURFACE
glyph.display_attrs.field.quantity = VisQuantity.VELOCITY
glyph.display_attrs.field.component = FieldComponent.MAGNITUDE
scene.add_filter(glyph)

image_extract = scene.render_images(
    name="piper volume solution", description="Piper volume solution visualization."
)
image_extract.wait()

image_buffer, label = image_extract.download_images()[0]
image = Image.open(image_buffer)
display(image)
