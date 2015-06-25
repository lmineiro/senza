import click
from unittest.mock import MagicMock
from senza.components import component_iam_role, component_elastic_load_balancer, get_merged_policies


def test_component_iam_role(monkeypatch):
    configuration = {
        'Name': 'MyRole',
        'MergePoliciesFromIamRoles': ['OtherRole']
    }
    definition = {}
    args = MagicMock()
    args.region = "foo"
    monkeypatch.setattr('senza.components.get_merged_policies', MagicMock(return_value=[{'a': 'b'}]))
    result = component_iam_role(definition, configuration, args, MagicMock(), False)

    assert [{'a': 'b'}] == result['Resources']['MyRole']['Properties']['Policies']


def test_get_merged_policies(monkeypatch):
    iam = MagicMock()
    iam.list_role_policies.return_value = {'list_role_policies_response': {'list_role_policies_result': {'policy_names': ['pol1']}}}
    iam.get_role_policy.return_value = {'get_role_policy_response': {'get_role_policy_result': {'policy_document': '{"foo":"bar"}'}}}
    monkeypatch.setattr('boto.iam.connect_to_region', lambda x: iam)
    assert [{'PolicyDocument': {'foo': 'bar'}, 'PolicyName': 'pol1'}] == get_merged_policies(['RoleA'], 'myregion')


def test_component_load_balancer_healthcheck(monkeypatch):
    configuration = {
        "Name": "test_lb",
        "SecurityGroups": "",
        "HTTPPort": "9999",
        "HealthCheckPath": "/healthcheck"
    }

    definition = {"Resources": {}}

    args = MagicMock()
    args.region = "foo"

    mock_string_result = MagicMock()
    mock_string_result.return_value = "foo"
    monkeypatch.setattr('senza.components.find_ssl_certificate_arn', mock_string_result)
    monkeypatch.setattr('senza.components.resolve_security_groups', mock_string_result)

    result = component_elastic_load_balancer(definition, configuration, args, MagicMock(), False)
    # Defaults to HTTP
    assert "HTTP:9999/healthcheck" == result["Resources"]["test_lb"]["Properties"]["HealthCheck"]["Target"]

    # Supports other AWS protocols
    configuration["HealthCheckProtocol"] = "TCP"
    result = component_elastic_load_balancer(definition, configuration, args, MagicMock(), False)
    assert "TCP:9999/healthcheck" == result["Resources"]["test_lb"]["Properties"]["HealthCheck"]["Target"]

    # Will fail on incorrect protocol
    configuration["HealthCheckProtocol"] = "MYFANCYPROTOCOL"
    try:
        component_elastic_load_balancer(definition, configuration, args, MagicMock(), False)
    except click.UsageError:
        pass
    except:
        assert False, "check for supported protocols failed"
