import pytest


@pytest.fixture()
def node(Ansible, Interface, Command, request):
    """
    This fixture represents a single node in the ceph cluster. Using the
    Ansible fixture provided by testinfra it can access all the ansible variables
    provided to it by the specific test scenario being ran.

    You must include this fixture on any tests that operate on specific type of node
    because it contains the logic to manage which tests a node should run.
    """
    vars = Ansible.get_variables()
    node_type = vars["group_names"][0]
    if not request.node.get_marker(node_type) and not request.node.get_marker('all'):
        pytest.skip("Not a valid test for node type")

    if request.node.get_marker("journal_collocation") and not vars.get("journal_collocation"):
        pytest.skip("Skipping because scenario is not using journal collocation")

    osd_ids = []
    if node_type == "osds":
        result = Command.check_output('sudo ls /var/lib/ceph/osd/ | grep -oP "\d+$"')
        osd_ids = result.split("\n")

    # I can assume eth1 because I know all the vagrant
    # boxes we test with use that interface
    address = Interface("eth1").addresses[0]
    subnet = ".".join(vars["public_network"].split(".")[0:-1])
    data = dict(
        address=address,
        subnet=subnet,
        vars=vars,
        osd_ids=osd_ids,
    )
    return data


def pytest_collection_modifyitems(session, config, items):
    for item in items:
        test_path = item.location[0]
        if "mon" in test_path:
            item.add_marker(pytest.mark.mons)
        elif "osd" in test_path:
            item.add_marker(pytest.mark.osds)
        elif "mds" in test_path:
            item.add_marker(pytest.mark.mdss)
        elif "rgw" in test_path:
            item.add_marker(pytest.mark.rgws)
        else:
            item.add_marker(pytest.mark.all)

        if "journal_collocation" in test_path:
            item.add_marker(pytest.mark.journal_collocation)
