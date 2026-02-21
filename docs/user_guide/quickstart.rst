Quick Start
===========

This page walks you through a minimal, reliable setup for PyLabFlow.

Prerequisites
-------------

- Python 3.9+
- ``pip`` (or ``conda``)
- A local folder for your project and custom components

1. Create an isolated Python environment
---------------------------------------

   .. code-block:: bash

      conda create -n plf_env python=3.10
      conda activate plf_env

   You can also use ``venv``:

   .. code-block:: bash

      python -m venv .venv
      .venv\Scripts\activate

2. Install PyLabFlow
--------------------

   .. code-block:: bash

      pip install PyLabFlow jupyter

   For development from source:

   .. code-block:: bash

      git clone https://github.com/ExperQuick/PyLabFlow.git
      cd PyLabFlow
      pip install -e .

3. Verify installation
----------------------

   .. code-block:: bash

      python -c "import plf; print('PyLabFlow import OK')"

4. Create your first lab project
--------------------------------

   .. code-block:: python

      from plf.lab import create_project, lab_setup

      settings = {
          "project_name": "my_first_lab",
          "project_dir": "./projects",
          "component_dir": "./components"
      }

      settings_path = create_project(settings)
      lab_setup(settings_path)

   This creates your project folder, initializes tracking databases, and
   registers your component directory for the current session.

5. (Optional) Launch Jupyter
----------------------------

   .. code-block:: bash

      jupyter notebook

6. Use the official example setup
---------------------------------

   If you prefer a ready-made example, download the ``Basic`` setup:

   1. Open:

   .. code-block:: text

      https://download-directory.github.io/

   2. Paste:

   .. code-block:: text

      https://github.com/ExperQuick/PLF_DL_SetUps/tree/main/Basic

   3. Extract the downloaded folder.
   4. Run files in this order:

   - `setup.py`
   - `experiment.ipynb`
   - `Monitor.ipynb`

Next steps
----------

- Continue with :doc:`workflow` to build and run pipelines.
- See :doc:`experiment_management` to query, filter, archive, and transfer experiments.
- Follow :doc:`reproducibility` for repeatable experiment practices.
