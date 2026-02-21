Experiment Management
=====================

After running pipelines, use the experiment utilities in ``plf.experiment`` to
inspect, organize, and maintain your lab.

Core Operations
---------------

.. code-block:: python

    from plf.experiment import (
        get_ppls,
        get_ppl_details,
        get_ppl_status,
        filter_ppls,
        archive_ppl,
        delete_ppl,
        transfer_ppl,
    )

- ``get_ppls()``: Returns active pipeline IDs.
- ``get_ppl_details(...)``: Returns configuration-oriented details for selected pipelines.
- ``get_ppl_status(...)``: Returns a DataFrame of runtime/status metadata.
- ``filter_ppls(query)``: Finds pipelines matching configuration conditions.

Typical Monitoring Flow
-----------------------

.. code-block:: python

    # List all active runs
    ppls = get_ppls()
    print(ppls)

    # Inspect statuses
    status_df = get_ppl_status(ppls)
    print(status_df)

    # Narrow down runs by config query
    candidates = filter_ppls("trainer.lr >= 0.001")
    print(candidates)

Lifecycle Actions
-----------------

Archive completed runs to keep active workspace clean:

.. code-block:: python

    archive_ppl(["baseline_v1", "lr_0.001"])

Restore archived runs:

.. code-block:: python

    archive_ppl(["baseline_v1"], reverse=True)

Delete archived runs permanently:

.. code-block:: python

    delete_ppl(["old_experiment_01"])

Transfer runs between main and transfer area:

.. code-block:: python

    # Export run artifacts
    transfer_ppl(["baseline_v1"], transfer_type="export", mode="copy")

    # Import back later
    transfer_ppl(["baseline_v1"], transfer_type="import", mode="copy")

Operational Recommendations
---------------------------

- Archive runs only after they are no longer active.
- Use consistent ``pplid`` naming (for example: ``modelA_lr1e-3_seed42``).
- Run status checks before archive/delete actions.
- Treat ``delete_ppl`` as irreversible cleanup for archived data only.
- Keep transfer operations explicit (``copy`` vs ``move``) to avoid accidental data loss.
