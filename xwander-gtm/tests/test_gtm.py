"""
Integration tests for xwander-gtm plugin.

These tests use the live GTM API. Run with:
    pytest tests/test_gtm.py -v
"""

import pytest
from xwander_gtm import (
    GTMClient,
    TagManager,
    VariableManager,
    TriggerManager,
    WorkspaceManager,
    Publisher,
    GTMError,
    AuthenticationError,
    ResourceNotFoundError
)

# Test configuration
TEST_ACCOUNT_ID = "6215694602"
TEST_CONTAINER_ID = "176670340"


@pytest.fixture(scope="module")
def client():
    """Create GTM client fixture"""
    try:
        return GTMClient()
    except AuthenticationError:
        pytest.skip("GTM credentials not configured")


@pytest.fixture(scope="module")
def tag_manager(client):
    """Create TagManager fixture"""
    return TagManager(client)


@pytest.fixture(scope="module")
def variable_manager(client):
    """Create VariableManager fixture"""
    return VariableManager(client)


@pytest.fixture(scope="module")
def trigger_manager(client):
    """Create TriggerManager fixture"""
    return TriggerManager(client)


@pytest.fixture(scope="module")
def workspace_manager(client):
    """Create WorkspaceManager fixture"""
    return WorkspaceManager(client)


@pytest.fixture(scope="module")
def publisher(client):
    """Create Publisher fixture"""
    return Publisher(client)


class TestClient:
    """Test GTM client operations"""

    def test_client_initialization(self, client):
        """Test client initializes successfully"""
        assert client is not None
        assert client.service is not None

    def test_get_workspace_id(self, client):
        """Test workspace ID retrieval"""
        workspace_id = client.get_workspace_id(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert workspace_id is not None
        assert isinstance(workspace_id, str)

    def test_invalid_credentials(self):
        """Test invalid credentials raise AuthenticationError"""
        with pytest.raises(AuthenticationError):
            GTMClient(credentials_path="/nonexistent/path.yaml")


class TestTags:
    """Test tag operations"""

    def test_list_tags(self, tag_manager):
        """Test listing tags"""
        tags = tag_manager.list_tags(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert isinstance(tags, list)
        assert len(tags) > 0

    def test_list_conversion_tags(self, tag_manager):
        """Test listing conversion tags"""
        tags = tag_manager.list_conversion_tags(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert isinstance(tags, list)

        # Verify conversion tags have required fields
        if len(tags) > 0:
            tag = tags[0]
            assert 'tagId' in tag
            assert 'name' in tag
            assert 'type' in tag
            assert tag['type'] == 'awct'
            assert 'ecEnabled' in tag

    def test_get_tag(self, tag_manager):
        """Test getting specific tag"""
        # First get a tag ID
        tags = tag_manager.list_tags(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        if len(tags) == 0:
            pytest.skip("No tags in container")

        tag_id = tags[0]['tagId']
        tag = tag_manager.get_tag(TEST_ACCOUNT_ID, TEST_CONTAINER_ID, tag_id)

        assert tag is not None
        assert tag['tagId'] == tag_id
        assert 'name' in tag
        assert 'type' in tag

    def test_get_nonexistent_tag(self, tag_manager):
        """Test getting nonexistent tag raises error"""
        with pytest.raises(ResourceNotFoundError):
            tag_manager.get_tag(TEST_ACCOUNT_ID, TEST_CONTAINER_ID, "999999")


class TestVariables:
    """Test variable operations"""

    def test_list_variables(self, variable_manager):
        """Test listing variables"""
        variables = variable_manager.list_variables(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert isinstance(variables, list)
        assert len(variables) > 0

        # Verify variable structure
        var = variables[0]
        assert 'variableId' in var
        assert 'name' in var
        assert 'type' in var

    def test_get_variable(self, variable_manager):
        """Test getting specific variable"""
        variables = variable_manager.list_variables(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        if len(variables) == 0:
            pytest.skip("No variables in container")

        var_id = variables[0]['variableId']
        variable = variable_manager.get_variable(TEST_ACCOUNT_ID, TEST_CONTAINER_ID, var_id)

        assert variable is not None
        assert variable['variableId'] == var_id


class TestTriggers:
    """Test trigger operations"""

    def test_list_triggers(self, trigger_manager):
        """Test listing triggers"""
        triggers = trigger_manager.list_triggers(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert isinstance(triggers, list)
        assert len(triggers) > 0

        # Verify trigger structure
        trigger = triggers[0]
        assert 'triggerId' in trigger
        assert 'name' in trigger
        assert 'type' in trigger


class TestWorkspace:
    """Test workspace operations"""

    def test_sync_workspace(self, workspace_manager):
        """Test workspace sync"""
        result = workspace_manager.sync(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert result is not None

    def test_list_versions(self, workspace_manager):
        """Test listing versions"""
        versions = workspace_manager.list_versions(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert isinstance(versions, list)
        assert len(versions) > 0

        # Verify version structure
        version = versions[0]
        assert 'containerVersionId' in version

    def test_get_latest_version(self, workspace_manager):
        """Test getting latest version"""
        version = workspace_manager.get_latest_version(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert version is not None
        assert 'containerVersionId' in version


class TestPublisher:
    """Test publishing operations"""

    def test_get_live_version(self, publisher):
        """Test getting live version"""
        try:
            live_version = publisher.get_live_version(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
            assert live_version is not None
            assert 'containerVersionId' in live_version
        except GTMError:
            # It's OK if no live version exists
            pytest.skip("No live version in container")


class TestErrorHandling:
    """Test error handling"""

    def test_resource_not_found(self, client):
        """Test ResourceNotFoundError"""
        with pytest.raises(ResourceNotFoundError):
            client.get_resource('tags', TEST_ACCOUNT_ID, TEST_CONTAINER_ID, '999999')

    def test_invalid_resource_type(self, client):
        """Test invalid resource type"""
        with pytest.raises(GTMError):
            client.list_resources('invalid_type', TEST_ACCOUNT_ID, TEST_CONTAINER_ID)


class TestIntegration:
    """Integration tests for complete workflows"""

    def test_conversion_tag_workflow(self, tag_manager):
        """Test complete conversion tag workflow"""
        # List conversion tags
        tags = tag_manager.list_conversion_tags(TEST_ACCOUNT_ID, TEST_CONTAINER_ID)
        assert len(tags) > 0

        # Get first tag
        tag_id = tags[0]['tagId']
        tag = tag_manager.get_tag(TEST_ACCOUNT_ID, TEST_CONTAINER_ID, tag_id)
        assert tag is not None

        # Verify it's a conversion tag
        assert tag['type'] == 'awct'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
