Reproducibility Guidelines
==========================

PyLabFlow already tracks pipeline metadata and session logs. These practices
help you get stable, repeatable outcomes across reruns and machines.

1) Stabilize Your Environment
-----------------------------

- Use an isolated environment per project.
- Pin dependency versions in a ``requirements.txt`` or lock file.
- Store your project settings JSON with the experiment outputs.

Example:

.. code-block:: bash

    pip freeze > requirements.txt

2) Keep Configurations Explicit
-------------------------------

- Put all run-changing parameters inside pipeline config ``args``.
- Avoid hidden defaults in component code when possible.
- Use descriptive, unique ``pplid`` values.

Example naming convention:

.. code-block:: text

    <workflow>_<dataset>_<model>_lr<value>_seed<value>

3) Track Session Context
------------------------

- Start each working session with ``lab_setup(settings_path)``.
- Keep one active lab per process/session to avoid path confusion.
- Use ``get_logs()`` to review when and where sessions were started.

4) Control Sources of Randomness
--------------------------------

Inside your workflow/components, set seeds for all frameworks you use
(for example Python ``random``, NumPy, PyTorch, TensorFlow).

.. code-block:: python

    import random
    import numpy as np

    random.seed(42)
    np.random.seed(42)

5) Prefer Immutable Historical Records
--------------------------------------

- Archive completed runs instead of modifying existing outputs.
- Use new ``pplid`` values for changed configurations.
- Keep raw inputs and generated outputs under project-managed paths.

6) Re-run Protocol
------------------

When reproducing a prior result:

1. Recreate environment from your pinned dependencies.
2. Load the same settings file via ``lab_setup``.
3. Recreate pipeline with the same config arguments.
4. Compare status/details outputs with the original run.

Quick Reproducibility Checklist
-------------------------------

- [ ] Environment is isolated and dependency versions are pinned.
- [ ] Lab settings file is versioned/saved with the project.
- [ ] All experiment parameters are declared in pipeline config.
- [ ] Seeds are set in all stochastic components.
- [ ] Completed runs are archived, not overwritten.
