Core API Reference
==================

Lab Module
----------

.. automodule:: plf.lab
    :members:
    :undoc-members:
    :show-inheritance:

Experiment Module
-----------------

.. automodule:: plf.experiment
    :members:
    :undoc-members:
    :show-inheritance:

Utils Module
------------

.. automodule:: plf.utils
    :members:
    :undoc-members:
    :show-inheritance:

Example Workflow
----------------

.. code-block:: python

    from plf.lab import Lab
    from plf.experiment import Experiment

    lab = Lab("Physics Lab")
    exp = Experiment("Free Fall")

    lab.add_experiment(exp)
    lab.run()