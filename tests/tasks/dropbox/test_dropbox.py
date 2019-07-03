from unittest.mock import MagicMock

import pytest

import prefect
from prefect.tasks.dropbox import DropboxDownload
from prefect.utilities.configuration import set_temporary_config


class TestInitialization:
    def test_initializes_with_path_and_sets_defaults(self):
        task = DropboxDownload(path="")
        assert task.path == ""
        assert task.access_token_secret == "DROPBOX_ACCESS_TOKEN"

    def test_additional_kwargs_passed_upstream(self):
        task = DropboxDownload(path="", name="test-task", checkpoint=True, tags=["bob"])
        assert task.name == "test-task"
        assert task.checkpoint is True
        assert task.tags == {"bob"}

    def test_path_is_required(self):
        with pytest.raises(TypeError) as exc:
            DropboxDownload()

        assert "path" in str(exc.value)

    @pytest.mark.parametrize("attr", ["access_token_secret"])
    def test_download_initializes_attr_from_kwargs(self, attr):
        task = DropboxDownload(path="path", **{attr: "my-value"})
        assert task.path == "path"
        assert getattr(task, attr) == "my-value"


class TestCredentials:
    def test_creds_are_pulled_from_secret_at_runtime(self, monkeypatch):
        task = DropboxDownload(path="test")

        dbx = MagicMock()
        monkeypatch.setattr("prefect.tasks.dropbox.dropbox.dropbox.Dropbox", dbx)

        with set_temporary_config({"cloud.use_local_secrets": True}):
            with prefect.context(secrets=dict(DROPBOX_ACCESS_TOKEN="HI")):
                task.run()

        assert dbx.call_args[0][0] == "HI"

    def test_creds_are_pulled_from_secret_at_runtime(self, monkeypatch):
        task = DropboxDownload(path="test")

        dbx = MagicMock()
        monkeypatch.setattr("prefect.tasks.dropbox.dropbox.dropbox.Dropbox", dbx)

        with set_temporary_config({"cloud.use_local_secrets": True}):
            with prefect.context(
                secrets=dict(DROPBOX_ACCESS_TOKEN="HI", TEST_SECRET="BYE")
            ):
                task.run()
                task.run(access_token_secret="TEST_SECRET")

        first_call, second_call = dbx.call_args_list
        assert first_call[0][0] == "HI"
        assert second_call[0][0] == "BYE"
