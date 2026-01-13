"""
GTM version publishing operations.
"""

from typing import Dict
from googleapiclient.errors import HttpError

from .client import GTMClient
from .exceptions import PublishingError, GTMError


class Publisher:
    """Publish GTM container versions"""

    def __init__(self, client: GTMClient):
        """
        Initialize publisher.

        Args:
            client: GTMClient instance
        """
        self.client = client

    def publish(self, account_id: str, container_id: str, version_id: str) -> Dict:
        """
        Publish a GTM version to LIVE.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID
            version_id: Version ID to publish

        Returns:
            Published version metadata

        Raises:
            PublishingError: If publish fails
            GTMError: If API call fails
        """
        version_path = f"accounts/{account_id}/containers/{container_id}/versions/{version_id}"

        try:
            print(f"  Publishing version {version_id}...")
            result = self.client.service.accounts().containers().versions().publish(
                path=version_path
            ).execute()

            print(f"  Version {version_id} published successfully!")
            return result

        except HttpError as e:
            error_msg = str(e)

            if e.resp.status == 400:
                raise PublishingError(
                    f"Cannot publish version {version_id}: Invalid version",
                    details={"version_id": version_id, "error": error_msg}
                )
            elif e.resp.status == 403:
                raise PublishingError(
                    f"No permission to publish container {container_id}",
                    details={"container_id": container_id, "error": error_msg}
                )
            elif e.resp.status == 404:
                raise PublishingError(
                    f"Version {version_id} not found",
                    details={"version_id": version_id, "error": error_msg}
                )
            else:
                raise PublishingError(
                    f"Failed to publish version {version_id}: {error_msg}",
                    details={"version_id": version_id, "error": error_msg}
                )

    def get_live_version(self, account_id: str, container_id: str) -> Dict:
        """
        Get the currently live container version.

        Args:
            account_id: GTM account ID
            container_id: GTM container ID

        Returns:
            Live containerVersion object

        Raises:
            GTMError: If no live version or API call fails
        """
        try:
            parent = f"accounts/{account_id}/containers/{container_id}"
            response = self.client.service.accounts().containers().version_headers().list(
                parent=parent
            ).execute()

            for version_header in response.get('containerVersionHeader', []):
                if version_header.get('deleted') is False:
                    # The first non-deleted version is the live one
                    version_id = version_header['containerVersionId']
                    version_path = f"{parent}/versions/{version_id}"
                    return self.client.service.accounts().containers().versions().get(
                        path=version_path
                    ).execute()

            raise GTMError(
                f"No live version found for container {container_id}",
                details={"account_id": account_id, "container_id": container_id}
            )

        except HttpError as e:
            raise self.client.handle_http_error(e, "get live version")
