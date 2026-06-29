Skipping Conditional Tests
##########################

Use ``@pytest.mark.builtwith`` to skip tests when the client does not support a
required SSSD feature:

.. code-block:: python

    from authselect_test_framework.roles.client import Client
    from authselect_test_framework.topology import Profile


    @pytest.mark.topology(Profile.Local)
    @pytest.mark.builtwith("files-provider")
    def test_files_provider(client: Client):
        pass

Check features on other roles by passing keyword arguments:

.. code-block:: python

    @pytest.mark.topology(Profile.SSSD)
    @pytest.mark.builtwith(Profile.SSSD, ipa="passkey")
    def test_example(client: Client, ipa: IPA):
        pass

.. seealso::

    ``@pytest.mark.builtwith`` is converted to ``@pytest.mark.require`` from
    pytest-mh. See `runtime requirements
    <https://pytest-mh.readthedocs.io/en/latest/runtime-requirements.html>`_.
