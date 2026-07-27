import unittest
from unittest.mock import MagicMock, patch

from utils.artifactory_client import ArtifactoryClient


class TestArtifactoryClient(unittest.TestCase):

    def test_from_env_requires_credentials(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                ArtifactoryClient.from_env()

    def test_from_env_reads_credentials(self):
        with patch.dict(
            'os.environ',
            {
                'ARTIFACTORY_URL': 'https://repox.jfrog.io/repox',
                'ARTIFACTORY_ACCESS_TOKEN': 'token',
            },
            clear=True,
        ):
            client = ArtifactoryClient.from_env()
            self.assertEqual(client.base_url, 'https://repox.jfrog.io/repox')
            self.assertEqual(client.access_token, 'token')

    def test_fetch_build_info_uses_bearer_auth(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {'buildInfo': {'modules': []}}
        session.get.return_value = response

        client = ArtifactoryClient('https://repox.jfrog.io/repox', 'secret-token', session=session)
        build_info = client.fetch_build_info('sonar-enterprise-sqs', 125719)

        self.assertEqual(build_info, {'modules': []})
        session.get.assert_called_once()
        args, kwargs = session.get.call_args
        self.assertEqual(
            args[0],
            'https://repox.jfrog.io/repox/api/build/sonar-enterprise-sqs/125719',
        )
        self.assertEqual(kwargs['headers'], {'Authorization': 'Bearer secret-token'})
        self.assertEqual(kwargs['timeout'], 30)

    def test_fetch_build_info_url_encodes_build_name(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {'buildInfo': {'modules': []}}
        session.get.return_value = response

        client = ArtifactoryClient('https://repox.jfrog.io/repox', 'token', session=session)
        client.fetch_build_info('repo with space', 1)

        args, _kwargs = session.get.call_args
        self.assertIn('repo%20with%20space', args[0])

    def test_fetch_build_info_raises_on_http_error(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 404
        session.get.return_value = response

        client = ArtifactoryClient('https://repox.jfrog.io/repox', 'token', session=session)
        with self.assertRaises(ArtifactoryClient.FetchError) as ctx:
            client.fetch_build_info('missing', 1)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_fetch_build_info_raises_when_build_info_missing(self):
        session = MagicMock()
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {}
        session.get.return_value = response

        client = ArtifactoryClient('https://repox.jfrog.io/repox', 'token', session=session)
        with self.assertRaises(ArtifactoryClient.FetchError):
            client.fetch_build_info('demo', 1)


if __name__ == '__main__':
    unittest.main()
