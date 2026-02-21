Workflow Guide
==============

Before building workflows and pipelines, create (or load) a lab environment.
The lab stores settings, logs, and pipeline records in a consistent structure.

Create a New Lab
----------------

Use ``create_project`` when starting a new project:

.. code-block:: python

    from plf.lab import create_project

    settings = {
        "project_name": "my_experiment",
        "project_dir": "./projects",
        "component_dir": "path/to/component/dir/"
    }

    settings_path = create_project(settings)

This initializes project metadata and tracking databases, including:

- ``logs.db`` for session tracking
- ``ppls.db`` for active pipelines
- ``Archived/ppls.db`` for archived pipelines

Load an Existing Lab
--------------------

Use ``lab_setup`` to continue work in an existing project:

.. code-block:: python

    from plf.lab import lab_setup
    lab_setup(settings_path)

This loads project settings, registers component paths, and creates a log entry
for the current session.

Workflow Example 1: Single Pipeline Run
---------------------------------------

This example shows a standard run sequence: define config, create pipeline,
prepare resources, then execute.

.. code-block:: python

   from plf.experiment import PipeLine

   pipeline_config = {
      "workflow": {
         "loc": "my_workflows.TrainWorkflow",
         "args": {}
      },
      "args": {
         "loader": {
            "loc": "my_components.DataLoader",
            "args": {"path": "./data/train.csv"}
         },
         "trainer": {
            "loc": "my_components.Trainer",
            "args": {"epochs": 20, "lr": 1e-3}
         }
      }
   }

   P = PipeLine()
   P.new(pplid="baseline_v1", args=pipeline_config)
   P.prepare()
   P.run()

Workflow Example 2: Parameter Variations
----------------------------------------

Use one workflow template with different arguments to create comparable runs.

.. code-block:: python

   from plf.experiment import PipeLine

   lrs = [1e-2, 1e-3, 1e-4]
   for lr in lrs:
      pplid = f"lr_{lr}"
      cfg = {
         "workflow": {"loc": "my_workflows.TrainWorkflow", "args": {}},
         "args": {
            "loader": {
               "loc": "my_components.DataLoader",
               "args": {"path": "./data/train.csv"}
            },
            "trainer": {
               "loc": "my_components.Trainer",
               "args": {"epochs": 20, "lr": lr}
            }
         }
      }

      pipeline = PipeLine()
      pipeline.new(pplid=pplid, args=cfg)
      pipeline.prepare()
      pipeline.run()

Recommended Run Order
---------------------

1. Create or load lab (``create_project`` / ``lab_setup``)
2. Define workflow + component configuration
3. Create pipeline (``PipeLine().new(...)``)
4. Prepare runtime resources (``prepare``)
5. Execute (``run``)
6. Review status and metadata (see :doc:`experiment_management`)

