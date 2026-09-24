from unittest.mock import MagicMock, patch

from flaskbb.user.services import factories


def test_settings_update_handler_uses_db_and_pluggy():
    handler = factories.settings_update_handler()

    assert handler is not None


@patch("flaskbb.user.services.factories.ChangePasswordForm")
def test_change_password_form_factory_uses_current_user(mock_form):
    expected_form = MagicMock()
    mock_form.return_value = expected_form

    result = factories.change_password_form_factory()

    mock_form.assert_called_once_with(user=factories.current_user)
    assert result is expected_form


@patch("flaskbb.user.services.factories.ChangeEmailForm")
def test_change_email_form_factory_uses_current_user(mock_form):
    expected_form = MagicMock()
    mock_form.return_value = expected_form

    result = factories.change_email_form_factory()

    mock_form.assert_called_once_with(user=factories.current_user)
    assert result is expected_form


@patch("flaskbb.user.services.factories.ChangeUserDetailsForm")
def test_change_details_form_factory_uses_current_user(mock_form):
    expected_form = MagicMock()
    mock_form.return_value = expected_form

    result = factories.change_details_form_factory()

    mock_form.assert_called_once_with(obj=factories.current_user)
    assert result is expected_form
